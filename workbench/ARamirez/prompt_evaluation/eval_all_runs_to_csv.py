#!/usr/bin/env python3
"""
Read an all_runs CSV, evaluate each row using existing test_data.eval.process_row,
and write a new CSV in the same directory prefixed with 'eval_'.

Outputs the following tri-state columns (each value is one of {Match, NoMatch, Query error}):
- eval_custom: normalized custom DataFrame comparison result
- eval_bird:   normalized BIRD SQL comparison result

Additionally, two columns capture the reason when a result is 'Query error':
- eval_custom_error_reason
- eval_bird_error_reason

For backward compatibility, 'eval_result' is also written and equals 'eval_custom'.

Usage:
  python eval_all_runs_to_csv.py \
    --all-runs /path/to/all_runs.csv \
    --db-base-path /path/to/db_base \
    --metadata-base-path /path/to/metadata_base
"""

import argparse
import os
import sys
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, Tuple, Optional
import multiprocessing as mp

# Ensure we can import sibling package modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from test_data.eval import process_row, query_sqlite_db  # type: ignore


def _create_ground_truth_cache(df: pd.DataFrame, db_base_path: str) -> Dict[Tuple[str, str, str], Tuple[Optional[pd.DataFrame], Optional[str]]]:
    """Create a cache of ground truth SQL results keyed by (question_index, dataset_name, db_name, sql).
    
    Returns:
        Dict mapping (question_index, dataset_name, db_name, sql) -> (ground_truth_df, sql_exception)
    """
    cache = {}
    
    # Group by the key columns to avoid duplicate SQL executions
    unique_queries = df.groupby(['question_index', 'dataset_name', 'db_name', 'sql']).first().reset_index()
    
    print(f"Caching ground truth results for {len(unique_queries)} unique queries...")
    
    for _, row in unique_queries.iterrows():
        question_index = row['question_index']
        dataset_name = row['dataset_name']
        db_name = row['db_name']
        sql = row['sql']
        
        db_path = os.path.join(db_base_path, dataset_name, "databases", db_name, f"{db_name}.sqlite")
        
        # Execute the ground truth SQL once per unique query
        ground_truth_df, sql_exception = query_sqlite_db(sql, db_path)
        
        cache_key = (question_index, dataset_name, db_name, sql)
        cache[cache_key] = (ground_truth_df, sql_exception)
    
    print(f"Ground truth cache created with {len(cache)} entries")
    return cache


def _normalize_eval_result(result_value):
    """Map various result strings to the required tri-state output.

    Input values can include: 'Match', 'No Match', 'Query Error', 'SQL error', 'Unknown', etc.
    Output must be one of: 'Match', 'NoMatch', 'Query error'.
    """
    if result_value is None:
        return 'Query error'
    text = str(result_value).strip()
    if text == 'Match':
        return 'Match'
    if text.replace(' ', '').lower() == 'nomatch':
        return 'NoMatch'
    # Treat any error/unknown/SQL error as a Query error per requirement
    lowered = text.lower()
    if (
        'error' in lowered
        or 'unknown' in lowered
        or 'sql' in lowered
        or 'query' in lowered
        or 'not available' in lowered
        or 'no sql generated' in lowered
        or 'timeout' in lowered
    ):
        return 'Query error'
    # Default fallback
    return 'Query error'


def _pydough_exec_worker(q, extracted_code, metadata_path, db_name, db_path):
    """Worker to execute PyDough code in a separate process."""
    try:
        import pydough  # noqa: F401  (import inside process)
        from datetime import datetime  # noqa: F401
        from test_data.eval import execute_code_and_extract_result  # type: ignore

        local_env = {"pydough": pydough, "datetime": datetime}
        result_df, execution_exception, generated_sql = execute_code_and_extract_result(
            extracted_code, local_env, metadata_path, db_name, db_path
        )
        q.put(("ok", (result_df, execution_exception, generated_sql)))
    except BaseException as e:
        q.put(("err", str(e)))


def _execute_pydough_with_timeout(extracted_code, metadata_path, db_name, db_path, timeout_seconds: int):
    """Execute PyDough in a subprocess with timeout.

    Returns (result_df, execution_exception, generated_sql, timed_out: bool)
    """
    q = mp.Queue()
    p = mp.Process(target=_pydough_exec_worker, args=(q, extracted_code, metadata_path, db_name, db_path))
    p.daemon = True
    p.start()
    try:
        status, payload = q.get(timeout=timeout_seconds)
    except Exception:
        if p.is_alive():
            p.terminate()
        p.join()
        return None, 'timeout', None, True
    else:
        p.join()
        if status == 'ok':
            result_df, execution_exception, generated_sql = payload
            return result_df, execution_exception, generated_sql, False
        return None, str(payload), None, False


