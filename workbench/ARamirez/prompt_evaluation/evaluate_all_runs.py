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
from test_data.eval import process_row, symetric_compare_df
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
    Build result_df and question_summary_df using an existing eval column without executing code.

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
    # Strictly use the provided eval_column for normalization
    result_df['comparison_result'] = result_df[eval_column].map(_normalize_eval_result_to_comparison)
    # Keep an exception column for schema parity; not applicable in eval-only
    result_df['exception'] = None

    question_summary_df = create_question_summary(result_df, comparison_col='comparison_result')

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
        """Process a single row and return evaluation results (custom and bird)."""
        try:
            custom_result, custom_exception, bird_result, bird_exception = process_row(
                row, db_base_path, metadata_base_path
            )
            return (custom_result, custom_exception, bird_result, bird_exception)
        except Exception as e:
            logger.error(f"Error processing row {row.name}: {e}")
            # Preserve shapes: return 4-tuple
            return ('Error', str(e), 'Not Available', str(e))
    
    # Determine workers
    if num_threads is None or num_threads <= 0:
        num_threads = os.cpu_count() or 4

    logger.info(f"Processing {len(df)} rows with {num_threads} threads ...")

    # Create a generator to avoid duplicating rows in memory
    rows_iterable = (row for _, row in df.iterrows())

    # Process rows in parallel with progress bar, accumulating minimal results
    custom_eval_results = []
    custom_eval_exceptions = []
    bird_eval_results = []
    bird_eval_exceptions = []
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results_iter = executor.map(process_single_row, rows_iterable)
        for c_res, c_exc, b_res, b_exc in tqdm(results_iter, total=len(df), desc="Evaluating"):
            custom_eval_results.append(c_res)
            custom_eval_exceptions.append(c_exc)
            bird_eval_results.append(b_res)
            bird_eval_exceptions.append(b_exc)
    
    # Merge with original data - OUTPUT 1: Identical CSV with extra column
    result_df = df.copy()
    # Store both evaluation tracks
    result_df['custom_eval'] = custom_eval_results
    result_df['custom_eval_exception'] = custom_eval_exceptions
    result_df['bird_eval'] = bird_eval_results
    result_df['bird_eval_exception'] = bird_eval_exceptions
    # Backward-compatible columns
    result_df['comparison_result'] = result_df['custom_eval'].map(_normalize_eval_result_to_comparison)
    result_df['exception'] = result_df['custom_eval_exception']
    # Normalized bird comparison column
    try:
        result_df['bird_comparison_result'] = result_df['bird_eval'].map(_normalize_eval_result_to_comparison)
    except Exception:
        result_df['bird_comparison_result'] = None

    # If input CSV already contains eval_bird (from eval_all_runs_to_csv), prefer it to correct/override
    # runtime BIRD results that are missing or classified as 'Query Error'. This ensures CSV-provided
    # BIRD-only labels (Match/No Match/Query Error) are respected in the final summary.
    try:
        if 'eval_bird' in df.columns:
            mapped_bird = df['eval_bird'].map(_normalize_eval_result_to_comparison)
            if 'bird_comparison_result' in result_df.columns:
                # Override where runtime value is NaN or 'Query Error' but CSV provides a concrete label
                mask_available = mapped_bird.notna()
                mask_runtime_bad = result_df['bird_comparison_result'].isna() | (result_df['bird_comparison_result'] == 'Query Error')
                mask = mask_available & mask_runtime_bad
                if mask.any():
                    result_df.loc[mask, 'bird_comparison_result'] = mapped_bird.loc[mask]
            else:
                result_df['bird_comparison_result'] = mapped_bird
    except Exception:
        pass
    
    # Create question summaries (custom) - OUTPUT 2: Unique question IDs with has_match column
    question_summary_df = create_question_summary(result_df, comparison_col='comparison_result')
    
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
            'custom_eval': result_df['custom_eval'],
            'custom_eval_exception': result_df['custom_eval_exception'],
            'bird_eval': result_df['bird_eval'],
            'bird_eval_exception': result_df['bird_eval_exception'],
            'comparison_result': result_df['comparison_result'],
            'exception': result_df['exception'],
        })
        evaluation_details_df.to_csv(eval_output_file, index=False)
        logger.info(f"Saved evaluation details to: {eval_output_file}")
    
    return result_df, question_summary_df

