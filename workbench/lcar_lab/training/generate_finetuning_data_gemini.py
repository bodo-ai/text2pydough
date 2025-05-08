import os
import pandas as pd
from dotenv import load_dotenv
import argparse
import json
from pathlib import Path
from sklearn.model_selection import train_test_split
from tqdm import tqdm
import asyncio
import aiohttp
import time
from aiolimiter import AsyncLimiter
from concurrent.futures import ThreadPoolExecutor
from retrieve_pydough import (
    initialize_r2r_client,
    extract_key_terms_from_code,
    create_rag_prompt,
    perform_rag_retrieval
)
from datetime import datetime
from collections import deque
from typing import List
import random

# Load environment variables from .env file
load_dotenv()

# Get the workspace root directory
WORKSPACE_ROOT = Path("/mnt/c/Users/david/bodo")
DATASET = 'kaggledbqa'

# Global resources
_pool = ThreadPoolExecutor()  # Thread pool for CPU-bound work
_session = None  # Will be initialized in async context
rpm_limiter = AsyncLimiter(30, 60)  # Conservative rate limit of 30 requests per minute
_request_times = deque(maxlen=30)  # Track last 30 request times
_request_lock = asyncio.Lock()  # Lock for request tracking

# Configuration
CONFIG = {
    'default_data_path': str(WORKSPACE_ROOT / 'text2pydough' / 'training' / 'training_data' / 'labeled_data' / DATASET / 'training_ready' / 'training_data_with_schema.csv'),
    'output_file': 'sample_training_data.jsonl',
    'default_sample_size': 3,
    'filter_field': 'dataframe_match',
    'filter_value': True,
    'question_field': 'question',
    'code_field': 'generated_pydough',
    'response_field': 'generated_response',
    'schema_field': 'database_schema',
    'system_instruction': "You are an analytics expert and a proficient Pydough generator that creates Python code based on natural language descriptions.",
    'retry_attempts': 3,
    'retry_delay': 5,  # seconds
    'max_batch_size': 5,  # Process 5 tasks at a time
    'batch_delay': 5,  # Seconds to wait between batches (increased from 2)
}

async def init_session():
    """Initialize the aiohttp session."""
    global _session
    if _session is None:
        _session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=45))

async def cleanup():
    """Cleanup global resources."""
    global _session
    if _session is not None:
        await _session.close()
        _session = None
    _pool.shutdown()

async def _extract_key_terms(code):
    """Run CPU-bound key term extraction in thread pool."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_pool, extract_key_terms_from_code, code)

async def _create_rag_prompt(question, code, key_terms):
    """Run CPU-bound prompt creation in thread pool."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_pool, create_rag_prompt, question, code, key_terms)

async def track_request():
    """Track request timing and ensure we don't exceed rate limits."""
    async with _request_lock:
        now = time.time()
        _request_times.append(now)
        
        # If we have 30 requests in the last minute, wait until the oldest one expires
        if len(_request_times) == 30:
            oldest_time = _request_times[0]
            wait_time = 60 - (now - oldest_time)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                _request_times.popleft()

async def perform_rag_retrieval_async(client, prompt, attempt=1):
    """Asynchronous RAG retrieval with exponential backoff."""
    try:
        # Track request timing
        await track_request()
        
        # Run the synchronous R2R client call in a thread pool
        loop = asyncio.get_running_loop()
        rag_response = await loop.run_in_executor(
            _pool,
            client.retrieval.rag,
            prompt,
            {
                "search_mode": "advanced",
                "graph_settings": {"enabled": True},
                "search_strategy": "rag_fusion",
                "use_hybrid_search": True,
                "hybrid_settings": {
                    "full_text_weight": 1.0,
                    "semantic_weight": 5.0,
                    "full_text_limit": 200,
                    "rrf_k": 50
                },
                "limit": 20
            }
        )
        return rag_response.results.generated_answer, rag_response.results.__dict__
    except Exception as e:
        if "rate limit" in str(e).lower() and attempt < CONFIG['retry_attempts']:
            # Exponential backoff with jitter, starting at 5 seconds
            base_delay = 5 * (2 ** (attempt - 1))  # Start at 5 seconds
            delay = min(base_delay + random.uniform(0, 1), 30)
            print(f"Rate limit hit, waiting {delay:.2f} seconds before retry {attempt + 1}")
            await asyncio.sleep(delay)
            return await perform_rag_retrieval_async(client, prompt, attempt + 1)
        raise Exception(f"Error during RAG retrieval: {str(e)}")

