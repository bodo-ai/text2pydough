#!/usr/bin/env python3
import argparse
import os
from typing import List

import pandas as pd


def _detect_group_columns(df: pd.DataFrame) -> List[str]:
    """Best-effort detection of question grouping columns.

    Priority:
    1) question_id
    2) question_index
    3) composite of (question, db_name, dataset_name)
    4) question
    Fallback: [] (treat each row independently)
    """
    if 'question_id' in df.columns:
        return ['question_id']
    if 'question_index' in df.columns:
        return ['question_index']
    composite = ['question', 'db_name', 'dataset_name']
    if all(col in df.columns for col in composite):
        return composite
    if 'question' in df.columns:
        return ['question']
    return []


def _build_output_path(input_path: str) -> str:
    """Insert _valid_q before the .csv extension (or append if no extension)."""
    directory, filename = os.path.split(os.path.abspath(input_path))
    name, ext = os.path.splitext(filename)
    if ext.lower() == '.csv':
        return os.path.join(directory, f"{name}_valid_q{ext}")
    return os.path.join(directory, f"{filename}_valid_q.csv")


def filter_valid_questions(input_csv: str, eval_type: str = 'custom') -> str:
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    df = pd.read_csv(input_csv)

    eval_type_norm = (eval_type or 'custom').strip().lower()
    if eval_type_norm not in ('custom', 'bird'):
        raise ValueError("--eval must be one of {'custom','bird'}")

    eval_col = 'eval_custom' if eval_type_norm == 'custom' else 'eval_bird'
    if eval_col not in df.columns:
        raise ValueError(f"Input CSV must contain an '{eval_col}' column")

    group_cols = _detect_group_columns(df)

    # Normalize comparison to be robust to stray whitespace/case
    is_match = df[eval_col].astype(str).str.strip().str.lower() == 'match'

    if not group_cols:
        # No group columns found; fall back to filtering only rows that are Match
        filtered = df[is_match].copy()
    else:
        # Compute which groups (questions) have at least one Match
        matched_groups = (
            df.assign(__is_match=is_match)
              .groupby(group_cols)['__is_match']
              .any()
        )
        # Keep all rows whose group key is in matched_groups == True
        matched_group_keys = set(matched_groups[matched_groups].index.tolist())
        if len(group_cols) == 1:
            key_col = group_cols[0]
            filtered = df[df[key_col].isin(matched_groups[matched_groups].index)].copy()
        else:
            # Build tuple keys for comparison
            df_keys = list(map(tuple, df[group_cols].itertuples(index=False, name=None)))
            mask = [key in matched_group_keys for key in df_keys]
            filtered = df[pd.Series(mask, index=df.index)].copy()

    out_path = _build_output_path(input_csv)
    filtered.to_csv(out_path, index=False)
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Filter CSV to questions with at least one Match in the selected eval column, keeping all rows of those questions.")
    parser.add_argument('--input', required=True, help='Path to input CSV file')
    parser.add_argument('--eval', dest='eval', choices=['custom', 'bird'], default='custom', help='Which eval column to use (custom->eval_custom, bird->eval_bird). Default: custom')
    args = parser.parse_args()

    out_path = filter_valid_questions(args.input, eval_type=args.eval)
    print(out_path)


if __name__ == '__main__':
    main()