def create_question_summary(df, comparison_col: str = 'comparison_result'):
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
    agg_dict = {
        'question': 'first',
        'db_name': 'first', 
        'dataset_name': 'first',
        'comparison_result': lambda x: 'Match' if 'Match' in x.values else 'No Match'
    }
    # Carry complexity/difficulty if present
    if 'complexity' in df.columns:
        agg_dict['complexity'] = 'first'
    if 'difficulty' in df.columns:
        agg_dict['difficulty'] = 'first'

    # Use provided comparison column for aggregation by temporarily aligning name
    tmp = df.copy()
    if comparison_col != 'comparison_result' and comparison_col in tmp.columns:
        tmp = tmp.rename(columns={comparison_col: 'comparison_result'})
    question_groups = tmp.groupby('question_id').agg(agg_dict).reset_index()
    
    # Create the has_match column
    question_groups['has_match'] = question_groups['comparison_result'] == 'Match'
    
    # Reorder columns for better readability
    base_cols = ['question_id', 'question', 'db_name', 'dataset_name', 'comparison_result', 'has_match']
    # Insert optional columns in a stable order if present
    if 'complexity' in question_groups.columns:
        base_cols.insert(4, 'complexity')
    if 'difficulty' in question_groups.columns:
        # After complexity if both exist, otherwise before comparison_result
        insert_pos = 5 if 'complexity' in question_groups.columns else 4
        base_cols.insert(insert_pos, 'difficulty')
    question_summary = question_groups[base_cols]
    
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