def _process_row_with_cache(row, db_base_path: str, metadata_base_path: str, ground_truth_cache: Dict, timeout_seconds: int) -> Tuple[str, str, Optional[str], Optional[str]]:
    """Modified version of process_row that uses cached ground truth results.
    
    Returns:
        Tuple of (custom_eval_result, bird_eval_result, custom_error_reason, bird_error_reason)
    """
    # Import here to avoid circular imports
    from test_data.eval import compare_df, bird_eval
    import pydough
    from datetime import datetime
    
    extracted_code = row.get('extracted_python_code')
    question = row.get('question')
    question_index = row.get('question_index')
    db_name = row['db_name']
    dataset_name = row['dataset_name']
    sql = row['sql']
    db_path = os.path.join(db_base_path, dataset_name, "databases", db_name, f"{db_name}.sqlite")
    
    # Get cached ground truth result
    cache_key = (question_index, dataset_name, db_name, sql)
    ground_truth_df, sql_exception = ground_truth_cache.get(cache_key, (None, "Cache miss"))
    
    # Initialize default return values
    custom_eval_result = 'Unknown'
    bird_eval_result = 'Unknown'
    custom_error_reason: Optional[str] = None
    bird_error_reason: Optional[str] = None
    
    # If ground truth SQL failed, both evaluations fail
    if ground_truth_df is None:
        # If ground truth failed, both evaluations are Query error; capture reason
        reason = f"ground truth sql error: {sql_exception}" if sql_exception else 'ground truth sql error'
        return ('Query error', 'Query error', reason, reason)
    
    # Case 1: We have extracted Python code to execute
    if pd.notna(extracted_code): 
        metadata_dir = os.path.join(metadata_base_path, dataset_name, "metadata")
        metadata_path = os.path.join(metadata_dir, f"{db_name}_graph.json")

        # Execute the PyDough code with timeout
        result_df, execution_exception, generated_sql, timed_out = _execute_pydough_with_timeout(
            extracted_code, metadata_path, db_name, db_path, timeout_seconds
        )
        
        if timed_out:
            # On timeout classify both evaluations as Query error and record reason
            return ('Query error', 'Query error', 'timeout', 'timeout')

        if result_df is not None and execution_exception is None:
            # Custom evaluation: DataFrame comparison using cached ground truth
            try:
                df_comparison_success = compare_df(
                    ground_truth_df, result_df, query_category="a", question=question
                )
                custom_eval_result = 'Match' if df_comparison_success else 'NoMatch'
                if custom_eval_result != 'Query error':
                    custom_error_reason = None
            except Exception as e:
                custom_eval_result = 'Query error'
                custom_error_reason = f'df comparison exception: {e}'
            
            # Bird evaluation: SQL execution comparison
            if generated_sql is not None:
                try:
                    sql_comparison_result = bird_eval(generated_sql, sql, db_path)
                    bird_eval_result = 'Match' if sql_comparison_result == 1 else 'NoMatch'
                    if bird_eval_result != 'Query error':
                        bird_error_reason = None
                except Exception as e:
                    bird_eval_result = 'Query error'
                    bird_error_reason = f'bird eval exception: {e}'
            else:
                bird_eval_result = 'Query error'
                bird_error_reason = 'no generated sql'
        else:
            # PyDough code execution failed
            custom_eval_result = 'Query error'
            bird_eval_result = 'Query error'
            custom_error_reason = f'execution exception: {execution_exception}' if execution_exception else 'execution failed'
            bird_error_reason = 'execution failed'
    
    # Case 2: No extracted code, try to use pre-computed DataFrame from CSV
    else:
        # Try to get generated DataFrame/SQL from CSV
        generated_df_json = row.get('gen_df_json')
        generated_sql = row.get('gen_sql')
        # Fallback: some producers name the column 'generated_sql'
        if (generated_sql is None or (isinstance(generated_sql, float) and pd.isna(generated_sql))) and 'generated_sql' in row:
            generated_sql = row.get('generated_sql')

        if generated_df_json is not None and generated_sql is not None:
            try:
                generated_df = pd.read_json(generated_df_json)
                df_comparison_success = compare_df(
                    ground_truth_df, generated_df, query_category="a", question=question
                )
                custom_eval_result = 'Match' if df_comparison_success else 'NoMatch'
                sql_comparison_result = bird_eval(generated_sql, sql, db_path)
                bird_eval_result = 'Match' if sql_comparison_result == 1 else 'NoMatch'
                if custom_eval_result != 'Query error':
                    custom_error_reason = None
                if bird_eval_result != 'Query error':
                    bird_error_reason = None
            except Exception as e:
                custom_eval_result = 'Query error'
                bird_eval_result = 'Query error'
                custom_error_reason = f'generated df/compare exception: {e}'
                bird_error_reason = f'bird eval exception: {e}'
        elif generated_sql is not None:
            # We have SQL but no generated DataFrame; still evaluate BIRD SQL comparison
            try:
                sql_comparison_result = bird_eval(generated_sql, sql, db_path)
                bird_eval_result = 'Match' if sql_comparison_result == 1 else 'NoMatch'
                if bird_eval_result != 'Query error':
                    bird_error_reason = None
            except Exception as e:
                bird_eval_result = 'Query error'
                bird_error_reason = f'bird eval exception: {e}'
            # Custom DataFrame comparison cannot be performed without a generated dataframe
            custom_eval_result = 'Query error'
            custom_error_reason = 'no generated df'
        else:
            custom_eval_result = 'Query error'
            bird_eval_result = 'Query error'
            custom_error_reason = 'no generated df'
            bird_error_reason = 'no generated sql'
    
    return (custom_eval_result, bird_eval_result, custom_error_reason, bird_error_reason)


