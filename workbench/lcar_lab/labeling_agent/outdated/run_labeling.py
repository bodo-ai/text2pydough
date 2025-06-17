import pandas as pd
import os
from labeling_agent.generator_agent_with_feedback import PydoughGeneratorAgent
from evaluator_agent import SQLEvaluatorAgent, compare_df
import json
from typing import Dict, Any, List
import time
import argparse
from io import StringIO

# max number of rows used by evaluator to provide feedback. 
MAX_ROWS = 100 

def process_questions(
    questions_csv_path: str,
    output_csv_path: str,
    db_path: str,
    metadata_path: str,
    cheatsheet_path: str,
    num_questions: int = None
) -> None:
    """
    Process questions from CSV and store results in output CSV.
    
    Args:
        questions_csv_path: Path to the questions CSV file
        output_csv_path: Path to store the output CSV
        db_path: Path to the SQLite database file
        metadata_path: Path to the metadata graph JSON file
        cheatsheet_path: Path to the cheatsheet markdown file
        num_questions: Number of questions to process (None for all)
    """
    # Initialize agents
    print("Initializing agents...")
    generator_agent = PydoughGeneratorAgent(db_path, metadata_path, cheatsheet_path)
    evaluator_agent = SQLEvaluatorAgent(f"sqlite:///{db_path}")
    
    # Read questions
    print(f"Reading questions from {questions_csv_path}")
    questions_df = pd.read_csv(questions_csv_path)
    
    # Limit number of questions if specified
    if num_questions is not None:
        questions_df = questions_df.iloc[:num_questions]#questions_df.head(num_questions)
        print(f"Processing {num_questions} questions out of {len(questions_df)} total questions")
    
    # Prepare output data
    output_data = []
    
    # Process each question
    for idx, row in questions_df.iterrows():
        question = row['question']
        sql_query = row['sql']  # Get the SQL query from the CSV
        
        print(f"\nProcessing question {idx + 1}: {question}")
        print(f"Ground truth SQL: {sql_query}")
        
        try:
            # Generate Pydough code and execute
            print("Generating and executing Pydough code...")
            generated_code = generator_agent.generate_and_execute(question)
            
            # Get the generated response and DataFrame
            generated_response = generated_code.get('generator_response', '')
            generated_df_json = generated_code.get('dataframe', '{}')
            generated_pydough = generated_code.get('code', '')
            
            
            # Execute the ground truth SQL query
            print("Executing ground truth SQL query...")
            sql_result = evaluator_agent._convert_sql_to_dataframe(sql_query)
            
            
            # Compare the two dataframes
            generated_df = pd.read_json(StringIO(generated_df_json))
            ground_truth_df = pd.read_json(StringIO(sql_result))
            dataframe_comparison_boolean = compare_df(ground_truth_df,generated_df,"order_by",question)
            
            # Sample large DataFrames before sending to evaluator

            if len(generated_df) > MAX_ROWS:
                print(f"Generated DataFrame is large ({len(generated_df)} rows), sampling {MAX_ROWS} rows")
                generated_df_json = generated_df.iloc[:MAX_ROWS].to_json()
            
            if len(ground_truth_df) > MAX_ROWS:
                print(f"Ground truth DataFrame is large ({len(ground_truth_df)} rows), sampling {MAX_ROWS} rows")
                sql_result = ground_truth_df.iloc[:MAX_ROWS].to_json()
                        
            # Evaluate the responses
            print("Evaluating responses...")
            evaluation = evaluator_agent.evaluate_responses(
                question=question,
                ground_truth_sql=sql_query,
                generated_response=generated_response,
                generated_df_json=generated_df_json,
                precomputed_match=dataframe_comparison_boolean
            )
            
            # Store results
            result = {
                'question_id': idx + 1,
                'question': question,
                'ground_truth_sql': sql_query,
                #'ground_truth_result': sql_result,
                #'ground_truth_response': sql_response,
                'generated_response': generated_response,
                'generated_pydough': generated_pydough,
                #'generated_df_json': generated_df_json,
                'evaluation_match': evaluation['match'],
                'evaluation_explanation': evaluation['explanation'],
                'error': None
            }
            
        except Exception as e:
            print(f"Error processing question {idx + 1}: {str(e)}")
            result = {
                'question_id': idx + 1,
                'question': question,
                'ground_truth_sql': sql_query,
                #'ground_truth_result': None,
                #'ground_truth_response': None,
                'generated_response': '',
                'generated_pydough': '',
                #'generated_df_json': '{}',
                'evaluation_match': None,
                'evaluation_explanation': None,
                'error': str(e)
            }
        
        output_data.append(result)
        
        # Save progress after each question
        pd.DataFrame(output_data).to_csv(output_csv_path, index=False)
        print(f"Saved progress to {output_csv_path}")
        
        # Add a small delay to avoid overwhelming the system
        time.sleep(1)

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Process questions using PyDough generator agent.')
    parser.add_argument('--num-questions', type=int, default=None,
                      help='Number of questions to process (default: all)')
    parser.add_argument('--output-dir', type=str, default=None,
                      help='Directory to save output files (default: labeling_agent/results)')
    args = parser.parse_args()
    
    # Database path - handle both Windows and WSL paths
    if os.path.exists("/mnt/c"):
        # WSL environment
        base_path = "/mnt/c/Users/david/bodo"
    else:
        # Windows environment
        base_path = os.path.join("C:", "Users", "david", "bodo")
    
    # Set up paths
    db_path = os.path.join(base_path, "TPCH", "test_data", "tpch.db")
    metadata_path = os.path.join(base_path, "TPCH", "test_data", "tpch_demo_graph.json")
    cheatsheet_path = os.path.join(base_path, "labeling_agent", "pydough_data", "pydough_files", "cheatsheet_partition_overhaul.md")
    questions_csv_path = os.path.join(base_path, "TPCH", "test_data", "questions.csv")
    
    # Set up output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = os.path.join(base_path, "labeling_agent", "results")
    
    # Create output filename with timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_csv_path = os.path.join(output_dir, f"pydough_results_{timestamp}.csv")
    
    # Verify database exists
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        print("Please ensure the database file exists at the specified path.")
        return
    
    # Verify metadata file exists
    if not os.path.exists(metadata_path):
        print(f"Error: Metadata file not found at {metadata_path}")
        print("Please ensure the metadata file exists at the specified path.")
        return
        
    # Verify cheatsheet file exists
    if not os.path.exists(cheatsheet_path):
        print(f"Error: Cheatsheet file not found at {cheatsheet_path}")
        print("Please ensure the cheatsheet file exists at the specified path.")
        return

    print(f"Using database at: {db_path}")
    print(f"Using metadata at: {metadata_path}")
    print(f"Using cheatsheet at: {cheatsheet_path}")
    if args.num_questions:
        print(f"Processing {args.num_questions} questions")
    else:
        print("Processing all questions")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Process questions
    process_questions(
        questions_csv_path=questions_csv_path,
        output_csv_path=output_csv_path,
        db_path=db_path,
        metadata_path=metadata_path,
        cheatsheet_path=cheatsheet_path,
        num_questions=args.num_questions
    )
    
    print("\nProcessing complete!")
    print(f"Results saved to: {output_csv_path}")

if __name__ == "__main__":
    main() 