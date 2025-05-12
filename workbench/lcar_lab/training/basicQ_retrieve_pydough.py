import os
import pandas as pd
from dotenv import load_dotenv
import argparse
from r2r import R2RClient
from typing import Dict, List, Optional, Tuple
import csv
import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import queue
from tqdm import tqdm
from aiolimiter import AsyncLimiter
import time
from collections import deque
import random

# Load environment variables from root .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

# Global resources
_pool = ThreadPoolExecutor()  # Thread pool for CPU-bound work
rpm_limiter = AsyncLimiter(30, 60)  # Conservative rate limit of 30 requests per minute
_request_times = deque(maxlen=30)  # Track last 30 request times
_request_lock = asyncio.Lock()  # Lock for request tracking

# Configuration
CONFIG = {
    'retry_attempts': 3,
    'retry_delay': 5,  # seconds
    'max_batch_size': 10,  # Process 10 tasks at a time
    'batch_delay': 5,  # Seconds to wait between batches
}

def initialize_r2r_client() -> R2RClient:
    """Initialize the R2R client using the API key from .env."""
    url = "http://localhost:7272"
    return R2RClient(base_url=url)

def extract_key_terms_from_code(code: str) -> List[str]:
    """Extract key Pydough-specific terms and syntax from code."""
    terms = []
    
    # Pydough-specific functions and methods
    pydough_functions = [
        'CALCULATE', 'WHERE', 'ORDER_BY', 'TOP_K', '.PARTITION',
        'HAS', 'HASNOT', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'NDISTINCT',
        'ASC', 'DESC', 'JOIN_STRINGS', 'YEAR', 'MONTH'
    ]
    
    # Extract Pydough function calls
    for func in pydough_functions:
        if func in code:
            terms.append(func)
    
    # Extract collection names (they appear before dots)
    lines = code.split('\n')
    for line in lines:
        # Look for collection access patterns (e.g., "collection.subcollection")
        parts = line.split('.')
        if len(parts) > 1:
            # The first part before the dot is often a collection name
            collection = parts[0].strip()
            if collection and not collection.startswith((' ', '\t', '#')):
                terms.append(collection)
    
    # Extract aggregation patterns
    aggregation_patterns = [
        'SUM(', 'COUNT(', 'AVG(', 'MIN(', 'MAX(', 'NDISTINCT(',
        'HAS(', 'HASNOT('
    ]
    for pattern in aggregation_patterns:
        if pattern in code:
            terms.append(pattern[:-1])  # Remove the '('
    
    # Extract sorting patterns
    if 'ASC(' in code or 'DESC(' in code:
        terms.append('SORTING')
    
    # Extract partitioning patterns
    if 'PARTITION(' in code:
        terms.append('PARTITION')
    
    # Extract calculation patterns
    if '.CALCULATE(' in code:
        terms.append('CALCULATE')
    
    return list(set(terms))  # Remove duplicates

def create_rag_prompt(question: str, answer: str, key_terms: List[str]) -> str:
    """Create a prompt for RAG that focuses on documentation."""
    return f"""
    Please provide documentation and explanation for the following Pydough question and answer:
    
    Original User Question:
    {question}
    
    Pydough Answer:
    {answer}
    
    Based on information on the provided document only, focus on explaining:
    1. The Pydough-specific functions and patterns used in the answer
    2. The data flow and transformations
    3. Any important Pydough best practices demonstrated
    4. How this answer follows Pydough conventions
    5. How the answer addresses the original question
    6. Include key examples from the search when available. 
    7. Include key code blocks, key descriptions and definitions in your response, verbatim from source if possible.
    8. Don't make up any information or code.
    
    Key terms to consider: {', '.join(key_terms)}
    """

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

