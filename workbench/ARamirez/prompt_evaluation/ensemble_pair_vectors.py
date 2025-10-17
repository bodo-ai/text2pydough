#!/usr/bin/env python3
import argparse
import os
from itertools import combinations
from typing import List, Optional

import pandas as pd

from pair_vectors_by_question import _detect_group_columns, _first_non_null


def _derive_output_path(input_path: str) -> str:
    d, f = os.path.split(os.path.abspath(input_path))
    name, ext = os.path.splitext(f)
    if ext.lower() != '.csv':
        ext = '.csv'
    return os.path.join(d, f"{name}_ensemble_pair_vectors{ext}")


def _evaluate_pair(question: str, a_json: str, b_json: str) -> Optional[int]:
    try:
        from scooring_agents_exp import evaluate_binary_dataframes_with_confidence as llm_evaluate_binary
    except Exception:
        return None

    try:
        result = llm_evaluate_binary(question, [a_json, b_json])
        if isinstance(result, (int, float)):
            return int(result)
        try:
            return int(str(result).strip())
        except Exception:
            return None
    except Exception:
        return None


def _to_json_str(gen_df_json: Optional[str], df_obj_str: Optional[str]) -> str:
    # We rely on gen_df_json produced in the eval CSV; if missing, fall back to df_obj_str
    if isinstance(gen_df_json, str) and len(gen_df_json.strip()) > 0:
        return gen_df_json.strip()
    # As a last resort, try to coerce df string into a tiny JSON list with one string cell
    try:
        s = str(df_obj_str) if df_obj_str is not None else ""
        if len(s.strip()) == 0:
            return "[]"
        # Minimal valid JSON array with a single field that carries the textual table representation
        payload = [{"__df_text__": s[:5000]}]
        return pd.Series(payload).to_json(orient="values")
    except Exception:
        return "[]"


def build_ensemble_pair_vectors(input_csv: str) -> str:
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    df = pd.read_csv(input_csv)

    group_cols = _detect_group_columns(df)

    # If no grouping columns, compute a single global vector across all rows
    if not group_cols:
        g = df.copy()
        question = _first_non_null(g['question']) if 'question' in g.columns else None
        tokens: List[str] = []
        # Candidate JSONs in original order
        cand_json: List[str] = [
            _to_json_str(
                row.gen_df_json if 'gen_df_json' in g.columns else None,
                row.df if 'df' in g.columns else None,
            )
            for _, row in g.iterrows()
        ]
        for i, j in combinations(range(len(cand_json)), 2):
            winner = _evaluate_pair(question or "", cand_json[i], cand_json[j])
            if winner == 0:
                tokens.append("1-0")
            elif winner == 1:
                tokens.append("0-1")
            else:
                # undecided -> skip (no token)
                pass

        vector_str = f"[{','.join(tokens)}]"

        out = df[[
            'question_index', 'question', 'sql', 'dataset_name', 'db_name'
        ]].copy() if set(['question_index','question','sql','dataset_name','db_name']).issubset(df.columns) else pd.DataFrame()

        # Ensure columns exist even if missing
        for c in ['question_index', 'question', 'sql', 'dataset_name', 'db_name']:
            if c not in out.columns:
                out[c] = None
        out['pair_vector'] = vector_str
        # For compatibility with pair_vectors_by_question output
        out['match%'] = None

        out_path = _derive_output_path(input_csv)
        out.to_csv(out_path, index=False)
        return out_path

    # Compute per-group pair vectors preserving input row order
    records = []
    for _, g in df.groupby(group_cols, sort=False):
        question = _first_non_null(g['question']) if 'question' in g.columns else None

        cand_json: List[str] = [
            _to_json_str(
                row.gen_df_json if 'gen_df_json' in g.columns else None,
                row.df if 'df' in g.columns else None,
            )
            for _, row in g.iterrows()
        ]

        tokens: List[str] = []
        for i, j in combinations(range(len(cand_json)), 2):
            winner = _evaluate_pair(question or "", cand_json[i], cand_json[j])
            if winner == 0:
                tokens.append("1-0")
            elif winner == 1:
                tokens.append("0-1")
            else:
                # undecided -> skip token
                pass

        vector_str = f"[{','.join(tokens)}]"

        question_index = _first_non_null(g['question_index']) if 'question_index' in g.columns else None
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
            'match%': None,
        })

    out_df = pd.DataFrame.from_records(records, columns=[
        'question_index', 'question', 'sql', 'dataset_name', 'db_name', 'pair_vector', 'match%'
    ])
    out_path = _derive_output_path(input_csv)
    out_df.to_csv(out_path, index=False)
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Generate per-question binary-comparison pair vectors (1-0/0-1) using ensemble logic.")
    parser.add_argument('csv', help='Path to input evaluation CSV (multiple runs per question)')
    args = parser.parse_args()

    out_path = build_ensemble_pair_vectors(args.csv)
    print(out_path)


if __name__ == '__main__':
    main()