async def generate_pydough_context_async(client, question, code):
    """Generate Pydough context and documentation using RAG with rate limiting."""
    async with rpm_limiter:
        for attempt in range(CONFIG['retry_attempts']):
            try:
                start_time = time.time()
                
                # Run CPU-bound work in thread pool
                key_terms = await _extract_key_terms(code)
                prompt = await _create_rag_prompt(question, code, key_terms)
                
                # Perform async RAG retrieval
                generated_answer, _ = await perform_rag_retrieval_async(client, prompt)
                
                end_time = time.time()
                processing_time = end_time - start_time
                print(f"Request completed in {processing_time:.2f} seconds")
                
                return {
                    "key_terms": key_terms,
                    "documentation": generated_answer
                }
            except Exception as e:
                print(f"Error generating context (attempt {attempt + 1}/{CONFIG['retry_attempts']}): {str(e)}")
                if attempt < CONFIG['retry_attempts'] - 1:
                    await asyncio.sleep(CONFIG['retry_delay'])
                else:
                    print(f"Failed to generate context after {CONFIG['retry_attempts']} attempts")
                    return None

async def process_sample_async(row, client, pbar):
    """Process a single sample asynchronously."""
    try:
        # Add schema to the question
        question_with_schema = f"{row[CONFIG['question_field']]}\nDatabase Schema:\n{row[CONFIG['schema_field']]}"
        
        # Generate Pydough context and documentation
        context = await generate_pydough_context_async(client, row[CONFIG['question_field']], row[CONFIG['code_field']])
        
        result = {
            'question_id': row.get('question_id', ''),
            'db_name': row.get('db_name', ''),
            'question': question_with_schema,
            'code': row[CONFIG['code_field']],
            'response': row[CONFIG['response_field']],
            'context': context
        }
        
        pbar.update(1)  # Update progress bar
        return result
    except Exception as e:
        print(f"Error processing sample: {str(e)}")
        pbar.update(1)  # Still update progress bar on error
        return None

async def load_and_preprocess_data_async(csv_path, sample_size=None):
    """Load and preprocess the training data asynchronously."""
    # Initialize session
    await init_session()
    
    # Load the CSV file
    df = pd.read_csv(csv_path)
    
    # Filter for examples where dataframe_match is True
    df = df[df[CONFIG['filter_field']] == CONFIG['filter_value']]
    
    # Initialize R2R client
    client = initialize_r2r_client()
    
    # Create training examples
    examples = []
    total_samples = sample_size if sample_size else CONFIG['default_sample_size']
    
    print(f"Processing {total_samples} samples asynchronously...")
    
    # Track total processing time
    total_start_time = time.time()
    
    # Create progress bar
    with tqdm(total=total_samples, desc="Processing samples") as pbar:
        # Create all tasks upfront
        tasks = []
        for _, row in df.head(total_samples).iterrows():
            task = process_sample_async(row, client, pbar)
            tasks.append(task)
        
        # Process tasks in smaller batches with delays
        batch_size = CONFIG['max_batch_size']
        for i in range(0, len(tasks), batch_size):
            try:
                batch = tasks[i:i + batch_size]
                results = await asyncio.gather(*batch, return_exceptions=True)
                
                # Add successful results to examples
                for result in results:
                    if isinstance(result, dict) and result.get('context') is not None:
                        examples.append(result)
                
                # Print rate limiting stats
                async with _request_lock:
                    current_rate = len([t for t in _request_times if time.time() - t < 60])
                    print(f"\nCurrent request rate: {current_rate} requests per minute")
                
                # Wait between batches
                if i + batch_size < len(tasks):
                    await asyncio.sleep(CONFIG['batch_delay'])
                    
            except asyncio.CancelledError:
                print("\nProcessing interrupted. Saving progress...")
                break
            except Exception as e:
                print(f"\nError processing batch: {str(e)}")
                # Wait longer on error
                await asyncio.sleep(CONFIG['batch_delay'] * 2)
    
    total_end_time = time.time()
    total_processing_time = total_end_time - total_start_time
    avg_request_time = total_processing_time / len(examples) if examples else 0
    
    print(f"\nProcessing Summary:")
    print(f"Total processing time: {total_processing_time:.2f} seconds")
    print(f"Average request time: {avg_request_time:.2f} seconds")
    print(f"Successfully processed {len(examples)} out of {total_samples} samples")
    return examples

