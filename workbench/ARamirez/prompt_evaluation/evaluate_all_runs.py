#!/usr/bin/env python3
"""
Script to evaluate all_runs files using test_data.eval functions.
This script processes the all_runs CSV file and determines if each result is a match, no match, or query error.

Outputs:
1. An identical CSV as the input CSV but with an extra column that indicates if the row was match, no_match or query error.
2. A CSV with each unique question ID and a has_match column that is TRUE only if any one result of that same question ID came up as true
"""

import argparse
import pandas as pd
import os
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import logging
import json
import random
# Progress bar
try:
    from tqdm import tqdm
except ImportError:
    # Fallback dummy tqdm in case library missing
    def tqdm(iterable=None, **kwargs):
        return iterable if iterable is not None else (lambda x: x)

# Add the current directory to the path to import test_data.eval
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from test_data.eval import process_row, compare_output

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def evaluate_all_runs(all_runs_file, db_base_path, metadata_base_path, output_dir=None, num_threads: int = None):
    """
    Evaluate all runs in the all_runs file using test_data.eval functions.
    
    Args:
        all_runs_file (str): Path to the all_runs CSV file
        db_base_path (str): Base path to the databases
        metadata_base_path (str): Base path to the metadata files
        output_dir (str): Directory to save output files (optional)
    
    Returns:
        tuple: (evaluated_df, question_summary_df)
    """
    logger.info(f"Loading all_runs file: {all_runs_file}")
    
    # Read the all_runs file
    try:
        df = pd.read_csv(all_runs_file)
        logger.info(f"Loaded {len(df)} rows from all_runs file")
    except Exception as e:
        logger.error(f"Failed to read all_runs file: {e}")
        raise
    
    # Check required columns
    required_columns = ['question', 'db_name', 'dataset_name', 'sql', 'gen_df_json']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Add extracted_python_code column if it doesn't exist
    if 'extracted_python_code' not in df.columns:
        if 'code' in df.columns:
            df['extracted_python_code'] = df['code']
        else:
            logger.warning("No 'code' column found, will use JSON comparison only")
            df['extracted_python_code'] = None
    
    # Process each row using test_data.eval functions
    logger.info("Starting evaluation of all runs...")
    
    def process_single_row(row):
        """Process a single row and return evaluation result"""
        try:
            result, exception = process_row(row, db_base_path, metadata_base_path)
            # Return only the minimal data needed to reduce memory usage
            return (result, exception)
        except Exception as e:
            logger.error(f"Error processing row {row.name}: {e}")
            return ('Error', str(e))
    
    # Determine workers
    if num_threads is None or num_threads <= 0:
        num_threads = os.cpu_count() or 4

    logger.info(f"Processing {len(df)} rows with {num_threads} threads ...")

    # Create a generator to avoid duplicating rows in memory
    rows_iterable = (row for _, row in df.iterrows())

    # Process rows in parallel with progress bar, accumulating minimal results
    comparison_results = []
    exceptions = []
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results_iter = executor.map(process_single_row, rows_iterable)
        for res, exc in tqdm(results_iter, total=len(df), desc="Evaluating"):
            comparison_results.append(res)
            exceptions.append(exc)
    
    # Merge with original data - OUTPUT 1: Identical CSV with extra column
    result_df = df.copy()
    result_df['comparison_result'] = comparison_results
    result_df['exception'] = exceptions
    
    # Create question summary - OUTPUT 2: Unique question IDs with has_match column
    question_summary_df = create_question_summary(result_df)
    
    # Save results if output directory is specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y_%m_%d-%H_%M_%S')
        
        # Save evaluated results (OUTPUT 1)
        output_file = os.path.join(output_dir, f'evaluated_all_runs_{timestamp}.csv')
        result_df.to_csv(output_file, index=False)
        logger.info(f"Saved evaluated results to: {output_file}")
        
        # Save question summary (OUTPUT 2)
        question_summary_file = os.path.join(output_dir, f'question_summary_{timestamp}.csv')
        question_summary_df.to_csv(question_summary_file, index=False)
        logger.info(f"Saved question summary to: {question_summary_file}")
        
        # Save detailed evaluation results (minimal to reduce disk/memory)
        eval_output_file = os.path.join(output_dir, f'evaluation_details_{timestamp}.csv')
        evaluation_details_df = pd.DataFrame({
            'row_index': result_df.index,
            'comparison_result': comparison_results,
            'exception': exceptions,
        })
        evaluation_details_df.to_csv(eval_output_file, index=False)
        logger.info(f"Saved evaluation details to: {eval_output_file}")
    
    return result_df, question_summary_df