def _compute_ensemble_stats(result_df: pd.DataFrame, selection_method: str, tie_breaker: str = 'random', comparison_col: str = 'comparison_result'):
    """
    Compute tie-break and finalist statistics using ensemble logic criteria.
    Returns a dict with keys: total_questions, tie_questions, single_finalist_questions,
    single_match_count, tie_match_count.
    """
    tmp_df = result_df.copy()
    # Align the comparison column name
    if comparison_col != 'comparison_result' and comparison_col in tmp_df.columns:
        tmp_df = tmp_df.rename(columns={comparison_col: 'comparison_result'})
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

    # Optional breakdowns by complexity and difficulty if columns exist
    has_complexity = 'complexity' in tmp_df.columns
    has_difficulty = 'difficulty' in tmp_df.columns

    def _new_stats_dict():
        return {
            'total_questions': 0,
            'tie_questions': 0,
            'single_finalist_questions': 0,
            'single_match_count': 0,
            'tie_match_count': 0,
            'considered_questions': 0,
            'winner_match_count': 0,
            'winner_no_match_count': 0,
            'winner_query_error_count': 0,
        }

    by_complexity = {}
    by_difficulty = {}

    def _safe_label(val):
        try:
            if pd.isna(val):
                return 'Unknown'
        except Exception:
            pass
        text = str(val).strip()
        return text if text else 'Unknown'

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
        elif selection_method == 'reverse_size':
            sizes = {}
            for i in valid_indices:
                try:
                    sizes[i] = runs[i]['df'].size
                except Exception:
                    sizes[i] = -1
            if not sizes:
                continue
            valid_sizes = [s for s in sizes.values() if s > -1]
            if len(valid_sizes) == 0:
                continue
            min_size = min(valid_sizes)
            candidates = [i for i, s in sizes.items() if s == min_size]
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
        elif selection_method == 'reverse_density':
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
            valid_densities = [d for d in densities.values() if d > -1]
            if len(valid_densities) == 0:
                continue
            min_density = min(valid_densities)
            candidates = [i for i, d in densities.items() if d == min_density]
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
        elif selection_method == 'reverse_frequency':
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
            min_votes = min(consensus.values())
            candidates = [i for i, v in consensus.items() if v == min_votes]
        elif selection_method == 'random':
            candidates = valid_indices.copy()
        elif selection_method == 'agent_indiv_grade':
            # Stats-only path: treat as having all valid candidates; tie-breaker decides winner
            candidates = valid_indices.copy()
        elif selection_method == 'binary_comp_selection':
            # Stats-only path for binary LLM comp: consider all valid as finalists
            candidates = valid_indices.copy()
        elif selection_method == 'double_elim':
            # Stats-only path for double elimination. With n=1 there must be a single finalist,
            # so pick one deterministically using the seeded RNG.
            if valid_indices:
                chosen = selection_random_tie_break(valid_indices, question_idx='?')
                if chosen is None:
                    chosen = rng_local.choice(valid_indices)
                candidates = [chosen]
            else:
                candidates = []
        
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

        # Determine breakdown buckets for this question
        comp_label = _safe_label(group['complexity'].iloc[0]) if has_complexity else None
        diff_label = _safe_label(group['difficulty'].iloc[0]) if has_difficulty else None
        comp_stats = by_complexity.setdefault(comp_label, _new_stats_dict()) if has_complexity else None
        diff_stats = by_difficulty.setdefault(diff_label, _new_stats_dict()) if has_difficulty else None

        # Increment per-bucket total questions
        if comp_stats is not None:
            comp_stats['total_questions'] += 1
        if diff_stats is not None:
            diff_stats['total_questions'] += 1

        if len(candidates) == 1:
            single_finalist_questions += 1
            winner_i = candidates[0]
            winner_row_idx = runs[winner_i]['row_index']
            if str(group.loc[winner_row_idx, 'comparison_result']).strip() == 'Match':
                single_match_count += 1
            # Per-bucket single finalist counters
            if comp_stats is not None:
                comp_stats['single_finalist_questions'] += 1
                if str(group.loc[winner_row_idx, 'comparison_result']).strip() == 'Match':
                    comp_stats['single_match_count'] += 1
            if diff_stats is not None:
                diff_stats['single_finalist_questions'] += 1
                if str(group.loc[winner_row_idx, 'comparison_result']).strip() == 'Match':
                    diff_stats['single_match_count'] += 1
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
            # Per-bucket tie finalist counters
            if comp_stats is not None:
                comp_stats['tie_questions'] += 1
                if str(group.loc[winner_row_idx, 'comparison_result']).strip() == 'Match':
                    comp_stats['tie_match_count'] += 1
            if diff_stats is not None:
                diff_stats['tie_questions'] += 1
                if str(group.loc[winner_row_idx, 'comparison_result']).strip() == 'Match':
                    diff_stats['tie_match_count'] += 1

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
            # Per-bucket winner outcomes
            if comp_stats is not None:
                comp_stats['considered_questions'] += 1
                if outcome == 'Match':
                    comp_stats['winner_match_count'] += 1
                elif outcome == 'No Match':
                    comp_stats['winner_no_match_count'] += 1
                else:
                    comp_stats['winner_query_error_count'] += 1
            if diff_stats is not None:
                diff_stats['considered_questions'] += 1
                if outcome == 'Match':
                    diff_stats['winner_match_count'] += 1
                elif outcome == 'No Match':
                    diff_stats['winner_no_match_count'] += 1
                else:
                    diff_stats['winner_query_error_count'] += 1
        except Exception:
            # If any lookup fails, count as query error for robustness
            considered_questions += 1
            winner_query_error_count += 1
            if comp_stats is not None:
                comp_stats['considered_questions'] += 1
                comp_stats['winner_query_error_count'] += 1
            if diff_stats is not None:
                diff_stats['considered_questions'] += 1
                diff_stats['winner_query_error_count'] += 1

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
        'by_complexity': by_complexity if has_complexity else None,
        'by_difficulty': by_difficulty if has_difficulty else None,
    }


