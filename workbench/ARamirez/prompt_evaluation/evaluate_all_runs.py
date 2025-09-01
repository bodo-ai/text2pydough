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
import re
try:
    import mlflow
except Exception:
    mlflow = None
try:
    from dotenv import load_dotenv
    from pathlib import Path
except Exception:
    load_dotenv = None
# Progress bar
try:
    from tqdm import tqdm
except ImportError:
    # Fallback dummy tqdm in case library missing
    def tqdm(iterable=None, **kwargs):
        return iterable if iterable is not None else (lambda x: x)

# Add the current directory to the path to import test_data.eval
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from test_data.eval import process_row, compare_output, symetric_compare_df
from ensemble_logic import selection_random_tie_break, selection_density_tie_break, selection_size_tie_break, ensemble_from_all_runs_df

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def _normalize_eval_result_to_comparison(value: str) -> str:
    """Normalize eval_result values into comparison_result categories.

    Output space: 'Match', 'No Match', 'Query Error'.
    """
    if value is None:
        return 'Query Error'
    text = str(value).strip()
    if text.lower() == 'match':
        return 'Match'
    if text.replace(' ', '').lower() == 'nomatch':
        return 'No Match'
    if text.lower() == 'no match':
        return 'No Match'
    # Collapse all other error-like statuses into Query Error
    if 'error' in text.lower() or 'unknown' in text.lower() or 'sql' in text.lower() or 'query' in text.lower():
        return 'Query Error'
    return 'Query Error'

def evaluate_from_eval_column(all_runs_file: str, output_dir: str = None, eval_column: str = 'eval_result'):
    """
    Build result_df and question_summary_df using an existing eval_result column without executing code.

    Returns tuple: (result_df, question_summary_df)
    """
    logger.info(f"Loading all_runs file (eval-only): {all_runs_file}")
    try:
        df = pd.read_csv(all_runs_file)
    except Exception as e:
        logger.error(f"Failed to read all_runs file: {e}")
        raise

    if eval_column not in df.columns:
        raise ValueError(f"Column '{eval_column}' not found in input CSV")

    result_df = df.copy()
    result_df['comparison_result'] = result_df[eval_column].map(_normalize_eval_result_to_comparison)
    # Keep an exception column for schema parity; not applicable in eval-only
    result_df['exception'] = None

    question_summary_df = create_question_summary(result_df)

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y_%m_%d-%H_%M_%S')
        output_file = os.path.join(output_dir, f'evaluated_all_runs_{timestamp}.csv')
        result_df.to_csv(output_file, index=False)
        logger.info(f"Saved evaluated results to: {output_file}")
        question_summary_file = os.path.join(output_dir, f'question_summary_{timestamp}.csv')
        question_summary_df.to_csv(question_summary_file, index=False)
        logger.info(f"Saved question summary to: {question_summary_file}")

    return result_df, question_summary_df

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

def _parse_df_from_json(gen_df_json):
    """Parse a pandas DataFrame from a gen_df_json string; return None on failure."""
    if not isinstance(gen_df_json, str) or gen_df_json.strip().lower() in ('', 'nan', 'none'):
        return None
    try:
        data = json.loads(gen_df_json)
        if isinstance(data, list):
            return pd.DataFrame(data)
        if isinstance(data, dict):
            return pd.DataFrame([data])
        return None
    except Exception:
        try:
            cleaned = gen_df_json.replace('\n', '').replace('\r', '')
            data = json.loads(cleaned)
            if isinstance(data, list):
                return pd.DataFrame(data)
            if isinstance(data, dict):
                return pd.DataFrame([data])
            return None
        except Exception:
            return None