def create_question_summary(df):
    """
    Create a summary DataFrame with unique question IDs and has_match column.
    
    Args:
        df (pd.DataFrame): DataFrame with evaluation results
    
    Returns:
        pd.DataFrame: Summary DataFrame with question_id and has_match columns
    """
    # Create a unique question identifier
    df['question_id'] = df['question'].astype(str) + '_' + df['db_name'].astype(str) + '_' + df['dataset_name'].astype(str)
    
    # Group by question_id and check if any result is a match
    question_groups = df.groupby('question_id').agg({
        'question': 'first',
        'db_name': 'first', 
        'dataset_name': 'first',
        'comparison_result': lambda x: 'Match' if 'Match' in x.values else 'No Match'
    }).reset_index()
    
    # Create the has_match column
    question_groups['has_match'] = question_groups['comparison_result'] == 'Match'
    
    # Reorder columns for better readability
    question_summary = question_groups[['question_id', 'question', 'db_name', 'dataset_name', 'comparison_result', 'has_match']]
    
    return question_summary

def print_summary(result_df, question_summary_df):
    """
    Print a formatted summary of the evaluation results.
    
    Args:
        result_df (pd.DataFrame): DataFrame with all evaluation results
        question_summary_df (pd.DataFrame): DataFrame with question summary
    """
    print("\n" + "="*80)
    print("EVALUATION SUMMARY")
    print("="*80)
    
    # Overall statistics
    total_runs = len(result_df)
    comparison_counts = result_df['comparison_result'].value_counts()
    total_percentages = (comparison_counts / total_runs * 100).round(2)
    
    print(f"\nOVERALL RESULTS (Total runs: {total_runs}):")
    for result_type, count in comparison_counts.items():
        percentage = total_percentages[result_type]
        print(f"  {result_type}: {count} ({percentage}%)")
    
    # Question-level statistics
    total_questions = len(question_summary_df)
    questions_with_match = question_summary_df['has_match'].sum()
    questions_without_match = total_questions - questions_with_match
    
    print(f"\nQUESTION-LEVEL RESULTS (Total unique questions: {total_questions}):")
    print(f"  Questions with at least one match: {questions_with_match} ({questions_with_match/total_questions*100:.1f}%)")
    print(f"  Questions with no matches: {questions_without_match} ({questions_without_match/total_questions*100:.1f}%)")
    
    # Model-wise statistics
    if 'model_name' in result_df.columns:
        model_stats = result_df.groupby('model_name')['comparison_result'].value_counts().unstack(fill_value=0)
        print(f"\nBY MODEL:")
        for model in model_stats.index:
            model_total = model_stats.loc[model].sum()
            print(f"\n  {model}:")
            for result_type in ['Match', 'No Match', 'Query Error', 'SQL error', 'Unknown']:
                if result_type in model_stats.columns:
                    count = model_stats.loc[model, result_type]
                    percentage = (count / model_total * 100) if model_total > 0 else 0
                    print(f"    {result_type}: {count} ({percentage:.1f}%)")
    
    # Database-wise statistics
    if 'db_name' in result_df.columns:
        db_stats = result_df.groupby('db_name')['comparison_result'].value_counts().unstack(fill_value=0)
        print(f"\nBY DATABASE:")
        for db in db_stats.index:
            db_total = db_stats.loc[db].sum()
            print(f"\n  {db}:")
            for result_type in ['Match', 'No Match', 'Query Error', 'SQL error', 'Unknown']:
                if result_type in db_stats.columns:
                    count = db_stats.loc[db, result_type]
                    percentage = (count / db_total * 100) if db_total > 0 else 0
                    print(f"    {result_type}: {count} ({percentage:.1f}%)")
    
    # Ensemble tie-break and finalist statistics (size-based selection)
    try:
        rng = random.Random(12345)

        # Compute a question_id locally (same scheme as create_question_summary)
        tmp_df = result_df.copy()
        tmp_df['question_id'] = tmp_df['question'].astype(str) + '_' + tmp_df['db_name'].astype(str) + '_' + tmp_df['dataset_name'].astype(str)

        def df_size_from_json(gen_df_json):
            if not isinstance(gen_df_json, str) or gen_df_json.strip().lower() in ('', 'nan', 'none'):
                return -1
            try:
                # Faster than constructing full pandas objects for size
                data = json.loads(gen_df_json)
                if isinstance(data, list) and data:
                    # Assume uniform keys across rows
                    num_rows = len(data)
                    num_cols = len(data[0]) if isinstance(data[0], dict) else 0
                    return num_rows * num_cols
                if isinstance(data, list):
                    return 0
                if isinstance(data, dict):
                    # Single object; treat as one row
                    return len(data)
                return -1
            except Exception:
                # Fallback: attempt cleaning for common escape/newline issues
                try:
                    cleaned = gen_df_json.replace('\n', '').replace('\r', '')
                    data = json.loads(cleaned)
                    if isinstance(data, list) and data:
                        return len(data) * (len(data[0]) if isinstance(data[0], dict) else 0)
                    if isinstance(data, dict):
                        return len(data)
                    return -1
                except Exception:
                    return -1

        total_questions = tmp_df['question_id'].nunique()
        tie_questions = 0
        single_finalist_questions = 0
        single_match_count = 0
        tie_match_count = 0

        for qid, group in tmp_df.groupby('question_id'):
            # Build sizes per row
            sizes = {}
            for idx, row in group.iterrows():
                sizes[idx] = df_size_from_json(row.get('gen_df_json', None))
            if not sizes:
                continue
            max_size = max(sizes.values()) if sizes else -1
            if max_size <= -1:
                # No valid finalists for this question
                continue
            candidates = [idx for idx, s in sizes.items() if s == max_size]
            if len(candidates) == 1:
                single_finalist_questions += 1
                winner_idx = candidates[0]
                if str(group.loc[winner_idx, 'comparison_result']).strip() == 'Match':
                    single_match_count += 1
            elif len(candidates) > 1:
                tie_questions += 1
                winner_idx = rng.choice(candidates)
                if str(group.loc[winner_idx, 'comparison_result']).strip() == 'Match':
                    tie_match_count += 1

        tie_percent = (tie_questions / total_questions * 100) if total_questions > 0 else 0.0
        single_match_pct = (single_match_count / single_finalist_questions * 100) if single_finalist_questions > 0 else 0.0
        tie_match_pct = (tie_match_count / tie_questions * 100) if tie_questions > 0 else 0.0

        print(f"\nENSEMBLE (size-based) TIE-BREAK STATS:")
        print(f"  Questions with multiple finalists (tie): {tie_questions}/{total_questions} ({tie_percent:.1f}%)")
        print(f"  Match rate where only one finalist: {single_match_count}/{single_finalist_questions} ({single_match_pct:.1f}%)")
        print(f"  Match rate where multiple finalists (random tie-break): {tie_match_count}/{tie_questions} ({tie_match_pct:.1f}%)")
    except Exception as e:
        print(f"\n[WARNING] Failed to compute ensemble tie-break statistics: {e}")

    print("\n" + "="*80)