def load_and_preprocess_data(csv_path, sample_size=None):
    """Wrapper for async data loading."""
    try:
        return asyncio.run(load_and_preprocess_data_async(csv_path, sample_size))
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Cleaning up...")
        asyncio.run(cleanup())
        raise
    finally:
        asyncio.run(cleanup())

def format_output(code, response, context):
    """Format the output with answer first, then code and context."""
    return f"""Answer:
{response}

Pydough Code:
{code}

Code Context:
{context['documentation']}"""

def convert_to_json_format(examples):
    """Convert examples to JSON format with context."""
    json_data = []
    for example in examples:
        if example['context'] is None:
            print(f"Warning: Skipping example due to missing context")
            continue
            
        # Format the output with code, response, and context
        combined_output = format_output(
            example['code'],
            example['response'],
            example['context']
        )
            
        json_data.append({
            "systemInstruction": {
                "role": "system",
                "parts": [{
                    "text": CONFIG['system_instruction']
                }]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": example['question']}]
                },
                {
                    "role": "model",
                    "parts": [{"text": combined_output}]
                }
            ]
        })
    return json_data

def save_jsonl(data, filepath):
    """Save data to a JSONL file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            for item in data:
                json.dump(item, f, ensure_ascii=False)
                f.write('\n')
    except Exception as e:
        print(f"Error saving JSONL file: {str(e)}")
        raise

def format_markdown(example):
    """Format a single example as markdown."""
    return f"""## Question
{example['question']}

## Answer
{example['response']}

## Pydough Code
```python
{example['code']}
```

## Code Context
{example['context']['documentation']}

---

"""

def save_markdown(examples, filepath):
    """Save examples to a markdown file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# Pydough Training Examples\n\n")
            for example in examples:
                if example['context'] is not None:
                    f.write(format_markdown(example))
    except Exception as e:
        print(f"Error saving markdown file: {str(e)}")
        raise

def save_csv_data(examples, csv_path):
    """Save examples to a CSV file with question, code, context, and metadata."""
    try:
        # Prepare data for CSV
        csv_data = []
        print("Saving CSV data...")
        for example in tqdm(examples, desc="Saving to CSV"):
            if example['context'] is None:
                continue
                
            # Extract question_id and db_name from the original data
            # The question field contains the full question text, so we need to get these from the original data
            question_id = example.get('question_id', '')
            db_name = example.get('db_name', '')
            
            csv_data.append({
                'question_id': question_id,
                'db_name': db_name,
                'question': example['question'],
                'pydough_code': example['code'],
                'context': example['context']['documentation']
            })
        
        # Convert to DataFrame and save
        df = pd.DataFrame(csv_data)
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"Created CSV file with {len(csv_data)} examples at {csv_path}")
    except Exception as e:
        print(f"Error saving CSV file: {str(e)}")
        raise

