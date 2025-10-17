#!/usr/bin/env python3
import argparse
import os

import pandas as pd


def _build_output_path(input_path: str) -> str:
    """Insert _no_query_error before the .csv extension (or append if no extension)."""
    directory, filename = os.path.split(os.path.abspath(input_path))
    name, ext = os.path.splitext(filename)
    if ext.lower() == '.csv':
        return os.path.join(directory, f"{name}_no_query_error{ext}")
    return os.path.join(directory, f"{filename}_no_query_error.csv")


def filter_no_query_error_rows(input_csv: str, eval_type: str = 'custom') -> str:
    """Filter out rows whose selected eval column contains 'Query error'.

    The eval column is chosen via --eval {custom|bird} mapping to
    eval_custom or eval_bird, respectively. The match is case-insensitive
    and treats NaNs as non-matching.
    """
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    df = pd.read_csv(input_csv)

    eval_type_norm = (eval_type or 'custom').strip().lower()
    if eval_type_norm not in ('custom', 'bird'):
        raise ValueError("--eval must be one of {'custom','bird'}")

    eval_col = 'eval_custom' if eval_type_norm == 'custom' else 'eval_bird'
    if eval_col not in df.columns:
        raise ValueError(f"Input CSV must contain an '{eval_col}' column")

    contains_query_error = (
        df[eval_col]
        .astype(str)
        .str.contains('query error', case=False, na=False)
    )

    # Keep rows that do NOT contain query error in the chosen eval column
    filtered = df[~contains_query_error].copy()

    out_path = _build_output_path(input_csv)
    filtered.to_csv(out_path, index=False)
    return out_path


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Filter CSV by removing rows whose chosen eval column contains 'Query error'."
        )
    )
    parser.add_argument('--input', required=True, help='Path to input CSV file')
    parser.add_argument(
        '--eval', dest='eval', choices=['custom', 'bird'], default='custom',
        help='Which eval column to use (custom->eval_custom, bird->eval_bird). Default: custom'
    )
    args = parser.parse_args()

    out_path = filter_no_query_error_rows(args.input, eval_type=args.eval)
    print(out_path)


if __name__ == '__main__':
    main()