def main():
    """Main function to run the evaluation script."""
    parser = argparse.ArgumentParser(
        description="Evaluate all_runs files using test_data.eval functions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python evaluate_all_runs.py --all-runs results/all_model_runs.csv --db-base-path /path/to/dbs --metadata-base-path /path/to/metadata
  python evaluate_all_runs.py --all-runs results/all_model_runs.csv --db-base-path /path/to/dbs --metadata-base-path /path/to/metadata --output-dir ./evaluation_results
        """
    )
    
    parser.add_argument(
        '--all-runs',
        required=True,
        help='Path to the all_runs CSV file'
    )
    
    parser.add_argument(
        '--db-base-path',
        required=True,
        help='Base path to the databases'
    )
    
    parser.add_argument(
        '--metadata-base-path',
        required=True,
        help='Base path to the metadata files'
    )
    
    parser.add_argument(
        '--output-dir',
        help='Directory to save output files (optional)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--num-threads',
        type=int,
        default=None,
        help='Number of worker threads to use for parallel evaluation (default: CPU count)'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input file
    if not os.path.exists(args.all_runs):
        logger.error(f"All runs file not found: {args.all_runs}")
        sys.exit(1)
    
    # Validate paths
    if not os.path.exists(args.db_base_path):
        logger.error(f"Database base path not found: {args.db_base_path}")
        sys.exit(1)
    
    if not os.path.exists(args.metadata_base_path):
        logger.error(f"Metadata base path not found: {args.metadata_base_path}")
        sys.exit(1)
    
    try:
        # Run evaluation
        logger.info("Starting evaluation...")
        result_df, question_summary_df = evaluate_all_runs(
            args.all_runs,
            args.db_base_path,
            args.metadata_base_path,
            args.output_dir,
            num_threads=args.num_threads
        )
        
        # Print summary
        print_summary(result_df, question_summary_df)
        
        logger.info("Evaluation completed successfully!")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
