import pandas as pd
import os
from pathlib import Path

def create_subdataset(input_csv: str, output_csv: str):
    """
    Creates a sub-dataset of the first 200 rows where `dataframe_match` is False.
    
    :param input_csv: Path to the input CSV file.
    :param output_csv: Path to save the output CSV file.
    """
    try:
        # Read the input CSV file
        df = pd.read_csv(input_csv)
        
        # Filter the first 200 rows where `dataframe_match` is False
        filtered_df = df[df['dataframe_match'] == False].head(200)
        
        # Save the filtered data to a new CSV file
        filtered_df.to_csv(output_csv, index=False)
        
        print(f"Sub-dataset created successfully and saved to {output_csv}")
    except FileNotFoundError:
        print(f"Error: File {input_csv} not found. Please check the path.")
    except KeyError:
        print("Error: The column `dataframe_match` is not found in the CSV file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Define input and output paths
    input_file_path = '/home/gerald8525/repositories/text2pydough/workbench/lcar_lab/training/training_data/labeled_data/spider/training_ready/training_data_with_schema_20250513_133702_spider.csv'
    output_file_path = '/home/gerald8525/repositories/text2pydough/workbench/lcar_lab/labeling_agent/evaluator_agent_improvement/200_testing_dataset.csv'
    
    # Call the function
    create_subdataset(input_file_path, output_file_path)