def _print_ensemble_tie_break_stats(tie_break_stats_per_method: dict, section_name: str = ""):
    """Helper function to print ensemble tie-break statistics."""
    if not tie_break_stats_per_method:
        return
    
    try:
        section_label = f" ({section_name})" if section_name else ""
        print(f"\nENSEMBLE TIE-BREAK STATS PER METHOD{section_label}:")
        for method, stats in tie_break_stats_per_method.items():
                total_questions = stats.get('total_questions', 0)
                tie_questions = stats.get('tie_questions', 0)
                single_finalist_questions = stats.get('single_finalist_questions', 0)
                single_match_count = stats.get('single_match_count', 0)
                tie_match_count = stats.get('tie_match_count', 0)

                tie_percent = (tie_questions / total_questions * 100) if total_questions > 0 else 0.0
                single_match_pct = (single_match_count / single_finalist_questions * 100) if single_finalist_questions > 0 else 0.0
                tie_match_pct = (tie_match_count / tie_questions * 100) if tie_questions > 0 else 0.0
                print(f"  {method}:")
                print(f"    Questions with multiple finalists (tie): {tie_questions}/{total_questions} ({tie_percent:.1f}%)")
                print(f"    Match rate where only one finalist: {single_match_count}/{single_finalist_questions} ({single_match_pct:.1f}%)")
                # Reflect selected tie-breaker in label
                tb_label = method.split('|tb:')[-1] if '|tb:' in method else 'random'
                print(f"    Match rate where multiple finalists ({tb_label} tie-break): {tie_match_count}/{tie_questions} ({tie_match_pct:.1f}%)")

                # Per-complexity and per-difficulty breakdowns for this pairing
                try:
                    by_comp = stats.get('by_complexity')
                    if by_comp:
                        print(f"    By complexity:")
                        for label, comp_stats in by_comp.items():
                            tq = comp_stats.get('total_questions', 0)
                            tie_q = comp_stats.get('tie_questions', 0)
                            sfq = comp_stats.get('single_finalist_questions', 0)
                            sm = comp_stats.get('single_match_count', 0)
                            tm = comp_stats.get('tie_match_count', 0)
                            tie_pct_c = (tie_q / tq * 100.0) if tq > 0 else 0.0
                            sm_pct_c = (sm / sfq * 100.0) if sfq > 0 else 0.0
                            tm_pct_c = (tm / tie_q * 100.0) if tie_q > 0 else 0.0
                            safe_label = str(label) if str(label).strip() else 'Unknown'
                            print(f"      {safe_label}: ties {tie_q}/{tq} ({tie_pct_c:.1f}%), single-finalist match {sm}/{sfq} ({sm_pct_c:.1f}%), tie match {tm}/{tie_q} ({tm_pct_c:.1f}%)")
                        # Winner outcome breakdowns by complexity
                        print(f"    Final winner outcomes by complexity:")
                        for label, comp_stats in by_comp.items():
                            cq = comp_stats.get('considered_questions', 0)
                            wm = comp_stats.get('winner_match_count', 0)
                            wnm = comp_stats.get('winner_no_match_count', 0)
                            wqe = comp_stats.get('winner_query_error_count', 0)
                            wm_pct = (wm / cq * 100.0) if cq > 0 else 0.0
                            wnm_pct = (wnm / cq * 100.0) if cq > 0 else 0.0
                            wqe_pct = (wqe / cq * 100.0) if cq > 0 else 0.0
                            safe_label = str(label) if str(label).strip() else 'Unknown'
                            print(f"      {safe_label}: Match {wm}/{cq} ({wm_pct:.1f}%), No Match {wnm}/{cq} ({wnm_pct:.1f}%), Query Error {wqe}/{cq} ({wqe_pct:.1f}%)")
                    by_diff = stats.get('by_difficulty')
                    if by_diff:
                        print(f"    By difficulty:")
                        for label, diff_stats in by_diff.items():
                            tq = diff_stats.get('total_questions', 0)
                            tie_q = diff_stats.get('tie_questions', 0)
                            sfq = diff_stats.get('single_finalist_questions', 0)
                            sm = diff_stats.get('single_match_count', 0)
                            tm = diff_stats.get('tie_match_count', 0)
                            tie_pct_d = (tie_q / tq * 100.0) if tq > 0 else 0.0
                            sm_pct_d = (sm / sfq * 100.0) if sfq > 0 else 0.0
                            tm_pct_d = (tm / tie_q * 100.0) if tie_q > 0 else 0.0
                            safe_label = str(label) if str(label).strip() else 'Unknown'
                            print(f"      {safe_label}: ties {tie_q}/{tq} ({tie_pct_d:.1f}%), single-finalist match {sm}/{sfq} ({sm_pct_d:.1f}%), tie match {tm}/{tie_q} ({tm_pct_d:.1f}%)")
                        # Winner outcome breakdowns by difficulty
                        print(f"    Final winner outcomes by difficulty:")
                        for label, diff_stats in by_diff.items():
                            cq = diff_stats.get('considered_questions', 0)
                            wm = diff_stats.get('winner_match_count', 0)
                            wnm = diff_stats.get('winner_no_match_count', 0)
                            wqe = diff_stats.get('winner_query_error_count', 0)
                            wm_pct = (wm / cq * 100.0) if cq > 0 else 0.0
                            wnm_pct = (wnm / cq * 100.0) if cq > 0 else 0.0
                            wqe_pct = (wqe / cq * 100.0) if cq > 0 else 0.0
                            safe_label = str(label) if str(label).strip() else 'Unknown'
                            print(f"      {safe_label}: Match {wm}/{cq} ({wm_pct:.1f}%), No Match {wnm}/{cq} ({wnm_pct:.1f}%), Query Error {wqe}/{cq} ({wqe_pct:.1f}%)")
                except Exception as e:
                    print(f"    [WARNING] Failed pairing breakdowns: {e}")
    except Exception as e:
            section_suffix = f" ({section_name})" if section_name else ""
            print(f"\n[WARNING] Failed to compute per-method tie-break{section_suffix}: {e}")


