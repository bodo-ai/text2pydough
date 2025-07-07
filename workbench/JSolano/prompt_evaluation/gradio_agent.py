from gradio_client import Client
import json
import pandas as pd
import re
import time
from datetime import datetime
import os

# -------------------------------------------------------------------
# ⚙️ Experiment tracking configuration
# -------------------------------------------------------------------
EXPERIMENT_NAME = "Ensemble"
PARENT_RUN_ID = "c4ad9fa8cda949889c8502e69c434d4a"
# -------------------------------------------------------------------

def extract_plain_text(result):
    """Extract plain text from the agent response."""
    if not result or len(result) < 2:
        return ""
    
    assistant_response = result[1].get('content', '')
    return assistant_response

def extract_json(result):
    """Extract pure JSON from the agent response."""
    plain_text = extract_plain_text(result)
    if not plain_text:
        return None

    # Look for JSON content within ```json code blocks
    json_pattern = r'```json\s*(.*?)\s*```'
    match = re.search(json_pattern, plain_text, re.DOTALL)
    
    json_str = ""
    if match:
        json_str = match.group(1).strip()
    else:
        # If no markdown, maybe the whole response is JSON.
        # Let's find the first '{' or '[' and try to parse from there.
        brace_pos = plain_text.find('{')
        bracket_pos = plain_text.find('[')
        
        start_pos = -1
        
        if brace_pos != -1 and bracket_pos != -1:
            start_pos = min(brace_pos, bracket_pos)
        elif brace_pos != -1:
            start_pos = brace_pos
        elif bracket_pos != -1:
            start_pos = bracket_pos
            
        if start_pos != -1:
            json_str = plain_text[start_pos:]

    if not json_str:
        return None

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # The string may have trailing characters, so let's try to parse until we can't anymore
        decoder = json.JSONDecoder()
        try:
            val, idx = decoder.raw_decode(json_str)
            return val
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return None

def extract_dataframe(json_data):
    """Convert extracted JSON to a Pandas DataFrame."""
    if json_data is None:
        return None
    
    try:
        # Handle different JSON structures
        if isinstance(json_data, list):
            df = pd.DataFrame(json_data)
        elif isinstance(json_data, dict):
            df = pd.DataFrame([json_data])
        else:
            print(f"Unsupported JSON structure for DataFrame: {type(json_data)}")
            return None
        
        return df
    except Exception as e:
        print(f"Error converting to DataFrame: {e}")
        return None

def process_question(client, question, dataset_name, db_name, question_id=None):
    """Process a single question and return the results."""
    # Construct the selected_db_display string dynamically
    selected_db_display = f"{dataset_name}: {db_name}/{db_name}.sqlite"
    
    print(f"\n{'='*80}")
    if question_id:
        print(f"Processing Question ID: {question_id}")
    print(f"Question: {question}")
    print(f"Database: {selected_db_display}")
    print(f"{'='*80}")
    
    try:
        result = client.predict(
            message=question,
            history=[],
            architecture_dropdown="Multi-Agent Supervisor",
            model_display="Default",#"GCP: gemini-2.5-flash-preview-05-20",
            include_cheatsheet=False,
            include_schema=False,
            retriever_file="cheatsheet_partition_overhaul.md",
            prompt_file="system_prompt.md",
            temperature=0.1,
            top_p=0.95,
            top_k=40,
            max_steps=25,
            pydough_tool=True,
            sql_list_tables=True,
            sql_schema=True,
            sql_query=False,
            sql_query_checker=False,
            document_kb=True,
            selected_db_display=selected_db_display,
            use_sh_query_gen=False,
            tracking_backend="MLflow",
            experiment_name=EXPERIMENT_NAME,
            parent_run_id=PARENT_RUN_ID,
            api_name="/process_message"
        )
        
        # Extract plain text
        plain_text = extract_plain_text(result)
        print(f"\nPlain text response length: {len(plain_text)} characters")
        
        # Extract JSON
        json_data = extract_json(result)
        if json_data:
            print(f"JSON extracted successfully: {type(json_data)}")
        else:
            print("No JSON data extracted")
        
        # Convert to DataFrame
        df = extract_dataframe(json_data)
        if df is not None:
            print(f"DataFrame shape: {df.shape}")
            print(f"DataFrame columns: {list(df.columns)}")
        
        return {
            'question_id': question_id,
            'question': question,
            'dataset_name': dataset_name,
            'db_name': db_name,
            'selected_db_display': selected_db_display,
            'plain_text': plain_text,
            'json_data': json_data,
            'dataframe': df,
            'success': True
        }
        
    except Exception as e:
        print(f"Error processing question: {e}")
        return {
            'question_id': question_id,
            'question': question,
            'dataset_name': dataset_name,
            'db_name': db_name,
            'selected_db_display': selected_db_display,
            'error': str(e),
            'success': False
        }

def main():
    """Main function to process questions from CSV file."""
    # Configuration
    csv_file_path = "../eval_data/defog/async_results_20250702_215431.csv"#test_execution_2025_06_29-05_18_34_QE.csv"
    server_URL = "http://localhost:2024/"
    
    # Initialize client
    print(f"Connecting to server: {server_URL}")
    client = Client(server_URL)
    
    # Read CSV file
    print(f"Reading questions from: {csv_file_path}")
    try:
        df = pd.read_csv(csv_file_path)
        print(f"Loaded {len(df)} questions from CSV")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return
    
    # Process questions sequentially
    results = []
    start_time = datetime.now()
    
    for index, row in df.iterrows():
        question = row['question']
        question_id = row.get('question_id', index + 1)
        dataset_name = row['dataset_name']
        db_name = row['db_name']
        
        print(f"\nProcessing question {index + 1}/{len(df)}")
        
        # Process the question
        result = process_question(client, question, dataset_name, db_name, question_id)
        results.append(result)
        
        # Add a small delay between requests to avoid overwhelming the server
        time.sleep(1)
    
    # Save final results
    end_time = datetime.now()
    total_time = end_time - start_time
    
    print(f"\n{'='*80}")
    print(f"Processing completed!")
    print(f"Total questions processed: {len(results)}")
    print(f"Total time: {total_time}")
    print(f"Average time per question: {total_time / len(results)}")
    
    # Create results summary
    successful_results = [r for r in results if r['success']]
    failed_results = [r for r in results if not r['success']]
    
    print(f"Successful: {len(successful_results)}")
    print(f"Failed: {len(failed_results)}")
    
    # Save final results with "agents_" prefix in the same directory
    csv_filename = os.path.basename(csv_file_path)
    output_filename = f"agents_{csv_filename}"
    output_file = os.path.join(os.path.dirname(csv_file_path), output_filename)
    
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_file, index=False)
    print(f"Results saved to: {output_file}")

if __name__ == "__main__":
    main()