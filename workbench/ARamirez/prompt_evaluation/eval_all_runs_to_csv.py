#!/usr/bin/env python3
"""
Read an all_runs CSV, evaluate each row using existing test_data.eval.process_row,
add a column 'eval_result' with values {Match, NoMatch, Query error}, and
write a new CSV in the same directory prefixed with 'eval_'.

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

# Ensure we can import sibling package modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from test_data.eval import process_row  # type: ignore


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
    if 'error' in text.lower() or 'unknown' in text.lower() or 'sql' in text.lower() or 'query' in text.lower():
        return 'Query error'
    # Default fallback
    return 'Query error'


def evaluate_file(all_runs_path: str, db_base_path: str, metadata_base_path: str, num_threads: int = 0) -> str:
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

    # Evaluate per row (optionally threaded)
    results = []

    def _eval_row(row):
        try:
            res, exc = process_row(row, db_base_path, metadata_base_path)
        except Exception:
            res = 'Query Error'
        return _normalize_eval_result(res)

    if num_threads and num_threads > 1:
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            results = list(executor.map(_eval_row, (row for _, row in df.iterrows())))
    else:
        for _, row in df.iterrows():
            results.append(_eval_row(row))

    df['eval_result'] = results

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
    args = parser.parse_args()

    out_path = evaluate_file(args.all_runs, args.db_base_path, args.metadata_base_path, num_threads=args.num_threads)
    print(out_path)


if __name__ == '__main__':
    main()


