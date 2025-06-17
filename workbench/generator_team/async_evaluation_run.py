import pandas as pd
import os
import asyncio
from generator_team.agents.ReAct import PydoughGeneratorAgent
from evaluator_agent import SQLEvaluatorAgent, compare_df
import json
from typing import Dict, Any, List
import time
import argparse
from io import StringIO
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from tqdm import tqdm
import atexit
import signal
import sys
import re


# Auto‑patch LangChain & LangGraph
from openinference.instrumentation.langchain import LangChainInstrumentor 
LangChainInstrumentor().instrument()

# Register a Phoenix tracer
from phoenix.otel import register
tracer_provider = register(
    project_name=os.getenv("EXPERIMENT_NAME", "pydough-demo-2.5pro"),  # Use environment variable with fallback
    auto_instrument=True          # captures every LC/LG call automatically
)


# Set up executors at module level
THREAD_EXECUTOR = ThreadPoolExecutor(max_workers=os.cpu_count() * 5)
PROCESS_EXECUTOR = None  # Initialize as None, will be created when needed

# Cleanup function for executors
def cleanup_executors():
    """Clean up executors when the program exits."""
    # print("Cleaning up executors...")
    THREAD_EXECUTOR.shutdown(wait=True)
    if PROCESS_EXECUTOR is not None:
        PROCESS_EXECUTOR.shutdown(wait=True)

# Register cleanup function
atexit.register(cleanup_executors)

# Signal handler for graceful shutdown
def signal_handler(signum, frame):
    """Handle signals for graceful shutdown."""
    # print(f"\nReceived signal {signum}, shutting down gracefully...")
    cleanup_executors()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Helper function to run blocking code in thread pool
