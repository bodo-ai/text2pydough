import pandas as pd
import os
import asyncio
from generator_agent_with_feedback import PydoughGeneratorAgent
from evaluator_agent import SQLEvaluatorAgent, compare_df
import json
from typing import Dict, Any, List
import time
import argparse
from io import StringIO
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from tqdm import tqdm
import mlflow

# Global variable to control logging backend
# Global variable to control logging backend
# USE_MLFLOW = True  # Set to False to use Phoenix instead

# # Configure MLflow
# if USE_MLFLOW:
#     MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
#     MLFLOW_TRACKING_TOKEN = os.getenv("MLFLOW_TRACKING_TOKEN", "")
#     # print(MLFLOW_TRACKING_URI)
#     os.environ["MLFLOW_TRACKING_TOKEN"] = MLFLOW_TRACKING_TOKEN
#     mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
#     mlflow.set_experiment(os.getenv("EXPERIMENT_NAME", "labeling-agent-debug"))
#     # Enable MLflow LangChain autologging
#     mlflow.langchain.autolog(
#         log_traces=True,
#         log_models=True,
#         log_input_examples=True,
#         log_model_signatures=True,
#         registered_model_name="pydough_agent"
#     )
# else:
#     # Register a Phoenix tracer
#     from phoenix.otel import register
#     API_KEY = os.getenv("PHOENIX_API_KEY")
#     COLLECTOR_ENDPOINT = os.getenv("PHOENIX_COLLECTOR_ENDPOINT")  # Ej: "http://mlflow-alb-1071096006.us-east-2.elb.amazonaws.com:6060/v1/traces"
#     tracer_provider = register(
#         endpoint=COLLECTOR_ENDPOINT,               # URL raíz sin /v1/traces
#         headers={"Authorization": f"Bearer {API_KEY}"},
#         project_name=os.getenv("EXPERIMENT_NAME", "agent-react-testing"),
#         auto_instrument=True,
#         protocol="http/protobuf"                    # Forzar uso HTTP en lugar de gRPC
#     )

# Set up executors at module level
THREAD_EXECUTOR = ThreadPoolExecutor(max_workers=os.cpu_count() * 5)
PROCESS_EXECUTOR = ProcessPoolExecutor(max_workers=os.cpu_count())

