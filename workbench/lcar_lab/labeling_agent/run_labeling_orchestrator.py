import pandas as pd
import os
from generator_agent_with_feedback import PydoughGeneratorAgent
from evaluator_agent import SQLEvaluatorAgent, compare_df
import json
from typing import Dict, Any, List
import time
import argparse
from io import StringIO

# max number of rows used by evaluator to provide feedback. 
MAX_ROWS = 10 
# max number of feedback loops between generator and evaluator
MAX_FEEDBACK_LOOPS = 3

def process_questions(
    questions_csv_path: str,
    output_csv_path: str,
    db_path: str,
    metadata_path: str,
    cheatsheet_path: str,
    num_questions: int = None,
    start_row: int = 0
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
        start_row: Row number to start processing from (0-based index)
    """
    # Initialize agents
    print("ORCHESTRATOR: Initializing agents...")
    generator_agent = PydoughGeneratorAgent(db_path, metadata_path, cheatsheet_path)
    evaluator_agent = SQLEvaluatorAgent(f"sqlite:///{db_path}")
    
    # Read questions
    print(f"ORCHESTRATOR: Reading questions from {questions_csv_path}")
    questions_df = pd.read_csv(questions_csv_path)
    
    # Select starting row and limit number of questions if specified
    questions_df = questions_df.iloc[start_row:]
    if num_questions is not None:
        questions_df = questions_df.iloc[:num_questions]
    
    print(f"ORCHESTRATOR: Starting from row {start_row + 1}")
    print(f"ORCHESTRATOR: Processing {len(questions_df)} questions out of {len(pd.read_csv(questions_csv_path))} total questions")
    
    # Prepare output data
    output_data = []
    
    # Process each question
    for idx, row in questions_df.iterrows():
        question = row['question']
        sql_query = row['sql']  # Get the SQL query from the CSV
        
        print(f"\nORCHESTRATOR: Processing question {idx + 1}: {question}")
        print(f"ORCHESTRATOR: Ground truth SQL: {sql_query}")
        
        try:
            # Initialize feedback loop variables
            feedback = None
            dataframe_comparison_boolean = False
            feedback_loop_count = 0
            
            # Execute the ground truth SQL query once
            print("ORCHESTRATOR: Executing ground truth SQL query...")
            sql_result = evaluator_agent._convert_sql_to_dataframe(sql_query)
            ground_truth_df = pd.read_json(StringIO(sql_result))
            print(f"ORCHESTRATOR: Ground truth DataFrame shape: {ground_truth_df.shape}")
            print(f"ORCHESTRATOR: Ground truth DataFrame columns: {ground_truth_df.columns.tolist()}")
            
            # Feedback loop between generator and evaluator
            while feedback_loop_count < MAX_FEEDBACK_LOOPS and not dataframe_comparison_boolean:
                print(f"\nORCHESTRATOR: Feedback loop iteration {feedback_loop_count + 1}/{MAX_FEEDBACK_LOOPS}")
                
                try:
                    # Generate Pydough code and execute
                    print("ORCHESTRATOR: Generating and executing Pydough code...")
                    generated_code = generator_agent.generate_and_execute(question, feedback)
                    
                    # Get the generated response and DataFrame
                    generated_response = generated_code.get('generator_response', '')
                    generated_df_json = generated_code.get('dataframe', '{}')
                    generated_pydough = generated_code.get('code', '')
                    
                    print(f"ORCHESTRATOR: Generated Pydough code:\n{generated_pydough}")
                    
                    # Check if we got a valid result
                    if generated_df_json is None:
                        print("ORCHESTRATOR: Error: Generated DataFrame JSON is None")
                        print("ORCHESTRATOR: Using empty DataFrame for evaluation")
                        generated_df = pd.DataFrame()
                    else:
                        try:
                            generated_df = pd.read_json(StringIO(generated_df_json))
                        except Exception as e:
                            print(f"ORCHESTRATOR: Error parsing generated DataFrame JSON: {str(e)}")
                            print("ORCHESTRATOR: Using empty DataFrame for evaluation")
                            generated_df = pd.DataFrame()
                    
                except Exception as e:
                    print(f"ORCHESTRATOR: Error in generator: {str(e)}")
                    print("ORCHESTRATOR: Using empty DataFrame for evaluation")
                    generated_df = pd.DataFrame()
                    generated_response = "Error in generator: " + str(e)
                    generated_pydough = ""
                
                print(f"ORCHESTRATOR: Generated DataFrame shape: {generated_df.shape}")
                print(f"ORCHESTRATOR: Generated DataFrame columns: {generated_df.columns.tolist()}")
                
                # Compare the dataframes
                dataframe_comparison_boolean = compare_df(ground_truth_df, generated_df, "order_by", question)
                print(f"ORCHESTRATOR: DataFrame comparison result: {dataframe_comparison_boolean}")
                
                if dataframe_comparison_boolean:
                    print("ORCHESTRATOR: DataFrames match! Ending feedback loop.")
                    break
                
                # Sample large DataFrames before sending to evaluator
                if len(generated_df) > MAX_ROWS:
                    print(f"ORCHESTRATOR: Generated DataFrame is large ({len(generated_df)} rows), sampling {MAX_ROWS} rows")
                    generated_df_json = generated_df.iloc[:MAX_ROWS].to_json()#orient='records')
                
                if len(ground_truth_df) > MAX_ROWS:
                    print(f"ORCHESTRATOR: Ground truth DataFrame is large ({len(ground_truth_df)} rows), sampling {MAX_ROWS} rows")
                    sql_result = ground_truth_df.iloc[:MAX_ROWS].to_json()#orient='records')
                
                # Get feedback from evaluator
                print("ORCHESTRATOR: Getting feedback from evaluator...")
                evaluation = evaluator_agent.evaluate_responses(
                    question=question,
                    ground_truth_sql=sql_query,
                    generated_response=generated_response,
                    generated_df_json=generated_df_json,
                    precomputed_match=dataframe_comparison_boolean
                )
                
                feedback = evaluation['explanation'] + "\n\n Previous Agent Response:\n" + evaluation['generated_response']
                print(f"ORCHESTRATOR: Evaluator feedback: {feedback}")
                
                feedback_loop_count += 1
            
            # Store results
            result = {
                'question_id': idx + 1,
                'question': question,
                'ground_truth_sql': sql_query,
                'generated_response': generated_response,
                'generated_pydough': generated_pydough,
                'evaluation_match': evaluation['match'],
                'evaluation_explanation': evaluation['explanation'],
                'feedback_loops': feedback_loop_count,
                'dataframe_match': dataframe_comparison_boolean,
                'error': None
            }
            
        except Exception as e:
            print(f"ORCHESTRATOR: Error processing question {idx + 1}: {str(e)}")
            print(f"ORCHESTRATOR: Error type: {type(e)}")
            import traceback
            print(f"ORCHESTRATOR: Traceback: {traceback.format_exc()}")
            result = {
                'question_id': idx + 1,
                'question': question,
                'ground_truth_sql': sql_query,
                'generated_response': '',
                'generated_pydough': '',
                'evaluation_match': None,
                'evaluation_explanation': None,
                'feedback_loops': feedback_loop_count,
                'dataframe_match': False,
                'error': str(e)
            }
        
        output_data.append(result)
        
        # Save progress after each question
        pd.DataFrame(output_data).to_csv(output_csv_path, index=False)
        print(f"ORCHESTRATOR: Saved progress to {output_csv_path}")
        
        # Add a small delay to avoid overwhelming the system
        time.sleep(1)

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Process questions using PyDough generator agent.')
    parser.add_argument('--num-questions', type=int, default=None,
                      help='Number of questions to process (default: all)')
    parser.add_argument('--start-row', type=int, default=0,
                      help='Row number to start processing from (0-based index, default: 0)')
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
        print(f"ORCHESTRATOR: Error: Database file not found at {db_path}")
        print("ORCHESTRATOR: Please ensure the database file exists at the specified path.")
        return
    
    # Verify metadata file exists
    if not os.path.exists(metadata_path):
        print(f"ORCHESTRATOR: Error: Metadata file not found at {metadata_path}")
        print("ORCHESTRATOR: Please ensure the metadata file exists at the specified path.")
        return
        
    # Verify cheatsheet file exists
    if not os.path.exists(cheatsheet_path):
        print(f"ORCHESTRATOR: Error: Cheatsheet file not found at {cheatsheet_path}")
        print("ORCHESTRATOR: Please ensure the cheatsheet file exists at the specified path.")
        return

    print(f"ORCHESTRATOR: Using database at: {db_path}")
    print(f"ORCHESTRATOR: Using metadata at: {metadata_path}")
    print(f"ORCHESTRATOR: Using cheatsheet at: {cheatsheet_path}")
    if args.num_questions:
        print(f"ORCHESTRATOR: Processing {args.num_questions} questions")
    else:
        print("ORCHESTRATOR: Processing all questions")
    print(f"ORCHESTRATOR: Starting from row {args.start_row + 1}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Process questions
    process_questions(
        questions_csv_path=questions_csv_path,
        output_csv_path=output_csv_path,
        db_path=db_path,
        metadata_path=metadata_path,
        cheatsheet_path=cheatsheet_path,
        num_questions=args.num_questions,
        start_row=args.start_row
    )
    
    print("\nORCHESTRATOR: Processing complete!")
    print(f"ORCHESTRATOR: Results saved to: {output_csv_path}")

if __name__ == "__main__":
    main() 