def run_in_thread(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(THREAD_EXECUTOR, lambda: func(*args, **kwargs))

# Helper function to run CPU-bound code in process pool
def _process_wrapper(func, args, kwargs):
    return func(*args, **kwargs)

def run_in_process(func, *args, **kwargs):
    global PROCESS_EXECUTOR
    if PROCESS_EXECUTOR is None:
        PROCESS_EXECUTOR = ProcessPoolExecutor(max_workers=os.cpu_count())
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(PROCESS_EXECUTOR, _process_wrapper, func, args, kwargs)

# max number of rows used by evaluator to provide feedback. 
MAX_ROWS = 20 
# Number of concurrent questions to process
MAX_CONCURRENT_QUESTIONS = 3

async def process_single_question(
    question: str,
    sql_query: str,
    generator_agent: PydoughGeneratorAgent,
    evaluator_agent: SQLEvaluatorAgent,
    question_id: int,
    pbar: tqdm,
    max_feedback_loops: int = 3
) -> Dict[str, Any]:
    """
    Process a single question asynchronously.
    """
    # print("\n" + "="*50, flush=True)
    # print(f"STARTING PROCESSING FOR QUESTION {question_id}", flush=True)
    # print("="*50 + "\n", flush=True)
    
    # Initialize all variables that will be used in the result
    feedback = None
    dataframe_comparison_boolean = False
    feedback_loop_count = 0
    evaluation = {'match': None, 'explanation': None}
    generated_response = ''
    generated_pydough = ''
    executor_error = None
    
    try:
        # Execute the ground truth SQL query once
        sql_result = await run_in_thread(evaluator_agent._convert_sql_to_dataframe, sql_query)
        ground_truth_df = pd.read_json(StringIO(sql_result))
        
        # Feedback loop between generator and evaluator (if max_feedback_loops > 0)
        while (max_feedback_loops > 0 and feedback_loop_count < max_feedback_loops and not dataframe_comparison_boolean) or feedback_loop_count == 0:
            try:
                # print("\n" + "-"*50, flush=True)
                # print(f"GENERATOR CALL {feedback_loop_count + 1}", flush=True)
                # print("-"*50 + "\n", flush=True)
                
                # Generate Pydough code and execute
                generated_code = await run_in_thread(
                    generator_agent.generate_and_execute,
                    question if feedback is None else feedback
                )
                
                # print("\nGENERATOR RESPONSE:", flush=True)
                # print(f"Type: {type(generated_code)}", flush=True)
                # print(f"Keys: {generated_code.keys() if isinstance(generated_code, dict) else 'Not a dict'}", flush=True)
                # print(f"Full response: {generated_code}", flush=True)
                
                # Get the generated response and DataFrame
                generated_response = generated_code.get('generator_response', '')
                generated_df_json = generated_code.get('dataframe', '{}')
                generated_pydough = generated_code.get('pydough_code', '')
                
                # print("\nEXTRACTED VALUES:", flush=True)
                # print(f"Generated response: {generated_response}", flush=True)
                # print(f"Generated PyDough: {generated_pydough}", flush=True)
                # print(f"DataFrame JSON: {generated_df_json}", flush=True)
                
                # If we don't have the PyDough code, try to extract it
                if not generated_pydough and generated_response:
                    # print("\nATTEMPTING TO EXTRACT PYDOUGH CODE:", flush=True)
                    code_match = re.search(r'```python\n(.*?)\n```', generated_response, re.DOTALL)
                    if code_match:
                        generated_pydough = code_match.group(1).strip()
                        # print(f"Extracted code: {generated_pydough}", flush=True)
                    else:
                        # print("No code block found in response", flush=True)
                        pass
                
                # Check if we got a valid result
                if generated_df_json is None:
                    generated_df = pd.DataFrame()
                else:
                    try:
                        generated_df = pd.read_json(StringIO(generated_df_json))
                    except Exception as e:
                        generated_df = pd.DataFrame()
                        executor_error = str(e)
                
                # print("\nDATAFRAME STATUS:", flush=True)
                # print(f"Shape: {generated_df.shape}", flush=True)
                # print(f"Error: {executor_error}", flush=True)
                
            except Exception as e:
                # print("\nGENERATOR ERROR:", flush=True)
                # print(f"Error: {str(e)}", flush=True)
                generated_df = pd.DataFrame()
                generated_response = "Error in generator: " + str(e)
                generated_pydough = ""
                executor_error = str(e)
            
            # Compare the dataframes using process pool for CPU-bound work
            dataframe_comparison_boolean = await run_in_process(
                compare_df,
                ground_truth_df,
                generated_df,
                "order_by",
                question
            )
            
            if max_feedback_loops == 0 or dataframe_comparison_boolean:
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
            
            feedback = evaluation['explanation'] + "\n\n Previous Agent Response:\n" + evaluation['generated_response']
            feedback_loop_count += 1
            
            # Update progress bar description
            if max_feedback_loops > 0:
                pbar.set_description(f"Q{question_id} (Loop {feedback_loop_count}/{max_feedback_loops})")
            else:
                pbar.set_description(f"Q{question_id}")
        
    except Exception as e:
        # print("\nPROCESSING ERROR:", flush=True)
        # print(f"Error: {str(e)}", flush=True)
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
            'error': str(e)
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
        'error': None
    }
    
    # print("\n" + "="*50, flush=True)
    # print("FINAL RESULT:", flush=True)
    # print(f"Generated response: {result['generated_response']}", flush=True)
    # print(f"Generated PyDough: {result['generated_pydough']}", flush=True)
    # print("="*50 + "\n", flush=True)
    
    return result