def _compute_ensemble_stats(result_df: pd.DataFrame, selection_method: str, tie_breaker: str = 'random'):
    """
    Compute tie-break and finalist statistics using ensemble logic criteria.
    Returns a dict with keys: total_questions, tie_questions, single_finalist_questions,
    single_match_count, tie_match_count.
    """
    tmp_df = result_df.copy()
    tmp_df['question_id'] = tmp_df['question'].astype(str) + '_' + tmp_df['db_name'].astype(str) + '_' + tmp_df['dataset_name'].astype(str)

    rng_local = random.Random(12345)

    total_questions = tmp_df['question_id'].nunique()
    tie_questions = 0
    single_finalist_questions = 0
    single_match_count = 0
    tie_match_count = 0

    # Track overall selected-winner outcomes per method
    considered_questions = 0  # questions where at least one candidate existed
    winner_match_count = 0
    winner_no_match_count = 0
    winner_query_error_count = 0

    for qid, group in tmp_df.groupby('question_id'):
        # Build runs with parsed DataFrames and keep mapping to original row index
        runs = []
        for idx, row in group.iterrows():
            df_obj = _parse_df_from_json(row.get('gen_df_json'))
            runs.append({
                'row_index': idx,
                'df': df_obj,
                'model_name': row.get('model_name'),
            })

        valid_indices = [i for i, r in enumerate(runs) if r['df'] is not None]
        if not valid_indices:
            continue

        candidates = []
        # Determine finalists by selection method
        if selection_method == 'size':
            sizes = {}
            for i in valid_indices:
                try:
                    sizes[i] = runs[i]['df'].size
                except Exception:
                    sizes[i] = -1
            if not sizes:
                continue
            max_size = max(sizes.values())
            if max_size <= -1:
                continue
            candidates = [i for i, s in sizes.items() if s == max_size]
        elif selection_method == 'density':
            densities = {}
            for i in valid_indices:
                try:
                    df_obj = runs[i]['df']
                    # Ensure df_obj is a pandas DataFrame before processing
                    if not isinstance(df_obj, pd.DataFrame):
                        try:
                            df_obj = pd.DataFrame(df_obj)
                        except Exception:
                            densities[i] = -1.0
                            continue
                    rows, cols = df_obj.shape
                    denom = rows * cols
                    if denom <= 0:
                        densities[i] = -1.0
                    else:
                        try:
                            bytes_used = df_obj.memory_usage(deep=True).sum()
                        except Exception:
                            bytes_used = df_obj.memory_usage(deep=False).sum()
                        densities[i] = float(bytes_used) / float(denom)
                except Exception:
                    densities[i] = -1.0
            if not densities:
                continue
            max_density = max(densities.values())
            if max_density <= -1:
                continue
            candidates = [i for i, d in densities.items() if d == max_density]
        elif selection_method == 'frequency':
            consensus = {i: 0 for i in valid_indices}
            for i in range(len(runs)):
                if i not in valid_indices:
                    continue
                for j in range(i + 1, len(runs)):
                    if j not in valid_indices:
                        continue
                    try:
                        if symetric_compare_df(runs[i]['df'], runs[j]['df'], query_category='a', question=group.iloc[0]['question']):
                            consensus[i] += 1
                            consensus[j] += 1
                    except Exception:
                        pass
            if len(consensus) == 0:
                continue
            max_votes = max(consensus.values())
            candidates = [i for i, v in consensus.items() if v == max_votes]
        elif selection_method == 'random':
            candidates = valid_indices.copy()
        elif selection_method == 'agent_indiv_grade':
            # Stats-only path: treat as having all valid candidates; tie-breaker decides winner
            candidates = valid_indices.copy()
        
        else:
            # Default to size
            sizes = {}
            for i in valid_indices:
                try:
                    sizes[i] = runs[i]['df'].size
                except Exception:
                    sizes[i] = -1
            if not sizes:
                continue
            max_size = max(sizes.values())
            if max_size <= -1:
                continue
            candidates = [i for i, s in sizes.items() if s == max_size]

        if not candidates:
            continue

        if len(candidates) == 1:
            single_finalist_questions += 1
            winner_i = candidates[0]
            winner_row_idx = runs[winner_i]['row_index']
            if str(group.loc[winner_row_idx, 'comparison_result']).strip() == 'Match':
                single_match_count += 1
        else:
            tie_questions += 1
            # Use selected tie-breaker
            if tie_breaker == 'density':
                # Build minimal runs for density tie-breaker
                tb_runs = runs
                winner_i = selection_density_tie_break(candidates, tb_runs, question_idx='?')
            elif tie_breaker == 'size':
                tb_runs = runs
                winner_i = selection_size_tie_break(candidates, tb_runs, question_idx='?')
            else:
                winner_i = selection_random_tie_break(candidates, question_idx='?')
            # Fallbacks
            if winner_i is None:
                winner_i = rng_local.choice(candidates)
            winner_row_idx = runs[winner_i]['row_index']
            if str(group.loc[winner_row_idx, 'comparison_result']).strip() == 'Match':
                tie_match_count += 1

        # Count winner outcome categories
        try:
            considered_questions += 1
            outcome = str(group.loc[winner_row_idx, 'comparison_result']).strip()
            if outcome == 'Match':
                winner_match_count += 1
            elif outcome == 'No Match':
                winner_no_match_count += 1
            else:
                # Treat any other status as Query Error (includes 'Query Error', 'SQL error', 'Unknown')
                winner_query_error_count += 1
        except Exception:
            # If any lookup fails, count as query error for robustness
            considered_questions += 1
            winner_query_error_count += 1

    return {
        'total_questions': total_questions,
        'tie_questions': tie_questions,
        'single_finalist_questions': single_finalist_questions,
        'single_match_count': single_match_count,
        'tie_match_count': tie_match_count,
        'considered_questions': considered_questions,
        'winner_match_count': winner_match_count,
        'winner_no_match_count': winner_no_match_count,
        'winner_query_error_count': winner_query_error_count,
    }