def prepare_sample_dataset(csv_path, output_file=CONFIG['output_file'], sample_size=None, markdown_output=None, validation_split=0.2):
    """Prepare a sample dataset with context in JSON format."""
    # Load and preprocess data
    examples = load_and_preprocess_data(csv_path, sample_size=sample_size)
    
    # Split into training and validation sets
    train_examples, val_examples = train_test_split(examples, test_size=validation_split, random_state=42)
    
    print(f"Split data into {len(train_examples)} training and {len(val_examples)} validation examples")
    
    # Get the base directory (spider directory)
    base_dir = os.path.dirname(os.path.dirname(csv_path))
    
    # Create timestamp for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create output directories with timestamp
    training_ready_dir = os.path.join(base_dir, 'training_ready', timestamp)
    rag_documentation_dir = os.path.join(base_dir, 'rag_documentation', timestamp)
    os.makedirs(training_ready_dir, exist_ok=True)
    os.makedirs(rag_documentation_dir, exist_ok=True)
    
    # Save training data
    train_json_data = convert_to_json_format(train_examples)
    train_json_path = os.path.join(training_ready_dir, f'train_{output_file}')
    save_jsonl(train_json_data, train_json_path)
    
    # Save validation data
    val_json_data = convert_to_json_format(val_examples)
    val_json_path = os.path.join(training_ready_dir, f'val_{output_file}')
    save_jsonl(val_json_data, val_json_path)
    
    # Save to markdown if requested
    if markdown_output:
        train_markdown_path = os.path.join(training_ready_dir, f'train_{markdown_output}')
        val_markdown_path = os.path.join(training_ready_dir, f'val_{markdown_output}')
        save_markdown(train_examples, train_markdown_path)
        save_markdown(val_examples, val_markdown_path)
        print(f"Created markdown files with {len(train_examples)} training and {len(val_examples)} validation examples")
    
    # Save to CSV in rag_documentation directory
    train_csv_path = os.path.join(rag_documentation_dir, 'train_rag_documentation.csv')
    save_csv_data(train_examples, train_csv_path)
    
    val_csv_path = os.path.join(rag_documentation_dir, 'val_rag_documentation.csv')
    save_csv_data(val_examples, val_csv_path)
    
    print(f"Created training dataset with {len(train_json_data)} examples at {train_json_path}")
    print(f"Created validation dataset with {len(val_json_data)} examples at {val_json_path}")
    
    # Save metadata about this run
    metadata = {
        'timestamp': timestamp,
        'total_samples': len(examples),
        'training_samples': len(train_examples),
        'validation_samples': len(val_examples),
        'validation_split': validation_split,
        'input_file': csv_path,
        'output_files': {
            'training_jsonl': train_json_path,
            'validation_jsonl': val_json_path,
            'training_csv': train_csv_path,
            'validation_csv': val_csv_path
        }
    }
    
    metadata_path = os.path.join(training_ready_dir, 'metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return train_json_path, val_json_path

def main():
    parser = argparse.ArgumentParser(description='Prepare training data with database schema and Pydough context.')
    parser.add_argument('--data-path', type=str, default=CONFIG['default_data_path'],
                      help='Path to the training data CSV file')
    parser.add_argument('--output-file', type=str, default=CONFIG['output_file'],
                      help='Name of the output JSONL file (will be saved in training_ready/timestamp directory)')
    parser.add_argument('--sample-size', type=int, default=CONFIG['default_sample_size'],
                      help='Number of examples to include in the sample (default: 3, use 0 for all examples)')
    parser.add_argument('--markdown-output', type=str,
                      help='Name of the markdown file (will be saved in training_ready/timestamp directory)')
    parser.add_argument('--validation-split', type=float, default=0.2,
                      help='Fraction of data to use for validation (default: 0.2)')
    args = parser.parse_args()

    print("Preparing sample dataset with context...")
    train_file, val_file = prepare_sample_dataset(
        args.data_path, 
        args.output_file,
        args.sample_size if args.sample_size > 0 else None,
        args.markdown_output,
        args.validation_split
    )
    print(f"Dataset preparation complete! Training data: {train_file}, Validation data: {val_file}")

if __name__ == "__main__":
    main() 