async def process_questions(
    questions_csv_path: str,
    output_csv_path: str,
    db_path: str,
    metadata_path: str,
    cheatsheet_path: str,
    num_questions: int = None,
    start_row: int = 0,
    max_feedback_loops: int = 3,
    use_cheatsheet: bool = True,
    model_name: str = "gpt-4-turbo-preview",
    temperature: float = 0.7,
    top_p: float = 0.95
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
        use_cheatsheet: Whether to use the cheatsheet in the generator agent
        model_name: Name of the model to use for the PyDough generator
        temperature: Temperature parameter for model generation
        top_p: Top-p parameter for model generation
    """
    # Initialize agents
    generator_agent = PydoughGeneratorAgent(
        db_path=db_path,
        metadata_path=metadata_path,
        cheatsheet_path=cheatsheet_path if use_cheatsheet else None,
        model_name=model_name,
        temperature=temperature,
        top_p=top_p
    )
    evaluator_agent = SQLEvaluatorAgent(f"sqlite:///{db_path}")
    
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
            return await process_single_question(
                question=row['question'],
                sql_query=row['sql'],
                generator_agent=generator_agent,
                evaluator_agent=evaluator_agent,
                question_id=idx + 1,
                pbar=pbar,
                max_feedback_loops=max_feedback_loops
            )
    
    # Create all tasks
    tasks = [
        asyncio.create_task(safe_process(row, idx))
        for idx, row in questions_df.iterrows()
    ]
    
    try:
        # Process results as they complete
        for coro in asyncio.as_completed(tasks):
            result = await coro
            output_data.append(result)
            
            # Update progress bar
            pbar.update(1)
            
            # Save progress after each result
            df = pd.DataFrame(output_data)
            df.to_csv(output_csv_path, index=False)
    
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        raise
    finally:
        # Close progress bar
        pbar.close()

    # Calculate final statistics
    results_df = pd.read_csv(output_csv_path)
    total_samples = len(results_df)
    correct_matches = results_df['dataframe_match'].sum()
    accuracy = correct_matches / total_samples if total_samples > 0 else 0

    print(f"\nProcessing complete!")
    print(f"Results saved to: {output_csv_path}")
    print(f"Total samples processed: {total_samples}")
    print(f"Correct matches: {correct_matches}")
    print(f"Accuracy: {accuracy:.2%}")

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
                      help='Directory to save output files (default: generator_team/results)')
    parser.add_argument('--concurrent-questions', type=int, default=MAX_CONCURRENT_QUESTIONS,
                      help=f'Number of questions to process concurrently (default: {MAX_CONCURRENT_QUESTIONS})')
    parser.add_argument('--max-feedback-loops', type=int, default=3,
                      help='Maximum number of feedback loops between generator and evaluator (default: 3)')
    parser.add_argument('--db-path', type=str, required=True,
                      help='Path to the SQLite database file')
    parser.add_argument('--metadata-path', type=str, required=True,
                      help='Path to the metadata graph JSON file')
    parser.add_argument('--cheatsheet-path', type=str, required=True,
                      help='Path to the cheatsheet markdown file')
    parser.add_argument('--questions-csv-path', type=str, required=True,
                      help='Path to the questions CSV file')
    parser.add_argument('--use-cheatsheet', type=str, default='true',
                      help='Whether to use the cheatsheet in the generator agent (default: true)')
    parser.add_argument('--model-name', type=str, default='gpt-4-turbo-preview',
                      help='Name of the model to use for the PyDough generator (default: gpt-4-turbo-preview)')
    parser.add_argument('--experiment-name', type=str, default='default_experiment',
                      help='Name of the experiment for Phoenix logging (default: default_experiment)')
    parser.add_argument('--temperature', type=float, default=0.7,
                      help='Temperature parameter for model generation (default: 0.7)')
    parser.add_argument('--top-p', type=float, default=0.95,
                      help='Top-p parameter for model generation (default: 0.95)')
    args = parser.parse_args()
    
    # Convert use_cheatsheet string to boolean
    use_cheatsheet = args.use_cheatsheet.lower() == 'true'
    
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
    
    # Verify all required files exist
    required_files = {
        'Database': args.db_path,
        'Metadata': args.metadata_path,
        'Cheatsheet': args.cheatsheet_path,
        'Questions CSV': args.questions_csv_path
    }
    
    for name, path in required_files.items():
        if not os.path.exists(path):
            # print(f"Error: {name} file not found at {path}")
            # print(f"Please ensure the {name.lower()} file exists at the specified path.")
            return
    
    # Process questions
    await process_questions(
        questions_csv_path=args.questions_csv_path,
        output_csv_path=output_csv_path,
        db_path=args.db_path,
        metadata_path=args.metadata_path,
        cheatsheet_path=args.cheatsheet_path,
        num_questions=args.num_questions,
        start_row=args.start_row,
        max_feedback_loops=args.max_feedback_loops,
        use_cheatsheet=use_cheatsheet,
        model_name=args.model_name,
        temperature=args.temperature,
        top_p=args.top_p
    )
    
    # Calculate accuracy and create metadata
    results_df = pd.read_csv(output_csv_path)
    total_samples = len(results_df)
    correct_matches = results_df['dataframe_match'].sum()
    accuracy = correct_matches / total_samples if total_samples > 0 else 0
    
    metadata = {
        'timestamp': timestamp,
        'paths': {
            'database': args.db_path,
            'metadata_graph': args.metadata_path,
            'cheatsheet': args.cheatsheet_path,
            'questions_csv': args.questions_csv_path,
            'results_csv': output_csv_path
        },
        'parameters': {
            'num_questions': args.num_questions,
            'start_row': args.start_row,
            'concurrent_questions': args.concurrent_questions,
            'max_feedback_loops': args.max_feedback_loops,
            'experiment_name': args.experiment_name,
            'model_name': args.model_name,
            'use_cheatsheet': use_cheatsheet,
            'temperature': args.temperature,
            'top_p': args.top_p
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

if __name__ == "__main__":
    asyncio.run(main()) 