def _print_final_ensemble_results(final_winner_results_per_method: dict, section_name: str = ""):
    """Helper function to print final ensemble per-method results."""
    if not final_winner_results_per_method:
        return
    
    try:
        section_label = f" ({section_name})" if section_name else ""
        print(f"\nFINAL ENSEMBLE PER-METHOD RESULTS{section_label}:")
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
        section_suffix = f" ({section_name})" if section_name else ""
        print(f"\n[WARNING] Failed to print final ensemble per-method results{section_suffix}: {e}")


def print_summary(result_df,
                  question_summary_df,
                  tie_break_stats_per_method: dict = None,
                  final_winner_results_per_method: dict = None,
                  bird_question_summary_df: pd.DataFrame = None,
                  bird_tie_break_stats_per_method: dict = None,
                  bird_final_winner_results_per_method: dict = None):
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

    # Question-level breakdowns by complexity/difficulty when present
    try:
        if 'complexity' in question_summary_df.columns:
            by_comp = question_summary_df.groupby('complexity')['has_match'].agg(['sum', 'count']).reset_index()
            print(f"\nBY COMPLEXITY (question-level has_match):")
            for _, row in by_comp.iterrows():
                label = str(row['complexity']) if str(row['complexity']).strip() else 'Unknown'
                total = int(row['count'])
                matches = int(row['sum'])
                pct = (matches / total * 100.0) if total > 0 else 0.0
                print(f"  {label}: {matches}/{total} ({pct:.1f}%)")
        if 'difficulty' in question_summary_df.columns:
            by_diff = question_summary_df.groupby('difficulty')['has_match'].agg(['sum', 'count']).reset_index()
            print(f"\nBY DIFFICULTY (question-level has_match):")
            for _, row in by_diff.iterrows():
                label = str(row['difficulty']) if str(row['difficulty']).strip() else 'Unknown'
                total = int(row['count'])
                matches = int(row['sum'])
                pct = (matches / total * 100.0) if total > 0 else 0.0
                print(f"  {label}: {matches}/{total} ({pct:.1f}%)")
    except Exception as e:
        print(f"\n[WARNING] Failed to compute complexity/difficulty breakdowns: {e}")
    
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
    _print_ensemble_tie_break_stats(tie_break_stats_per_method)

    # Final ensemble per-method results using winners' eval_result across all questions
    _print_final_ensemble_results(final_winner_results_per_method)


    print("\n" + "="*80)

    # If bird track provided, print analogous sections
    if bird_question_summary_df is not None:
        print("\n" + "="*80)
        print("BIRD EVALUATION SUMMARY")
        print("="*80)

        # Overall statistics
        try:
            if 'bird_comparison_result' in result_df.columns and result_df['bird_comparison_result'].notna().any():
                bird_counts = result_df['bird_comparison_result'].value_counts()
                bird_percentages = (bird_counts / total_runs * 100).round(2)
                print(f"\nOVERALL RESULTS (Total runs: {total_runs}):")
                for result_type, count in bird_counts.items():
                    percentage = bird_percentages[result_type]
                    print(f"  {result_type}: {count} ({percentage}%)")
            else:
                print("\nOVERALL RESULTS: No BIRD results available.")
        except Exception as e:
            print(f"[WARNING] Failed to compute BIRD overall stats: {e}")

        # Question-level statistics
        try:
            total_bird_questions = len(bird_question_summary_df)
            bird_with_match = bird_question_summary_df['has_match'].sum()
            bird_without_match = total_bird_questions - bird_with_match
            print(f"\nQUESTION-LEVEL RESULTS (Total unique questions: {total_bird_questions}):")
            pct_m = (bird_with_match / total_bird_questions * 100.0) if total_bird_questions > 0 else 0.0
            pct_nm = (bird_without_match / total_bird_questions * 100.0) if total_bird_questions > 0 else 0.0
            print(f"  Questions with at least one match: {bird_with_match} ({pct_m:.1f}%)")
            print(f"  Questions with no matches: {bird_without_match} ({pct_nm:.1f}%)")
        except Exception as e:
            print(f"[WARNING] Failed to compute BIRD question-level stats: {e}")

        # Ensemble tie-break stats per method
        _print_ensemble_tie_break_stats(bird_tie_break_stats_per_method, "BIRD")

        # Final ensemble per-method results using winners
        _print_final_ensemble_results(bird_final_winner_results_per_method, "BIRD")


