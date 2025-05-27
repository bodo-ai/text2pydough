import mlflow
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
from dynamic_prompt.generate_pydough_metadata import generate_metadata

mlflow.set_tracking_uri("http://127.0.0.1:5000")
experiment = mlflow.set_experiment("labeling_agent")

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
# max number of feedback loops between generator and evaluator
MAX_FEEDBACK_LOOPS = 7
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
    pbar: tqdm
) -> Dict[str, Any]:
    """
    Process a single question asynchronously.
    
    Args:
        question: The question to process
        sql_query: The ground truth SQL query
        db_path: The database path
        metada_path: The metadata path 
	cheatsheet_path: The cheatsheet path 
        question_id: The ID of the question
        pbar: Progress bar instance
        
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
    
    try:
        generator_agent = PydoughGeneratorAgent(db_path, metadata_path, cheatsheet_path)
        evaluator_agent = SQLEvaluatorAgent(f"sqlite:///{db_path}", cheatsheet_path)

        # Execute the ground truth SQL query once
        sql_result = await run_in_thread(evaluator_agent._convert_sql_to_dataframe, sql_query)
        ground_truth_df = pd.read_json(StringIO(sql_result))
        
        # Feedback loop between generator and evaluator
        while feedback_loop_count < MAX_FEEDBACK_LOOPS and not dataframe_comparison_boolean:
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
                
                # Check if we got a valid result
                if generated_df_json is None:
                    generated_df = pd.DataFrame()
                else:
                    try:
                        generated_df = pd.read_json(StringIO(generated_df_json))
                    except Exception:
                        generated_df = pd.DataFrame()
                
            except Exception as e:
                generated_df = pd.DataFrame()
                generated_response = "Error in generator: " + str(e)
                generated_pydough = ""
            
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

            )
            
            feedback = evaluation['explanation'] + "\n\n Previous Agent Response:\n" + evaluation['generated_response']
            feedback_loop_count += 1
            
            # Update progress bar description
            pbar.set_description(f"Q{question_id} (Loop {feedback_loop_count}/{MAX_FEEDBACK_LOOPS})")
        
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
    start_row: int = 0
) -> None:
    """
    Process questions from CSV and store results in output CSV asynchronously.
    
    Args:
        questions_csv_path: Path to the questions CSV file
        output_csv_path: Path to store the output CSV
        db_base_path: Path to the SQLite database file
        metadata_base_path: Path to the metadata graph JSON file
        cheatsheet_path: Path to the cheatsheet markdown file
        num_questions: Number of questions to process (None for all)
        start_row: Row number to start processing from (0-based index)
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

            if not os.path.exists(metadata_path):
                os.makedirs(metadata_dir, exist_ok=True)  # Correct call to makedirs
                md = generate_metadata(db_path, db_name)
                with open(metadata_path, 'w') as f:
                    json.dump(md, f, indent=2)

            return await process_single_question(
                question=row['question'],
                sql_query=row['sql'],
                db_path=db_path,
                metadata_path=metadata_path,
                cheatsheet_path=cheatsheet_path,
                dataset_name=dataset_name,
                db_name=db_name,
                question_id=idx + 1,
                pbar=pbar
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
        output_dir = args.output_dir
    else:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
        
    # Create output filename with timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_csv_path = os.path.join(output_dir, f"pydough_results_{timestamp}.csv")

    # Output for reprocessed csv´s
    reprocessed_questions_output = os.path.join(output_dir, f"reprocessed_pydough_results_{timestamp}.csv")
        
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
        
        # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
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

        # Process questions
        await process_questions(
                questions_csv_path=reprocessed_questions_output,
                output_csv_path=output_csv_path,
                db_base_path=args.db_base_path,
                metadata_base_path=args.metadata_base_path,
                cheatsheet_path=args.cheatsheet_path,
                num_questions=args.num_questions,
                start_row=args.start_row
            )
    else:
        #Process question
        await process_questions(
                questions_csv_path=args.questions_csv_path,
                output_csv_path=output_csv_path,
                db_base_path=args.db_base_path,
                metadata_base_path=args.metadata_base_path,
                cheatsheet_path=args.cheatsheet_path,
                num_questions=args.num_questions,
                start_row=args.start_row
            )
        
    print(f"\nProcessing complete! Results saved to: {output_csv_path}")

if __name__ == "__main__":
    
    with mlflow.start_run(description="Testing langchain autolog", run_name="Langchain test", experiment_id=experiment.experiment_id):
        mlflow.langchain.autolog()
        asyncio.run(main()) 