async def process_single_question(
    client: R2RClient,
    question: str,
    key_terms: List[str],
    output_md: Optional[str] = None,
    md_content: Optional[List[str]] = None,
    idx: Optional[int] = None
) -> Dict:
    """Process a single question asynchronously."""
    try:
        prompt = create_rag_prompt(question, "", key_terms)
        try:
            # Perform async RAG retrieval with rate limiting
            async with rpm_limiter:
                generated_answer, full_results = await perform_rag_retrieval_async(client, prompt)
        except Exception as e:
            print(f"\nR2R API Error for question {idx + 1}: {str(e)}")
            if output_md and md_content is not None:
                md_content.append(f"\nR2R API Error for question {idx + 1}: {str(e)}\n")
            return None
        
        result = {
            'question': question,
            'generated_answer': generated_answer,
            'key_terms': ', '.join(key_terms)
        }
        
        if output_md and md_content is not None and idx is not None:
            md_content.append(f"\n## Example {idx + 1}\n")
            md_content.append("### Question")
            md_content.append(f"```\n{question}\n```\n")
            md_content.append("### Extracted Key Terms")
            md_content.append(", ".join(key_terms) + "\n")
            md_content.append("### Documentation Retrieval Results\n")
            md_content.append("#### Generated Documentation")
            md_content.append(generated_answer)
            md_content.append("\n#### Full RAG Results")
            md_content.append("```json")
            md_content.append(str(full_results))
            md_content.append("```\n")
        
        print(f"Completed question {idx + 1}")
        return result
    except Exception as e:
        print(f"\nError processing question {idx + 1}: {str(e)}")
        if output_md and md_content is not None:
            md_content.append(f"Error during processing: {str(e)}\n")
        return None

async def process_pydough_questions(
    csv_path: str,
    num_examples: int = 3,
    output_md: Optional[str] = None,
    batch_size: int = 10
) -> None:
    """Process the Pydough questions asynchronously in batches."""
    # Initialize R2R client
    client = initialize_r2r_client()
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_dir = os.path.dirname(os.path.abspath(__file__))  
    relative_path = os.path.join(base_dir, "training_data/labeled_data/basicQ/processed")
    output_dir = os.path.join(relative_path, timestamp)
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize list to store results
    results = []
    
    # Load the questions from CSV file
    try:
        # First try to read with pandas
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            # If pandas fails, try reading with csv module
            questions = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 1:  # Ensure we have at least a question
                        questions.append(row[0])
            df = pd.DataFrame({'question': questions})
        
        if 'question' not in df.columns:
            raise ValueError("CSV file must contain 'question' column")
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {str(e)}")
    
    # Create markdown content if output_md is specified
    if output_md:
        md_content = ["# Pydough Question Documentation Retrieval Results\n"]
    else:
        md_content = None
    
    # Process questions in batches
    total_questions = min(num_examples, len(df))
    processed_count = 0
    
    print(f"Starting to process {total_questions} questions in batches of {batch_size}")
    
    # Initialize progress bar
    pbar = tqdm(total=total_questions, desc="Processing questions", unit="question")
    
    while processed_count < total_questions:
        # Calculate the current batch size
        current_batch_size = min(batch_size, total_questions - processed_count)
        
        print(f"\nStarting batch of {current_batch_size} questions")
        
        # Create tasks for the current batch
        tasks = []
        for i in range(current_batch_size):
            idx = processed_count + i
            question = df.iloc[idx]['question']
            key_terms = extract_key_terms_from_code(question)
            task = asyncio.create_task(
                process_single_question(
                    client, question, key_terms, output_md, md_content, idx
                )
            )
            tasks.append(task)
        
        # Wait for all tasks in the current batch to complete
        batch_results = await asyncio.gather(*tasks)
        
        # Filter out None results and add to results list
        valid_results = [r for r in batch_results if r is not None]
        results.extend(valid_results)
        
        # Update progress bar
        pbar.update(len(valid_results))
        
        # Update processed count
        processed_count += current_batch_size
        
        # Wait between batches if there are more to process
        if processed_count < total_questions:
            print(f"Waiting {CONFIG['batch_delay']} seconds before next batch...")
            await asyncio.sleep(CONFIG['batch_delay'])
    
    # Close progress bar
    pbar.close()
    
    # Write markdown content to file if specified
    if output_md and md_content:
        with open(output_md, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_content))
        print(f"Markdown results written to {output_md}")
    
    # Write results to CSV
    results_df = pd.DataFrame(results)
    results_csv_path = os.path.join(output_dir, 'generated_answers.csv')
    results_df.to_csv(results_csv_path, index=False, encoding='utf-8')
    print(f"Generated answers saved to {results_csv_path}")

def main():
    parser = argparse.ArgumentParser(description='Process Pydough questions and perform RAG retrieval')
    parser.add_argument('--csv_path', type=str, required=True, help='Path to the CSV file containing Pydough questions and answers')
    parser.add_argument('--num_examples', type=int, default=3, help='Number of examples to process')
    parser.add_argument('--output_md', type=str, default=None, help='Optional output markdown file path')
    parser.add_argument('--batch_size', type=int, default=10, help='Number of questions to process in parallel')
    
    args = parser.parse_args()
    asyncio.run(process_pydough_questions(args.csv_path, args.num_examples, args.output_md, args.batch_size))

if __name__ == '__main__':
    main() 