def _log_mlflow_stats(args,
                      result_df: pd.DataFrame,
                      question_summary_df: pd.DataFrame,
                      tie_break_stats_per_method: dict = None,
                      final_winner_results_per_method: dict = None):
    """Log Overall, Question-level, Tie-break and Final ensemble results into MLflow using a single unified comparison_result."""
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

        # Log the original all_runs CSV file as an artifact for traceability
        try:
            src_csv = getattr(args, 'all_runs', None)
            if src_csv and os.path.isfile(src_csv):
                mlflow.log_artifact(src_csv, artifact_path='inputs')
        except Exception:
            # Best-effort; continue if artifact logging fails
            pass

        # Log parameters used to call the script (masking sensitive values)
        try:
            # Log the exact command invocation
            try:
                mlflow.log_param('script_command', ' '.join(sys.argv))
            except Exception:
                pass

            # Helper to serialize values
            def _serialize_param_value(val):
                try:
                    if val is None:
                        return None
                    if isinstance(val, (list, tuple)):
                        return ','.join([str(v) for v in val])
                    if isinstance(val, dict):
                        return json.dumps(val)
                    return str(val)
                except Exception:
                    return str(val)

            for k, v in vars(args).items():
                if v is None:
                    continue
                name = _sanitize_mlflow_name(f'arg__{k}')
                lower_k = str(k).lower()
                value_to_log = _serialize_param_value(v)
                if any(s in lower_k for s in ['token', 'password', 'secret', 'key', 'credential']):
                    # Avoid leaking secrets; indicate presence without value
                    value_to_log = '***'
                try:
                    mlflow.log_param(name, value_to_log)
                except Exception:
                    # Best-effort; continue on individual failures
                    pass
        except Exception:
            # Non-fatal if parameter logging fails
            pass

        # Log any extra CLI params that were not defined in argparse but passed by the user
        try:
            extra_cli_params = getattr(args, 'extra_cli_params', None)
            if isinstance(extra_cli_params, dict) and extra_cli_params:
                for k, v in extra_cli_params.items():
                    name = _sanitize_mlflow_name(str(k))
                    lower_k = str(k).lower()
                    value_to_log = _serialize_param_value(v)
                    if any(s in lower_k for s in ['token', 'password', 'secret', 'key', 'credential']):
                        value_to_log = '***'
                    try:
                        mlflow.log_param(name, value_to_log)
                    except Exception:
                        pass
        except Exception:
            # Continue even if extra-params logging fails
            pass

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

        # Question-level breakdowns by complexity/difficulty
        try:
            if 'complexity' in question_summary_df.columns:
                comp_group = question_summary_df.groupby('complexity')['has_match'].agg(['sum', 'count']).reset_index()
                for _, row in comp_group.iterrows():
                    label = _sanitize_mlflow_name(str(row['complexity']))
                    total = int(row['count'])
                    matches = int(row['sum'])
                    pct = (matches / total * 100.0) if total > 0 else 0.0
                    mlflow.log_metric(f'questions_by_complexity__{label}__total', total)
                    mlflow.log_metric(f'questions_by_complexity__{label}__with_match', matches)
                    mlflow.log_metric(f'questions_by_complexity__{label}__with_match_pct', float(pct))
            if 'difficulty' in question_summary_df.columns:
                diff_group = question_summary_df.groupby('difficulty')['has_match'].agg(['sum', 'count']).reset_index()
                for _, row in diff_group.iterrows():
                    label = _sanitize_mlflow_name(str(row['difficulty']))
                    total = int(row['count'])
                    matches = int(row['sum'])
                    pct = (matches / total * 100.0) if total > 0 else 0.0
                    mlflow.log_metric(f'questions_by_difficulty__{label}__total', total)
                    mlflow.log_metric(f'questions_by_difficulty__{label}__with_match', matches)
                    mlflow.log_metric(f'questions_by_difficulty__{label}__with_match_pct', float(pct))
        except Exception:
            pass

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

                # Per-bucket breakdowns by complexity and difficulty
                try:
                    by_comp = stats.get('by_complexity') if isinstance(stats, dict) else None
                    if by_comp:
                        for bucket, comp_stats in by_comp.items():
                            bucket_label = _sanitize_mlflow_name(str(bucket))
                            for metric_name in [
                                'total_questions', 'tie_questions', 'single_finalist_questions', 'single_match_count',
                                'tie_match_count', 'considered_questions', 'winner_match_count', 'winner_no_match_count',
                                'winner_query_error_count']:
                                value = comp_stats.get(metric_name)
                                if value is not None:
                                    mlflow.log_metric(f'{prefix}__by_complexity__{bucket_label}__{metric_name}', float(value))
                    by_diff = stats.get('by_difficulty') if isinstance(stats, dict) else None
                    if by_diff:
                        for bucket, diff_stats in by_diff.items():
                            bucket_label = _sanitize_mlflow_name(str(bucket))
                            for metric_name in [
                                'total_questions', 'tie_questions', 'single_finalist_questions', 'single_match_count',
                                'tie_match_count', 'considered_questions', 'winner_match_count', 'winner_no_match_count',
                                'winner_query_error_count']:
                                value = diff_stats.get(metric_name)
                                if value is not None:
                                    mlflow.log_metric(f'{prefix}__by_difficulty__{bucket_label}__{metric_name}', float(value))
                except Exception:
                    pass

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

                # Collect all keys tied for best match percentage
                if per_key_percentages:
                    tolerance = 1e-9
                    best_keys = [k for k, (mp, _, _) in per_key_percentages.items() if abs(mp - best_match_pct) <= tolerance]
                    if len(best_keys) > 0:
                        sanitized_keys = [_sanitize_mlflow_name(str(k)) for k in best_keys]
                        mlflow.log_param('Best_Ensemble_Pairing', ','.join(sanitized_keys))
                        # Log best percentages; match pct is identical across ties
                        mlflow.log_metric('Best_Match', float(best_match_pct))
                        # For No Match / Query Error, use the first best key for backward-compat
                        first_key = best_keys[0]
                        _, nm_pct, qe_pct = per_key_percentages[first_key]
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
        required=False,
        help='Base path to the databases'
    )
    
    parser.add_argument(
        '--metadata-base-path',
        required=False,
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
        choices=['size', 'frequency', 'random', 'density', 'agent_indiv_grade', 'binary_comp_selection', 'double_elim', 'reverse_size', 'reverse_frequency', 'reverse_density'],
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
    parser.add_argument(
        '--eval-type', '--eval_type',
        choices=['custom', 'bird'],
        default='custom',
        help='Select which eval column to use from CSV: custom uses eval_custom; bird uses eval_bird'
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
    
    # Parse known args, capturing any unknown flags for MLflow logging
    args, _unknown_cli_tokens = parser.parse_known_args()
    # Re-parse from sys.argv to retain exact token order for unknowns
    try:
        argv_tokens = sys.argv[1:]
    except Exception:
        argv_tokens = []
    extra_cli_params = {}
    try:
        idx = 0
        while idx < len(argv_tokens):
            token = argv_tokens[idx]
            if isinstance(token, str) and token.startswith('--'):
                raw = token[2:]
                # Skip if this flag is defined in argparse schema
                defined = any(raw == a or raw.replace('-', '_') == a.replace('-', '_') for a in vars(args).keys())
                if defined:
                    # If this known flag takes a value, skip its value too
                    # Heuristic: if next token exists and doesn't start with '-', assume it's a value
                    if (idx + 1) < len(argv_tokens) and not str(argv_tokens[idx + 1]).startswith('-'):
                        idx += 1
                else:
                    if '=' in raw:
                        key, val = raw.split('=', 1)
                        extra_cli_params[key] = val
                    else:
                        # Lookahead for value
                        if (idx + 1) < len(argv_tokens) and not str(argv_tokens[idx + 1]).startswith('-'):
                            extra_cli_params[raw] = argv_tokens[idx + 1]
                            idx += 1
                        else:
                            extra_cli_params[raw] = True
            idx += 1
    except Exception:
        # Best-effort; ignore failures
        pass
    # Attach for downstream MLflow logging
    setattr(args, 'extra_cli_params', extra_cli_params)
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input file
    if not os.path.exists(args.all_runs):
        logger.error(f"All runs file not found: {args.all_runs}")
        sys.exit(1)
    
    try:
        # Always run in eval-only mode using the selected eval type
        eval_column = 'eval_custom' if str(getattr(args, 'eval_type', 'custom')).lower() == 'custom' else 'eval_bird'
        # If user explicitly passed --eval-column, allow override (back-compat)
        try:
            argv_tokens = sys.argv[1:]
        except Exception:
            argv_tokens = []
        user_overrode_eval_col = any(t in argv_tokens for t in ['--eval-column', '--eval_column'])
        if user_overrode_eval_col:
            eval_column = args.eval_column
        logger.info(f"Starting evaluation (no code execution). Using column: {eval_column}")
        result_df, question_summary_df = evaluate_from_eval_column(
            args.all_runs,
            args.output_dir,
            eval_column=eval_column,
        )

        # Optional: compute ensemble winners per requested methods and evaluate Match/No Match percentages
        # Determine which ensemble methods to run; prefer --ensemble-methods, fallback to deprecated flag
        def _normalize_methods(methods_raw):
            allowed = ['size', 'frequency', 'random', 'density', 'agent_indiv_grade', 'binary_comp_selection', 'double_elim', 'reverse_size', 'reverse_frequency', 'reverse_density']
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


        # Compute tie-break/finalist stats per method (simulated, no LLM execution)
        tie_break_stats_per_method = {}
        for method in methods_to_use:
            for tb in tie_breakers_to_use:
                key = f"{method}|tb:{tb}"
                try:
                    tie_break_stats_per_method[key] = _compute_ensemble_stats(result_df, method, tie_breaker=tb, comparison_col='comparison_result')
                except Exception as e:
                    logger.warning(f"Failed computing tie-break stats for method {method} with tie-breaker {tb} (custom): {e}")

        # Execute ensemble functions for each requested method|tie-breaker to obtain actual winners
        winners_per_method = {}
        for method in methods_to_use:
            for tb in tie_breakers_to_use:
                key = f"{method}|tb:{tb}"
                try:
                    winners_df_exec = ensemble_from_all_runs_df(
                        result_df,
                        ensemble_selection_method=method,
                        use_gradio_agent=False,
                        mlflow_run_id=None,
                        tie_break_method=tb,
                    )
                    winners_per_method[key] = winners_df_exec
                except Exception as e:
                    logger.warning(f"Failed executing ensemble method {method} with tie-breaker {tb}: {e}")

        # Build final per-method winner outcome results using executed winners (LLM may be called)
        final_winner_results_per_method = {}
        try:
            for key, winners_df_exec in winners_per_method.items():
                # Merge winners with result_df to get comparison_result for each chosen winner
                merge_keys = ['question', 'dataset_name', 'db_name', 'question_index', 'model_name']
                for k in merge_keys:
                    if k not in winners_df_exec.columns:
                        # If any key missing, skip this method
                        raise KeyError(f"Winners DF missing key column: {k}")
                merged = winners_df_exec.merge(
                    result_df[
                        ['question', 'dataset_name', 'db_name', 'question_index', 'model_name', 'comparison_result']
                    ],
                    on=merge_keys,
                    how='left'
                )
                # Denominator must be total number of unique questions in the dataset,
                # regardless of whether the method produced a winner for each.
                total_questions = int(question_summary_df.shape[0]) if 'question_summary_df' in locals() and question_summary_df is not None else int(result_df.assign(question_id=result_df['question'].astype(str) + '_' + result_df['db_name'].astype(str) + '_' + result_df['dataset_name'].astype(str))['question_id'].nunique())

                # Count outcomes among the final one winner per question present in merged
                # Any missing winners are accounted as Query Error to keep denominator fixed
                winner_match_count = int((merged['comparison_result'].astype(str).str.strip() == 'Match').sum())
                winner_no_match_count = int((merged['comparison_result'].astype(str).str.strip() == 'No Match').sum())
                accounted = winner_match_count + winner_no_match_count
                winner_query_error_count = max(0, total_questions - accounted)
                final_winner_results_per_method[key] = {
                    'total_questions': int(total_questions),
                    'winner_match_count': winner_match_count,
                    'winner_no_match_count': winner_no_match_count,
                    'winner_query_error_count_adjusted': winner_query_error_count,
                }
        except Exception as e:
            logger.warning(f"Failed building executed final winner results: {e}")

        # Print summary
        print_summary(
            result_df,
            question_summary_df,
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