def print_summary(result_df, question_summary_df, ensemble_method_results: dict = None, tie_break_stats_per_method: dict = None, final_winner_results_per_method: dict = None):
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
    
    # Ensemble tie-break and finalist statistics per method (if provided)
    if tie_break_stats_per_method:
        try:
            print(f"\nENSEMBLE TIE-BREAK STATS PER METHOD:")
            for method, stats in tie_break_stats_per_method.items():
                total_questions = stats.get('total_questions', 0)
                tie_questions = stats.get('tie_questions', 0)
                single_finalist_questions = stats.get('single_finalist_questions', 0)
                single_match_count = stats.get('single_match_count', 0)
                tie_match_count = stats.get('tie_match_count', 0)
                considered_questions = stats.get('considered_questions', 0)

                tie_percent = (tie_questions / total_questions * 100) if total_questions > 0 else 0.0
                single_match_pct = (single_match_count / single_finalist_questions * 100) if single_finalist_questions > 0 else 0.0
                tie_match_pct = (tie_match_count / tie_questions * 100) if tie_questions > 0 else 0.0
                print(f"  {method}:")
                print(f"    Questions with multiple finalists (tie): {tie_questions}/{total_questions} ({tie_percent:.1f}%)")
                print(f"    Match rate where only one finalist: {single_match_count}/{single_finalist_questions} ({single_match_pct:.1f}%)")
                # Reflect selected tie-breaker in label
                tb_label = method.split('|tb:')[-1] if '|tb:' in method else 'random'
                print(f"    Match rate where multiple finalists ({tb_label} tie-break): {tie_match_count}/{tie_questions} ({tie_match_pct:.1f}%)")
        except Exception as e:
            print(f"\n[WARNING] Failed to compute per-method tie-break statistics: {e}")

    # Final ensemble per-method results using winners' eval_result across all questions
    if final_winner_results_per_method:
        try:
            print(f"\nFINAL ENSEMBLE PER-METHOD RESULTS:")
            for method, metrics in final_winner_results_per_method.items():
                total_q = metrics.get('total_questions', 0)
                m_cnt = metrics.get('winner_match_count', 0)
                nm_cnt = metrics.get('winner_no_match_count', 0)
                qe_cnt = metrics.get('winner_query_error_count_adjusted', 0)
                m_pct = (m_cnt / total_q * 100.0) if total_q > 0 else 0.0
                nm_pct = (nm_cnt / total_q * 100.0) if total_q > 0 else 0.0
                qe_pct = (qe_cnt / total_q * 100.0) if total_q > 0 else 0.0
                print(f"  {method}:")
                print(f"    Match: {m_cnt}/{total_q} ({m_pct:.1f}%)")
                print(f"    No Match: {nm_cnt}/{total_q} ({nm_pct:.1f}%)")
                print(f"    Query Error: {qe_cnt}/{total_q} ({qe_pct:.1f}%)")
        except Exception as e:
            print(f"\n[WARNING] Failed to print final ensemble per-method results: {e}")

    # Per-method ensemble results using ALL QUESTIONS as denominator (if provided)
    if ensemble_method_results:
        try:
            print(f"\nENSEMBLE METHOD RESULTS (All questions as denominator):")
            for method, metrics in ensemble_method_results.items():
                total_q = metrics.get('total_questions', 0)
                m_cnt = metrics.get('match_count', 0)
                nm_cnt = metrics.get('no_match_count', 0)
                qe_cnt = metrics.get('query_error_count', 0)
                m_pct = metrics.get('match_pct_all', 0.0)
                nm_pct = metrics.get('no_match_pct_all', 0.0)
                qe_pct = metrics.get('query_error_pct_all', 0.0)
                print(f"  {method}:")
                print(f"    Match: {m_cnt}/{total_q} ({m_pct:.1f}%)")
                print(f"    No Match: {nm_cnt}/{total_q} ({nm_pct:.1f}%)")
                print(f"    Query Error: {qe_cnt}/{total_q} ({qe_pct:.1f}%)")
        except Exception as e:
            print(f"\n[WARNING] Failed to print ensemble method comparison: {e}")

    print("\n" + "="*80)

