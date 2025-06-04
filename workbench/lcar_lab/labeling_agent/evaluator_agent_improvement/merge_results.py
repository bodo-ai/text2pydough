import pandas as pd
import os
import json
from datetime import datetime

def process_csv(csv1_path, csv2_path, output_true, output_false, metadata_path):
    # Load the CSV files
    df1 = pd.read_csv(csv1_path)
    df2 = pd.read_csv(csv2_path)

    # Check if the columns of both DataFrames match
    if list(df1.columns) != list(df2.columns):
        raise ValueError("The columns of the two CSV files do not match.")

    # Concatenate the DataFrames
    df_total = pd.concat([df1, df2], ignore_index=True)
    print(f"✅ Loaded {len(df1)} rows from {csv1_path} and {len(df2)} rows from {csv2_path}. Total rows: {len(df_total)}")
    # Filter rows where 'dataframe_match' is True or False
    df_true = df_total[df_total['dataframe_match'] == True]
    print(f"✅ Found {len(df_true)} rows with 'dataframe_match' == True")
    df_true = df_true.drop_duplicates()
    print(f"✅ Total unique rows after filtering: {len(df_true)}")
    df_false = df_total[df_total['dataframe_match'] == False].drop_duplicates()
    print(f"✅ Found {len(df_false)} rows with 'dataframe_match' == False")
    df_false = df_false.drop_duplicates()
    print(f"✅ Total unique rows after filtering: {len(df_false)}")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_true), exist_ok=True)

    # Save the results to new CSV files
    df_true.to_csv(output_true, index=False)
    df_false.to_csv(output_false, index=False)

    # Save metadata JSON
    metadata = {
        "input_files": [csv1_path, csv2_path],
        "output_true": output_true,
        "output_false": output_false
    }
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"✅ Generated Files:\n - {output_true}\n - {output_false}\n - {metadata_path}")

def main():
    # Create a timestamped folder inside 'merged_files'
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    merged_dir = os.path.join('merged_files', timestamp)
    os.makedirs(merged_dir, exist_ok=True)

    # Input and output file paths (modify as needed)
    csv1_path = '/home/gerald8525/repositories/text2pydough/workbench/lcar_lab/labeling_agent/evaluator_agent_improvement/results/gemini_2.5_flash/iteration_2/20250604_075548/results.csv'
    csv2_path = '/home/gerald8525/repositories/text2pydough/workbench/lcar_lab/labeling_agent/evaluator_agent_improvement/results/claud_4.0_soonet/iteration_2/20250603_155319/results.csv'
    output_true = os.path.join(merged_dir, 'result_match_true.csv')
    output_false = os.path.join(merged_dir, 'result_match_false.csv')
    metadata_path = os.path.join(merged_dir, 'merge_metadata.json')

    process_csv(csv1_path, csv2_path, output_true, output_false, metadata_path)

if __name__ == "__main__":
    main()
