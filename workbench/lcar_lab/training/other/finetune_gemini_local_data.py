import os
import pandas as pd
from dotenv import load_dotenv
import argparse
import json
from sklearn.model_selection import train_test_split
from retrieve_pydough import (
    initialize_r2r_client,
    extract_key_terms_from_code,
    create_rag_prompt,
    perform_rag_retrieval
)

# Load environment variables from .env file
load_dotenv()

def load_schema(schema_path):
    """Load the database schema from a markdown file."""
    with open(schema_path, 'r', encoding='utf-8') as f:
        return f.read()

def generate_pydough_context(client, question, code):
    """Generate Pydough context and documentation using RAG."""
    try:
        # Extract key terms from the code
        key_terms = extract_key_terms_from_code(code)
        
        # Create RAG prompt
        prompt = create_rag_prompt(question, code, key_terms)
        
        # Perform RAG retrieval
        generated_answer, _ = perform_rag_retrieval(client, prompt)
        
        return {
            "key_terms": key_terms,
            "documentation": generated_answer
        }
    except Exception as e:
        print(f"Error generating context: {str(e)}")
        return None

def load_and_preprocess_data(csv_path, schema_path='/mnt/c/Users/david/bodo/labeling_agent/pydough_data/database/tcph_graph.md'):
    """Load and preprocess the training data."""
    # Load the schema
    schema = load_schema(schema_path)
    
    df = pd.read_csv(csv_path)
    # Filter for valid examples
    df = df[df['valid'] == 'Y']
    
    # Initialize R2R client
    client = initialize_r2r_client()
    
    # Create training examples
    examples = []
    for _, row in df.head(3).iterrows():  # Only process first 3 examples for now
        # Add schema to the question
        question_with_schema = f"{row['question']}\nDatabase Schema:\n{schema}"
        
        # Generate Pydough context and documentation
        context = generate_pydough_context(client, row['question'], row['output'])
        
        examples.append({
            'question': question_with_schema,
            'output': row['output'],
            'context': context
        })
    return examples

def convert_to_json_format(examples):
    """Convert examples to JSON format with context."""
    json_data = []
    for example in examples:
        if example['context'] is None:
            print(f"Warning: Skipping example due to missing context")
            continue
            
        # Combine Pydough code and context in the output
        combined_output = f"""Pydough Code:
{example['output']}

Code Context:
{example['context']['documentation']}"""
            
        json_data.append({
            "systemInstruction": {
                "role": "system",
                "parts": [{
                    "text": "You are a Pydough generator that creates Python code based on natural language descriptions."
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

def save_json(data, filepath):
    """Save data to a JSON file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving JSON file: {str(e)}")
        raise

def prepare_sample_dataset(csv_path, output_file='sample_training_data.json'):
    """Prepare a sample dataset with context in JSON format."""
    # Load and preprocess data
    examples = load_and_preprocess_data(csv_path)
    
    # Convert to JSON format
    json_data = convert_to_json_format(examples)
    
    # Save to file
    save_json(json_data, output_file)
    
    print(f"Created sample dataset with {len(json_data)} examples at {output_file}")
    return output_file

def main():
    parser = argparse.ArgumentParser(description='Prepare training data with database schema and Pydough context.')
    parser.add_argument('--data-path', type=str, default='pydough_corpus.csv',
                      help='Path to the training data CSV file')
    parser.add_argument('--output-file', type=str, default='sample_training_data.json',
                      help='Path to save the sample dataset')
    args = parser.parse_args()

    print("Preparing sample dataset with context...")
    output_file = prepare_sample_dataset(args.data_path, args.output_file)
    print("Dataset preparation complete!")

if __name__ == "__main__":
    main() 