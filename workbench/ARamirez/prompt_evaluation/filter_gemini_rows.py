#!/usr/bin/env python3
"""
Filter rows from a CSV so that only rows with a `model_name` containing
the value "gemini" remain (case-insensitive).

Usage:
    python filter_gemini_rows.py /absolute/path/to/input.csv

This writes a sibling file named `<input>__gemini_filtered.csv`.
"""

import csv
import os
import sys


def main() -> int:
    # Increase CSV field size limit to handle very large fields
    try:
        csv.field_size_limit(sys.maxsize)
    except OverflowError:
        # Fallback for some platforms where sys.maxsize is too large for csv module
        csv.field_size_limit(2**31 - 1)

    if len(sys.argv) != 2:
        print(
            "Usage: python filter_gemini_rows.py /absolute/path/to/input.csv",
            file=sys.stderr,
        )
        return 2

    input_path = os.path.abspath(sys.argv[1])
    if not os.path.exists(input_path):
        print(f"[error] Input CSV not found: {input_path}", file=sys.stderr)
        return 1

    directory, filename = os.path.split(input_path)
    name, ext = os.path.splitext(filename)
    output_path = os.path.join(directory, f"{name}__gemini_filtered{ext}")

    total_rows = 0
    matched_rows = 0

    with open(input_path, "r", encoding="utf-8", newline="") as infile:
        reader = csv.DictReader(infile)
        if reader.fieldnames is None:
            print("[error] CSV appears to have no header row.", file=sys.stderr)
            return 1
        if "model_name" not in reader.fieldnames:
            print(
                "[error] Column 'model_name' not found in CSV headers: "
                + ", ".join(reader.fieldnames),
                file=sys.stderr,
            )
            return 1

        with open(output_path, "w", encoding="utf-8", newline="") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
            writer.writeheader()

            for row in reader:
                total_rows += 1
                model_name_value = row.get("model_name")
                if model_name_value is not None and "gemini" in model_name_value.lower():
                    matched_rows += 1
                    writer.writerow(row)

    print(f"Wrote {matched_rows} matching rows out of {total_rows} to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


