import pandas as pd
import os
import json
from datetime import datetime

def process_csv(csv1_path, csv2_path, output_true, output_false, output_error, metadata_path):
    # Load the CSV files
    df1 = pd.read_csv(csv1_path)
    df2 = pd.read_csv(csv2_path)

    # Check if the columns of both DataFrames match
    if list(df1.columns) != list(df2.columns):
        raise ValueError("The columns of the two CSV files do not match.")

    # Concatenate the DataFrames
    df_total = pd.concat([df1, df2], ignore_index=True)
    print(f"\u2705 Loaded {len(df1)} rows from {csv1_path} and {len(df2)} rows from {csv2_path}. Total rows: {len(df_total)}")

    # Sort so that True rows come first for each question
    df_total = df_total.sort_values(by=['question', 'dataframe_match'], ascending=[True, False])

    # Drop duplicates, keeping the first (which will be True if exists)
    df_total_unique = df_total.drop_duplicates(subset=['question'], keep='first')

    # Separate rows with non-empty 'error' column
    df_error = df_total_unique[df_total_unique['error'].notna() & (df_total_unique['error'] != '')]
    print(f"\u2705 Found {len(df_error)} unique rows with non-empty 'error' column")

    # Remove rows with errors from the main DataFrame
    df_total_unique = df_total_unique[~df_total_unique.index.isin(df_error.index)]

    # Split remaining rows into True and False after deduplication
    df_true = df_total_unique[df_total_unique['dataframe_match'] == True]
    print(f"\u2705 Found {len(df_true)} unique rows with 'dataframe_match' == True")

    df_false = df_total_unique[df_total_unique['dataframe_match'] == False]
    print(f"\u2705 Found {len(df_false)} unique rows with 'dataframe_match' == False")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_true), exist_ok=True)

    # Save the results to new CSV files
    df_true.to_csv(output_true, index=False)
    df_false.to_csv(output_false, index=False)
    df_error.to_csv(output_error, index=False)

    # Save metadata JSON
    metadata = {
        "input_files": [csv1_path, csv2_path],
        "output_true": output_true,
        "output_false": output_false,
        "output_error": output_error
    }
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\u2705 Generated Files:\n - {output_true}\n - {output_false}\n - {output_error}\n - {metadata_path}")

def main():
    # Create a timestamped folder inside 'merged_files'
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    merged_dir = os.path.join('merged_files', timestamp)
    os.makedirs(merged_dir, exist_ok=True)

    # Input and output file paths (modify as needed)
    csv1_path = "/home/jupyter/text2pydough/workbench/lcar_lab/labeling_agent/evaluator_agent_improvement/results/20250612_011724/results.csv"
    csv2_path = "/home/jupyter/text2pydough/workbench/lcar_lab/labeling_agent/evaluator_agent_improvement/results/20250612_011834/results.csv"

    output_true = os.path.join(merged_dir, 'result_match_true.csv')
    output_false = os.path.join(merged_dir, 'result_match_false.csv')
    output_error = os.path.join(merged_dir, 'result_with_errors.csv')
    metadata_path = os.path.join(merged_dir, 'merge_metadata.json')

    process_csv(csv1_path, csv2_path, output_true, output_false, output_error, metadata_path)

if __name__ == "__main__":
    main()