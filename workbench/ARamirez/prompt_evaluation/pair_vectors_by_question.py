#!/usr/bin/env python3
import argparse
import os
from itertools import combinations
from typing import List, Tuple

import pandas as pd


def _detect_group_columns(df: pd.DataFrame) -> List[str]:
    """Detect columns to group rows belonging to the same logical question.

    Priority order:
    - question_id
    - question_index
    - composite of (question, db_name, dataset_name)
    - question
    """
    if 'question_id' in df.columns:
        return ['question_id']
    if 'question_index' in df.columns:
        return ['question_index']
    composite = ['question', 'db_name', 'dataset_name']
    if all(c in df.columns for c in composite):
        return composite
    if 'question' in df.columns:
        return ['question']
    # No grouping columns: treat each row as its own group
    return []


def _select_eval_column(df: pd.DataFrame, eval_type: str) -> str:
    eval_type = (eval_type or 'custom').strip().lower()
    if eval_type not in ('custom', 'bird'):
        raise ValueError("--eval must be 'custom' or 'bird'")
    col = 'eval_custom' if eval_type == 'custom' else 'eval_bird'
    if col not in df.columns:
        raise ValueError(f"Input CSV must contain column '{col}'")
    return col


def _match_flags(values: pd.Series) -> List[int]:
    """Convert eval values to 1/0 flags (1 if 'Match', else 0)."""
    return (values.astype(str).str.strip().str.lower() == 'match').astype(int).tolist()


def _pairwise_flags(flags: List[int]) -> List[str]:
    """Return ordered pairings in round-robin fashion as strings like '1-0'.

    The order follows index combinations (i<j). For flags [f0,f1,f2], pairs:
    (0,1),(0,2),(1,2) -> ["f0-f1","f0-f2","f1-f2"].
    """
    out: List[str] = []
    for i, j in combinations(range(len(flags)), 2):
        out.append(f"{flags[i]}-{flags[j]}")
    return out


def _first_non_null(series: pd.Series):
    for v in series:
        if pd.notna(v):
            return v
    return None


def build_pair_vectors(input_csv: str, eval_type: str = 'custom') -> str:
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    df = pd.read_csv(input_csv)

    eval_col = _select_eval_column(df, eval_type)
    group_cols = _detect_group_columns(df)

    # If no grouping columns, each row is a question by itself -> vector is []
    if not group_cols:
        df = df.copy()
        flags = _match_flags(df[eval_col])
        pairs = _pairwise_flags(flags)
        vector_str = f"[{','.join(pairs)}]"
        ratio = (sum(flags) / len(flags)) if len(flags) > 0 else 0.0
        # Carry metadata from each row; vector is global for the entire file
        out = df[['question_index', 'question', 'sql', 'dataset_name', 'db_name']].copy()
        # Ensure columns exist even if missing
        for c in ['question_index', 'question', 'sql', 'dataset_name', 'db_name']:
            if c not in out.columns:
                out[c] = None
        out['pair_vector'] = vector_str
        out['match%'] = ratio
        out_path = _derive_output_path(input_csv)
        out.to_csv(out_path, index=False)
        return out_path

    # Compute per-group pair vectors preserving input row order
    records = []
    for _, g in df.groupby(group_cols, sort=False):
        # Preserve the existing order of rows as they appear in the CSV
        flags = _match_flags(g[eval_col])
        pairs = _pairwise_flags(flags)
        vector_str = f"[{','.join(pairs)}]"
        ratio = (sum(flags) / len(flags)) if len(flags) > 0 else 0.0

        # Derive representative metadata rows; attempt to keep "first" non-null/consistent
        question_index = _first_non_null(g['question_index']) if 'question_index' in g.columns else None
        question = _first_non_null(g['question']) if 'question' in g.columns else None
        sql = _first_non_null(g['sql']) if 'sql' in g.columns else None
        dataset_name = _first_non_null(g['dataset_name']) if 'dataset_name' in g.columns else None
        db_name = _first_non_null(g['db_name']) if 'db_name' in g.columns else None

        records.append({
            'question_index': question_index,
            'question': question,
            'sql': sql,
            'dataset_name': dataset_name,
            'db_name': db_name,
            'pair_vector': vector_str,
            'match%': ratio,
        })

    out_df = pd.DataFrame.from_records(records, columns=['question_index', 'question', 'sql', 'dataset_name', 'db_name', 'pair_vector', 'match%'])
    out_path = _derive_output_path(input_csv)
    out_df.to_csv(out_path, index=False)
    return out_path


def _derive_output_path(input_path: str) -> str:
    d, f = os.path.split(os.path.abspath(input_path))
    name, ext = os.path.splitext(f)
    if ext.lower() != '.csv':
        ext = '.csv'
    return os.path.join(d, f"{name}_pair_vectors{ext}")


def main():
    parser = argparse.ArgumentParser(description="Generate per-question round-robin match pair vectors from a CSV.")
    parser.add_argument('--input', required=True, help='Path to input CSV file')
    parser.add_argument('--eval', dest='eval', choices=['custom', 'bird'], default='custom', help='Which eval column to use: custom->eval_custom, bird->eval_bird (default: custom)')
    args = parser.parse_args()

    out_path = build_pair_vectors(args.input, eval_type=args.eval)
    print(out_path)


if __name__ == '__main__':
    main()