# Helper function to run blocking code in thread pool
def run_in_thread(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(THREAD_EXECUTOR, lambda: func(*args, **kwargs))

# Helper function to run CPU-bound code in process pool
def _process_wrapper(func, args, kwargs):
    return func(*args, **kwargs)

def run_in_process(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(PROCESS_EXECUTOR, _process_wrapper, func, args, kwargs)

# max number of rows used by evaluator to provide feedback. 
MAX_ROWS = 20 
# Number of concurrent questions to process
MAX_CONCURRENT_QUESTIONS = 3

async def process_single_question(
    question: str,
    sql_query: str,
    db_path: str,
    metadata_path: str,
    cheatsheet_path: str,
    dataset_name: str,
    db_name: str,
    question_id: int,
    pbar: tqdm,
    max_feedback_loops: int = 3
) -> Dict[str, Any]:
    """
    Process a single question asynchronously.
    
    Args:
        question: The question to process
        sql_query: The ground truth SQL query
        generator_agent: The generator agent instance
        evaluator_agent: The evaluator agent instance
        question_id: The ID of the question
        pbar: Progress bar instance
        max_feedback_loops: Maximum number of feedback loops between generator and evaluator
        
    Returns:
        Dictionary containing the processing results
    """
    # Initialize all variables that will be used in the result
    feedback = None
    dataframe_comparison_boolean = False
    feedback_loop_count = 0
    evaluation = {'match': None, 'explanation': None}
    generated_response = ''
    generated_pydough = ''
    executor_error = None
    
    # List to store history of all attempts
    attempt_history = []
    
    try:
        # Initialize agents
        generator_agent = PydoughGeneratorAgent(db_path, metadata_path, cheatsheet_path)
        evaluator_agent = SQLEvaluatorAgent(f"sqlite:///{db_path}")

        # Execute the ground truth SQL query once
        sql_result = await run_in_thread(evaluator_agent._convert_sql_to_dataframe, sql_query)
        ground_truth_df = pd.read_json(StringIO(sql_result))
        
        # Feedback loop between generator and evaluator
        while feedback_loop_count < max_feedback_loops and not dataframe_comparison_boolean:
            try:
                # Generate Pydough code and execute
                generated_code = await run_in_thread(
                    generator_agent.generate_and_execute,
                    question,
                    feedback
                )
                
                # Get the generated response and DataFrame
                generated_response = generated_code.get('generator_response', '')
                generated_df_json = generated_code.get('dataframe', '{}')
                generated_pydough = generated_code.get('code', '')
                error = generated_code.get('error', '')
                
                # Check if we got a valid result
                if generated_df_json is None:
                    generated_df = pd.DataFrame()
                else:
                    try:
                        generated_df = pd.read_json(StringIO(generated_df_json))
                    except Exception as e:
                        generated_df = pd.DataFrame()
                        executor_error = str(e)
                
            except Exception as e:
                generated_df = pd.DataFrame()
                generated_response = "Error in generator: " + str(e)
                generated_pydough = ""
                executor_error = str(e)
            
            # Compare the dataframes using process pool for CPU-bound work
            dataframe_comparison_boolean = False
            if not error:
                # Compare the dataframes using process pool for CPU-bound work
                dataframe_comparison_boolean = await run_in_process(
                    compare_df,
                    ground_truth_df,
                    generated_df,
                    "order_by",
                    question
                )
            if dataframe_comparison_boolean:
                break
            
            # Sample large DataFrames before sending to evaluator
            if len(generated_df) > MAX_ROWS:
                generated_df_json = generated_df.iloc[:MAX_ROWS].to_json(orient='records')
            
            if len(ground_truth_df) > MAX_ROWS:
                sql_result = ground_truth_df.iloc[:MAX_ROWS].to_json(orient='records')
            
            # Get feedback from evaluator
            evaluation = await run_in_thread(
                evaluator_agent.evaluate_responses,
                question=question,
                ground_truth_sql=sql_query,
                generated_response=generated_response,
                generated_df_json=generated_df_json,
                precomputed_match=dataframe_comparison_boolean,
                executor_error=executor_error
            )
            
            # Store this attempt in history
            attempt_history.append({
                'loop': feedback_loop_count + 1,
                'response': generated_response,
                'pydough': generated_pydough,
                'evaluation': evaluation['explanation']
            })
            
            # Construct feedback with complete history
            feedback = "Previous attempts:\n"
            for attempt in attempt_history:
                feedback += f"\nAttempt {attempt['loop']}:\n"
                feedback += f"Response: {attempt['response']}\n"
                feedback += f"Pydough: {attempt['pydough']}\n"
                feedback += f"Evaluation: {attempt['evaluation']}\n"
                feedback += "-" * 50 + "\n"
            
            # Print the feedback for monitoring
            print(f"\nFeedback for Question {question_id} (Loop {feedback_loop_count + 1}):")
            print(feedback)
            
            feedback_loop_count += 1
            
            # Update progress bar description
            pbar.set_description(f"Q{question_id} (Loop {feedback_loop_count}/{max_feedback_loops})")
        
    except Exception as e:
        result = {
            'question_id': question_id,
            'question': question,
            'ground_truth_sql': sql_query,
            'generated_response': generated_response,
            'generated_pydough': generated_pydough,
            'evaluation_match': evaluation['match'],
            'evaluation_explanation': evaluation['explanation'],
            'feedback_loops': feedback_loop_count,
            'dataframe_match': dataframe_comparison_boolean,
            'error': str(e),
            'dataset_name': dataset_name,
            'db_name': db_name
        }
        return result
    
    # Store results
    result = {
        'question_id': question_id,
        'question': question,
        'ground_truth_sql': sql_query,
        'generated_response': generated_response,
        'generated_pydough': generated_pydough,
        'evaluation_match': evaluation['match'],
        'evaluation_explanation': evaluation['explanation'],
        'feedback_loops': feedback_loop_count,
        'dataframe_match': dataframe_comparison_boolean,
        'error': None,
        'dataset_name': dataset_name,
        'db_name': db_name
    }
    
    return result

async def process_questions(
    questions_csv_path: str,
    output_csv_path: str,
    db_base_path: str,
    metadata_base_path: str,
    cheatsheet_path: str,
    num_questions: int = None,
    start_row: int = 0,
    max_feedback_loops: int = 3
) -> None:
    """
    Process questions from CSV and store results in output CSV asynchronously.
    
    Args:
        questions_csv_path: Path to the questions CSV file
        output_csv_path: Path to store the output CSV
        db_path: Path to the SQLite database file
        metadata_path: Path to the metadata graph JSON file
        cheatsheet_path: Path to the cheatsheet markdown file
        num_questions: Number of questions to process (None for all)
        start_row: Row number to start processing from (0-based index)
        max_feedback_loops: Maximum number of feedback loops between generator and evaluator
    """
    
    # Read questions
    questions_df = pd.read_csv(questions_csv_path)
    
    # Select starting row and limit number of questions if specified
    questions_df = questions_df.iloc[start_row:]
    if num_questions is not None:
        questions_df = questions_df.iloc[:num_questions]
    
    # Prepare output data
    output_data = []
    
    # Create progress bar
    pbar = tqdm(total=len(questions_df), desc="Processing questions")
    
    # Create semaphore for concurrency control
    sem = asyncio.Semaphore(MAX_CONCURRENT_QUESTIONS)
    
    async def safe_process(row, idx):
        async with sem:
            db_name = row['db_name']
            dataset_name = row['dataset_name']

            db_path = os.path.join(db_base_path, dataset_name, "databases", f"{db_name}/{db_name}.sqlite")
            metadata_dir = os.path.join(metadata_base_path, dataset_name, "metadata")
            metadata_path = os.path.join(metadata_dir, f"{db_name}_graph.json")
        
            return await process_single_question(
                question=row['question'],
                sql_query=row['sql'],
                db_path=db_path,
                metadata_path=metadata_path,
                cheatsheet_path=cheatsheet_path,
                dataset_name=dataset_name,
                db_name=db_name,
                question_id=idx + 1,
                pbar=pbar,
                max_feedback_loops=max_feedback_loops
            )
    
    # Create all tasks
    tasks = [
        asyncio.create_task(safe_process(row, idx))
        for idx, row in questions_df.iterrows()
    ]
    
    # Process results as they complete
    for coro in asyncio.as_completed(tasks):
        result = await coro
        output_data.append(result)
        
        # Update progress bar
        pbar.update(1)
        
        # Save progress after each result
        pd.DataFrame(output_data).to_csv(output_csv_path, index=False)
    
    # Close progress bar
    pbar.close()

async def main():
    # Declare global variable at the start
    global MAX_CONCURRENT_QUESTIONS
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Process questions using PyDough generator agent asynchronously.')
    parser.add_argument('--num-questions', type=int, default=None,
                      help='Number of questions to process (default: all)')
    parser.add_argument('--start-row', type=int, default=0,
                      help='Row number to start processing from (0-based index, default: 0)')
    parser.add_argument('--output-dir', type=str, default=None,
                      help='Directory to save output files (default: labeling_agent/results)')
    parser.add_argument('--concurrent-questions', type=int, default=MAX_CONCURRENT_QUESTIONS,
                      help=f'Number of questions to process concurrently (default: {MAX_CONCURRENT_QUESTIONS})')
    parser.add_argument('--max-feedback-loops', type=int, default=3,
                      help='Maximum number of feedback loops between generator and evaluator (default: 3)')
    parser.add_argument('--db-base-path', type=str, required=True,
                      help='Path to the SQLite database file')
    parser.add_argument('--metadata-base-path', type=str, required=True,
                      help='Path to the metadata graph JSON file')
    parser.add_argument('--cheatsheet-path', type=str, required=True,
                      help='Path to the cheatsheet markdown file')
    parser.add_argument('--questions-csv-path', type=str, required=True,
                      help='Path to the questions CSV file')
    args = parser.parse_args()
    
    # Update the global constant
    MAX_CONCURRENT_QUESTIONS = args.concurrent_questions
    
    # Set up output directory
    if args.output_dir:
        base_output_dir = args.output_dir
    else:
        base_output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
    
    print(f"\nBase output directory: {base_output_dir}")
    
    # Create timestamped folder for this run
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    run_output_dir = os.path.join(base_output_dir, timestamp)
    print(f"Creating run directory: {run_output_dir}")
    
    # Create both directories
    os.makedirs(base_output_dir, exist_ok=True)
    os.makedirs(run_output_dir, exist_ok=True)
    
    # Set up output paths
    output_csv_path = os.path.join(run_output_dir, "results.csv")
    print(f"Results will be saved to: {output_csv_path}")

    # Output for reprocessed csv´s
    reprocessed_questions_output = os.path.join(run_output_dir, f"reprocessed_pydough_results_{timestamp}.csv")
    
    # Verify all required files exist
    required_files = {
        'Database Directory': args.db_base_path,
        'Metadata Base Directory': args.metadata_base_path,
        'Cheatsheet': args.cheatsheet_path,
        'Questions CSV': args.questions_csv_path
    }
    
    for name, path in required_files.items():
        if not os.path.exists(path):
            print(f"Error: {name} file not found at {path}")
            print(f"Please ensure the {name.lower()} file exists at the specified path.")
            return
    
    # Read questions CSV to check for dataframe_match column
    df_questions = pd.read_csv(args.questions_csv_path)

    if 'dataframe_match' in df_questions.columns:
         # Filter rows where dataframe_match is False
        filtered_df = df_questions[df_questions['dataframe_match'] == False]

        # Reformat to original question structure
        reformatted_questions = filtered_df[['question', 'ground_truth_sql', 'dataset_name', 'db_name']] \
            .rename(columns={'ground_truth_sql': 'sql'}) \
            .to_dict(orient='records')
        
        new_csv = pd.DataFrame(reformatted_questions)

        # Save to CSV
        new_csv.to_csv(reprocessed_questions_output, index=False)

        # Process reprocessed questions
        await process_questions(
            questions_csv_path=reprocessed_questions_output,
            output_csv_path=output_csv_path,
            db_base_path=args.db_base_path,
            metadata_base_path=args.metadata_base_path,
            cheatsheet_path=args.cheatsheet_path,
            num_questions=args.num_questions,
            start_row=args.start_row,
            max_feedback_loops=args.max_feedback_loops
        )

    else:
        # Process questions
        await process_questions(
            questions_csv_path=args.questions_csv_path,
            output_csv_path=output_csv_path,
            db_base_path=args.db_base_path,
            metadata_base_path=args.metadata_base_path,
            cheatsheet_path=args.cheatsheet_path,
            num_questions=args.num_questions,
            start_row=args.start_row,
            max_feedback_loops=args.max_feedback_loops
        )
    
    # Calculate accuracy and create metadata
    results_df = pd.read_csv(output_csv_path)
    total_samples = len(results_df)
    correct_matches = results_df['dataframe_match'].sum()
    accuracy = correct_matches / total_samples if total_samples > 0 else 0
    
    metadata = {
        'timestamp': timestamp,
        'paths': {
            'database': args.db_base_path,
            'metadata_graph': args.metadata_base_path,
            'cheatsheet': args.cheatsheet_path,
            'questions_csv': args.questions_csv_path,
            'results_csv': output_csv_path
        },
        'parameters': {
            'num_questions': args.num_questions,
            'start_row': args.start_row,
            'concurrent_questions': args.concurrent_questions,
            'max_feedback_loops': args.max_feedback_loops
        },
        'results': {
            'total_samples': int(total_samples),
            'correct_matches': int(correct_matches),
            'accuracy': float(accuracy)
        }
    }
    
    # Save metadata
    metadata_path = os.path.join(run_output_dir, "metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nProcessing complete!")
    print(f"Results directory: {run_output_dir}")
    print(f"Results CSV: {output_csv_path}")
    print(f"Metadata file: {metadata_path}")
    print(f"Total samples: {total_samples}")
    print(f"Accuracy: {accuracy:.2%}")

if __name__ == "__main__":
    asyncio.run(main()) 