def evaluate_file(all_runs_path: str, db_base_path: str, metadata_base_path: str, num_threads: int = 0, timeout_seconds: int = 180) -> str:
    """Evaluate rows from all_runs_path and write an eval_ prefixed CSV.

    Returns the path to the written CSV.
    """
    if not os.path.exists(all_runs_path):
        raise FileNotFoundError(f"All runs file not found: {all_runs_path}")

    df = pd.read_csv(all_runs_path)

    # Ensure the code column exists where process_row expects it
    if 'extracted_python_code' not in df.columns:
        if 'code' in df.columns:
            df['extracted_python_code'] = df['code']
        else:
            # Proceed; process_row will yield Unknown/Query error
            df['extracted_python_code'] = None

    # Normalize SQL column naming differences:
    # Some producers write generated_sql rather than gen_sql which downstream expects
    if 'gen_sql' not in df.columns:
        if 'generated_sql' in df.columns:
            df['gen_sql'] = df['generated_sql']
        else:
            df['gen_sql'] = None

    # Create ground truth cache to minimize SQL calls per question
    ground_truth_cache = _create_ground_truth_cache(df, db_base_path)

    # Evaluate per row (optionally threaded) using cached ground truth
    results = []

    def _eval_row(row):
        try:
            custom_res, bird_res, custom_reason, bird_reason = _process_row_with_cache(row, db_base_path, metadata_base_path, ground_truth_cache, timeout_seconds)
        except Exception:
            return ('Query error', 'Query error', 'unexpected exception', 'unexpected exception')
        return (
            _normalize_eval_result(custom_res),
            _normalize_eval_result(bird_res),
            custom_reason if _normalize_eval_result(custom_res) == 'Query error' else None,
            bird_reason if _normalize_eval_result(bird_res) == 'Query error' else None,
        )

    if num_threads and num_threads > 1:
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            results = list(executor.map(_eval_row, (row for _, row in df.iterrows())))
    else:
        for _, row in df.iterrows():
            results.append(_eval_row(row))

    # Split results into columns
    df['eval_custom'] = [r[0] for r in results]
    df['eval_bird'] = [r[1] for r in results]
    # Error reasons (only populated when corresponding result is 'Query error')
    df['eval_custom_error_reason'] = [r[2] for r in results]
    df['eval_bird_error_reason'] = [r[3] for r in results]
    # Back-compat single column mirroring custom eval
    df['eval_result'] = df['eval_custom']

    # Build output path in same directory, prefixing filename with 'eval_'
    in_dir = os.path.dirname(os.path.abspath(all_runs_path))
    in_base = os.path.basename(all_runs_path)
    out_base = f"eval_{in_base}"
    out_path = os.path.join(in_dir, out_base)

    df.to_csv(out_path, index=False)
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Add eval_result to all_runs CSV and save as eval_ prefixed file")
    parser.add_argument('--all-runs', required=True, help='Path to the all_runs CSV file')
    parser.add_argument('--db-base-path', required=True, help='Base path to databases')
    parser.add_argument('--metadata-base-path', required=True, help='Base path to metadata files')
    parser.add_argument('--num-threads', type=int, default=0, help='Optional worker threads for evaluation')
    parser.add_argument('--timeout', type=int, default=180, help='Timeout in seconds for PyDough execution (default 180)')
    args = parser.parse_args()

    out_path = evaluate_file(
        args.all_runs,
        args.db_base_path,
        args.metadata_base_path,
        num_threads=args.num_threads,
        timeout_seconds=args.timeout,
    )
    print(out_path)


if __name__ == '__main__':
    main()


