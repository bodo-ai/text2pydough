#!/usr/bin/env python3
import argparse
import os
from typing import Dict, List, Tuple

import pandas as pd


def _parse_pair_vector(value: str) -> List[str]:
    if not isinstance(value, str):
        return []
    s = value.strip()
    if not s:
        return []
    # Allow values like "[1-0,0-1]" or "1-0, 0-1" or even already-parsed-like strings
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    if not s:
        return []
    parts = [p.strip() for p in s.split(',') if p.strip()]
    # Only keep recognized tokens
    allowed = {"0-0", "0-1", "1-0", "1-1"}
    return [p for p in parts if p in allowed]


def compute_global_pair_rates(csv_path: str) -> Tuple[Dict[str, float], int]:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if 'pair_vector' not in df.columns:
        raise ValueError("Input must contain column 'pair_vector' produced by pair_vectors_by_question")

    counts: Dict[str, int] = {"0-0": 0, "0-1": 0, "1-0": 0, "1-1": 0}

    for v in df['pair_vector']:
        for token in _parse_pair_vector(v):
            counts[token] += 1

    total = sum(counts.values())
    if total == 0:
        return ({k: 0.0 for k in counts}, 0)

    return ({k: counts[k] / total for k in counts}, total)


def main():
    parser = argparse.ArgumentParser(description="Compute global rates of pair outcomes (0-0,0-1,1-0,1-1) across all questions.")
    parser.add_argument('csv', help='Path to CSV produced by pair_vectors_by_question')
    args = parser.parse_args()

    rates, total = compute_global_pair_rates(args.csv)

    # Print summary
    print("Global rates across all pair outcomes (denominator = total pair entries):")
    print(f"Total pair entries: {total}")
    # Ensure a stable order
    for key in ["0-0", "0-1", "1-0", "1-1"]:
        pct = rates.get(key, 0.0) * 100.0
        print(f"{key}: {pct:.2f}%")


if __name__ == '__main__':
    main()