def _log_mlflow_stats(args,
                      result_df: pd.DataFrame,
                      question_summary_df: pd.DataFrame,
                      tie_break_stats_per_method: dict = None,
                      final_winner_results_per_method: dict = None):
    """Log Overall, Question-level, Tie-break and Final ensemble results into MLflow."""
    if getattr(args, 'disable_mlflow', False):
        return
    if mlflow is None:
        logger.warning("MLflow not available; skipping MLflow logging.")
        return

    try:
        def _sanitize_mlflow_name(name: str) -> str:
            # Replace disallowed '|' with ':' and any other invalid chars with '_'
            name = name.replace('|', ':')
            return re.sub(r'[^A-Za-z0-9_.:\-\/ ]', '_', name)
        # Load credentials from ~/.env if available (align with prompt_evaluation)
        if load_dotenv is not None:
            try:
                env_path = Path.home() / ".env"
                load_dotenv(dotenv_path=env_path)
                logger.info(f"Loaded MLflow credentials from {env_path}")
            except Exception:
                pass

        # Allow token override via CLI argument
        if getattr(args, 'mlflow_token', None):
            os.environ['MLFLOW_TRACKING_TOKEN'] = str(args.mlflow_token)

        # Optional setup
        if getattr(args, 'mlflow_uri', None):
            mlflow.set_tracking_uri(args.mlflow_uri)
        if getattr(args, 'mlflow_experiment', None):
            mlflow.set_experiment(args.mlflow_experiment)

        started_here = False
        if mlflow.active_run() is None:
            run_name = getattr(args, 'mlflow_run_name', None) or 'evaluate_all_runs'
            mlflow.start_run(run_name=run_name)
            started_here = True

        # Overall results
        total_runs = len(result_df)
        comparison_counts = result_df['comparison_result'].value_counts()
        total_percentages = (comparison_counts / total_runs * 100).round(2)
        mlflow.log_metric('overall_total_runs', int(total_runs))
        for result_type, count in comparison_counts.items():
            mlflow.log_metric(f'overall_count_{str(result_type).replace(" ", "_")}', int(count))
            pct_val = float(total_percentages[result_type]) if result_type in total_percentages else 0.0
            mlflow.log_metric(f'overall_pct_{str(result_type).replace(" ", "_")}', pct_val)

        # Question-level results
        total_questions = len(question_summary_df)
        questions_with_match = int(question_summary_df['has_match'].sum())
        questions_without_match = int(total_questions - questions_with_match)
        pct_with_match = (questions_with_match / total_questions * 100.0) if total_questions > 0 else 0.0
        pct_without_match = (questions_without_match / total_questions * 100.0) if total_questions > 0 else 0.0
        mlflow.log_metric('questions_total', int(total_questions))
        mlflow.log_metric('questions_with_match', int(questions_with_match))
        mlflow.log_metric('questions_without_match', int(questions_without_match))
        mlflow.log_metric('questions_with_match_pct', float(pct_with_match))
        mlflow.log_metric('questions_without_match_pct', float(pct_without_match))

        # Tie-break stats per-method
        if tie_break_stats_per_method:
            for key, stats in tie_break_stats_per_method.items():
                prefix = _sanitize_mlflow_name(f'tb__{key}')
                for metric_name in [
                    'total_questions', 'tie_questions', 'single_finalist_questions', 'single_match_count',
                    'tie_match_count', 'considered_questions', 'winner_match_count', 'winner_no_match_count',
                    'winner_query_error_count']:
                    value = stats.get(metric_name)
                    if value is not None:
                        mlflow.log_metric(f'{prefix}__{metric_name}', float(value))

        # Final ensemble per-method results
        if final_winner_results_per_method:
            for key, metrics in final_winner_results_per_method.items():
                prefix = _sanitize_mlflow_name(f'final__{key}')
                total_q = int(metrics.get('total_questions', 0))
                m_cnt = int(metrics.get('winner_match_count', 0))
                nm_cnt = int(metrics.get('winner_no_match_count', 0))
                qe_cnt = int(metrics.get('winner_query_error_count_adjusted', 0))
                m_pct = (m_cnt / total_q * 100.0) if total_q > 0 else 0.0
                nm_pct = (nm_cnt / total_q * 100.0) if total_q > 0 else 0.0
                qe_pct = (qe_cnt / total_q * 100.0) if total_q > 0 else 0.0
                mlflow.log_metric(f'{prefix}__total_questions', total_q)
                mlflow.log_metric(f'{prefix}__winner_match_count', m_cnt)
                mlflow.log_metric(f'{prefix}__winner_no_match_count', nm_cnt)
                mlflow.log_metric(f'{prefix}__winner_query_error_count', qe_cnt)
                mlflow.log_metric(f'{prefix}__winner_match_pct', float(m_pct))
                mlflow.log_metric(f'{prefix}__winner_no_match_pct', float(nm_pct))
                mlflow.log_metric(f'{prefix}__winner_query_error_pct', float(qe_pct))

        # Best_(statistic) logs using final winner results (match criterion)
        if final_winner_results_per_method:
            try:
                best_key = None
                best_match_pct = -1.0
                per_key_percentages = {}
                for key, metrics in final_winner_results_per_method.items():
                    total_q = int(metrics.get('total_questions', 0))
                    m_cnt = int(metrics.get('winner_match_count', 0))
                    nm_cnt = int(metrics.get('winner_no_match_count', 0))
                    qe_cnt = int(metrics.get('winner_query_error_count_adjusted', 0))
                    if total_q > 0:
                        match_pct = (m_cnt / total_q) * 100.0
                        no_match_pct = (nm_cnt / total_q) * 100.0
                        query_error_pct = (qe_cnt / total_q) * 100.0
                    else:
                        match_pct = 0.0
                        no_match_pct = 0.0
                        query_error_pct = 0.0
                    per_key_percentages[key] = (match_pct, no_match_pct, query_error_pct)
                    if match_pct > best_match_pct:
                        best_match_pct = match_pct
                        best_key = key

                if best_key is not None:
                    # Store pairing name as a parameter (string) and percentages as metrics
                    mlflow.log_param('Best_Ensemble_Pairing', _sanitize_mlflow_name(str(best_key)))
                    m_pct, nm_pct, qe_pct = per_key_percentages[best_key]
                    mlflow.log_metric('Best_Match', float(m_pct))
                    mlflow.log_metric('Best_No_Match', float(nm_pct))
                    mlflow.log_metric('Best_Query_Error', float(qe_pct))
            except Exception:
                # Non-fatal; continue without best-of logs
                pass

        if started_here:
            mlflow.end_run()
    except Exception as e:
        logger.warning(f"Failed to log MLflow metrics: {e}")

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
        '--num-threads', '--num_threads',
        type=int,
        default=None,
        help='Number of worker threads to use for parallel evaluation (default: CPU count)'
    )
    parser.add_argument(
        '--ensemble-selection-method', '--ensemble_selection_method',
        choices=['size', 'frequency', 'random', 'density', 'agent_indiv_grade'],
        default='size',
        help='[DEPRECATED] Use --ensemble-methods instead to specify one or more methods'
    )
    parser.add_argument(
        '--ensemble-methods', '--ensemble_methods',
        nargs='*',
        help='List of ensemble selection methods to run and summarize (e.g., size frequency density or "size,frequency,density")'
    )
    parser.add_argument(
        '--tie-breakers', '--tie_breakers',
        nargs='*',
        help='List of tie-breaker methods to run for finalists (random, density, size). Default: random'
    )
    parser.add_argument(
        '--use-eval-result-only', '--use_eval_result_only',
        action='store_true',
        help='Use the eval_result column from the CSV instead of executing code'
    )
    parser.add_argument(
        '--eval-column', '--eval_column',
        default='eval_result',
        help='Name of the column to use when --use-eval-result-only is enabled (default: eval_result)'
    )

    # MLflow options
    parser.add_argument(
        '--mlflow-uri', '--mlflow_uri',
        help='Override MLflow tracking URI (e.g., file:./mlruns)'
    )
    parser.add_argument(
        '--mlflow-experiment', '--mlflow_experiment',
        help='MLflow experiment name to log metrics under'
    )
    parser.add_argument(
        '--mlflow-run-name', '--mlflow_run_name',
        help='MLflow run name to use when starting a run'
    )
    parser.add_argument(
        '--mlflow-token', '--mlflow_token',
        help='MLflow tracking token to authenticate API requests'
    )
    parser.add_argument(
        '--disable-mlflow', '--disable_mlflow',
        action='store_true',
        help='Skip MLflow logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input file
    if not os.path.exists(args.all_runs):
        logger.error(f"All runs file not found: {args.all_runs}")
        sys.exit(1)
    
    # Validate paths only when executing code
    if not args.use_eval_result_only:
        if not os.path.exists(args.db_base_path):
            logger.error(f"Database base path not found: {args.db_base_path}")
            sys.exit(1)
        if not os.path.exists(args.metadata_base_path):
            logger.error(f"Metadata base path not found: {args.metadata_base_path}")
            sys.exit(1)
    
    try:
        # Run evaluation
        if args.use_eval_result_only:
            logger.info("Starting evaluation (using eval_result only, no code execution)...")
            result_df, question_summary_df = evaluate_from_eval_column(
                args.all_runs,
                args.output_dir,
                eval_column=args.eval_column,
            )
        else:
            logger.info("Starting evaluation (executing code)...")
            result_df, question_summary_df = evaluate_all_runs(
                args.all_runs,
                args.db_base_path,
                args.metadata_base_path,
                args.output_dir,
                num_threads=args.num_threads
            )

        # Optional: compute ensemble winners per requested methods and evaluate Match/No Match percentages
        # Determine which ensemble methods to run; prefer --ensemble-methods, fallback to deprecated flag
        def _normalize_methods(methods_raw):
            allowed = ['size', 'frequency', 'random', 'density', 'agent_indiv_grade']
            if not methods_raw:
                return []
            # Flatten and split on commas; lowercase and strip
            tokens = []
            for item in methods_raw:
                if isinstance(item, str):
                    parts = [p.strip().lower() for p in item.replace(';', ',').split(',') if p.strip()]
                    if parts:
                        tokens.extend(parts)
                else:
                    try:
                        tokens.append(str(item).strip().lower())
                    except Exception:
                        pass
            # Filter to allowed and de-duplicate preserving order
            seen = set()
            normalized = []
            for t in tokens:
                if t in allowed and t not in seen:
                    seen.add(t)
                    normalized.append(t)
                elif t not in allowed:
                    logger.warning(f"Skipping unknown ensemble method: {t}")
            return normalized

        methods_to_use = _normalize_methods(args.ensemble_methods) if args.ensemble_methods and len(args.ensemble_methods) > 0 else _normalize_methods([args.ensemble_selection_method])
        def _normalize_tie_breakers(tb_raw):
            allowed_tb = ['random', 'density', 'size']
            if not tb_raw:
                return ['random']
            tokens = []
            for item in tb_raw:
                if isinstance(item, str):
                    parts = [p.strip().lower() for p in item.replace(';', ',').split(',') if p.strip()]
                    if parts:
                        tokens.extend(parts)
                else:
                    try:
                        tokens.append(str(item).strip().lower())
                    except Exception:
                        pass
            seen = set()
            normalized = []
            for t in tokens:
                if t in allowed_tb and t not in seen:
                    seen.add(t)
                    normalized.append(t)
                elif t not in allowed_tb:
                    logger.warning(f"Skipping unknown tie-breaker: {t}")
            return normalized if normalized else ['random']

        tie_breakers_to_use = _normalize_tie_breakers(args.tie_breakers)
        if methods_to_use:
            logger.info(f"Ensemble methods selected: {methods_to_use}")
        else:
            logger.info("No valid ensemble methods provided; skipping ensemble comparison.")

        ensemble_method_results = None
        if (methods_to_use and len(methods_to_use) > 0) and (not args.use_eval_result_only):
            # Prepare winners per method using all_runs DataFrame
            try:
                all_runs_df = pd.read_csv(args.all_runs)
            except Exception as e:
                logger.error(f"Failed to reload all_runs file for ensemble methods: {e}")
                all_runs_df = None

            if all_runs_df is not None:
                # Ensure extracted code is present if needed downstream
                if 'extracted_python_code' not in all_runs_df.columns and 'code' in all_runs_df.columns:
                    all_runs_df['extracted_python_code'] = all_runs_df['code']

                ensemble_method_results = {}
                for method in methods_to_use:
                    try:
                        winners_df = ensemble_from_all_runs_df(
                            all_runs_df,
                            ensemble_selection_method=method,
                            use_gradio_agent=False,
                            mlflow_run_id=None,
                        )
                        # Evaluate winners_df similarly to compare_output's per-row logic
                        # Build a minimal df with columns expected by process_row
                        winners_eval_df = winners_df.copy()
                        if 'extracted_python_code' not in winners_eval_df.columns:
                            winners_eval_df['extracted_python_code'] = winners_eval_df.get('response')

                        # Process each winner row
                        total_questions = len(question_summary_df)
                        match_count = 0
                        no_match_count = 0
                        qe_count_measured = 0
                        total_rows = len(winners_eval_df)
                        for _, row in winners_eval_df.iterrows():
                            try:
                                res, exc = process_row(row, args.db_base_path, args.metadata_base_path)
                            except Exception:
                                res = 'Error'
                            outcome = str(res).strip()
                            if outcome == 'Match':
                                match_count += 1
                            elif outcome == 'No Match':
                                no_match_count += 1
                            else:
                                qe_count_measured += 1

                        # Treat any missing winners as Query Error to keep denominator as all questions
                        missing_questions = max(0, total_questions - total_rows)
                        query_error_count = qe_count_measured + missing_questions
                        match_pct_all = (match_count / total_questions * 100.0) if total_questions > 0 else 0.0
                        no_match_pct_all = (no_match_count / total_questions * 100.0) if total_questions > 0 else 0.0
                        query_error_pct_all = (query_error_count / total_questions * 100.0) if total_questions > 0 else 0.0
                        ensemble_method_results[method] = {
                            'match_count': match_count,
                            'no_match_count': no_match_count,
                            'query_error_count': query_error_count,
                            'total_questions': total_questions,
                            'match_pct_all': match_pct_all,
                            'no_match_pct_all': no_match_pct_all,
                            'query_error_pct_all': query_error_pct_all,
                        }
                    except Exception as e:
                        logger.warning(f"Failed computing ensemble winners for method {method}: {e}")

        # Compute tie-break/finalist stats per method using the same list
        tie_break_stats_per_method = {}
        for method in methods_to_use:
            for tb in tie_breakers_to_use:
                key = f"{method}|tb:{tb}"
                try:
                    tie_break_stats_per_method[key] = _compute_ensemble_stats(result_df, method, tie_breaker=tb)
                except Exception as e:
                    logger.warning(f"Failed computing tie-break stats for method {method} with tie-breaker {tb}: {e}")

        # Build final per-method winner outcome results using tie_break_stats (winners across questions considered)
        final_winner_results_per_method = {}
        try:
            for key, stats in tie_break_stats_per_method.items():
                total_questions = stats.get('total_questions', 0)
                considered_questions = stats.get('considered_questions', 0)
                w_match = stats.get('winner_match_count', 0)
                w_nomatch = stats.get('winner_no_match_count', 0)
                w_qerr = stats.get('winner_query_error_count', 0)
                # Adjust query error count to reflect all questions as denominator
                missing = max(0, total_questions - considered_questions)
                w_qerr_adjusted = w_qerr + missing
                final_winner_results_per_method[key] = {
                    'total_questions': total_questions,
                    'winner_match_count': w_match,
                    'winner_no_match_count': w_nomatch,
                    'winner_query_error_count_adjusted': w_qerr_adjusted,
                }
        except Exception as e:
            logger.warning(f"Failed building final per-method winner results: {e}")

        # Print summary
        print_summary(
            result_df,
            question_summary_df,
            ensemble_method_results=ensemble_method_results,
            tie_break_stats_per_method=tie_break_stats_per_method,
            final_winner_results_per_method=final_winner_results_per_method,
        )

        # Log stats to MLflow
        _log_mlflow_stats(
            args,
            result_df,
            question_summary_df,
            tie_break_stats_per_method=tie_break_stats_per_method,
            final_winner_results_per_method=final_winner_results_per_method,
        )
        
        logger.info("Evaluation completed successfully!")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
