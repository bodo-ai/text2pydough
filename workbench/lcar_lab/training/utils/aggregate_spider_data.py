import os
import pandas as pd
from pathlib import Path
import json

def aggregate_csv_files(input_dir, output_dir):
    # Convert paths to Path objects
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Debug information
    print(f"Input directory: {input_path}")
    print(f"Input directory exists: {input_path.exists()}")
    if input_path.exists():
        print(f"Input directory contents: {os.listdir(input_path)}")
    else:
        # Try WSL path if Windows path doesn't exist
        wsl_input_path = Path("/mnt/c/Users/david/bodo/text2pydough/training/training_data/labeled_data/spider/raw")
        print(f"\nTrying WSL path: {wsl_input_path}")
        print(f"WSL path exists: {wsl_input_path.exists()}")
        if wsl_input_path.exists():
            print(f"WSL directory contents: {os.listdir(wsl_input_path)}")
            input_path = wsl_input_path
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize an empty list to store all dataframes
    all_data = []
    
    # Get all CSV files in the input directory
    csv_files = list(input_path.glob('*.csv'))
    print(f"Found {len(csv_files)} CSV files to process")
    
    if not csv_files:
        print("No CSV files found. Checking for other file types...")
        all_files = list(input_path.glob('*'))
        print(f"All files in directory: {[f.name for f in all_files]}")
        return
    
    # Read and combine all CSV files
    for csv_file in csv_files:
        print(f"Processing {csv_file.name}")
        try:
            df = pd.read_csv(csv_file)
            print(f"Columns in {csv_file.name}: {df.columns.tolist()}")
            all_data.append(df)
        except Exception as e:
            print(f"Error processing {csv_file.name}: {str(e)}")
    
    if not all_data:
        print("No data was successfully loaded")
        return
    
    # Combine all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Save the combined dataframe
    output_file = output_path / 'combined_spider_data.csv'
    combined_df.to_csv(output_file, index=False)
    print(f"Combined data saved to {output_file}")
    
    # Print available columns
    print("\nAvailable columns in combined data:")
    print(combined_df.columns.tolist())
    
    # Compute statistics based on available columns
    stats = {
        'total_records': len(combined_df),
        'columns': combined_df.columns.tolist()
    }
    
    # Add dataframe_match statistics if column exists
    if 'dataframe_match' in combined_df.columns:
        stats['dataframe_match_counts'] = combined_df['dataframe_match'].value_counts().to_dict()
    
    # Add class distribution if column exists
    if 'class' in combined_df.columns:
        stats['class_distribution'] = combined_df['class'].value_counts().to_dict()
        if 'dataframe_match' in combined_df.columns:
            stats['dataframe_match_by_class'] = combined_df.groupby('class')['dataframe_match'].value_counts().to_dict()
    
    # Save statistics to JSON
    stats_file = output_path / 'spider_data_statistics.json'
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"Statistics saved to {stats_file}")
    
    # Print summary
    print("\nSummary Statistics:")
    print(f"Total records: {stats['total_records']}")
    
    if 'dataframe_match_counts' in stats:
        print("\nDataframe Match Distribution:")
        for value, count in stats['dataframe_match_counts'].items():
            print(f"  {value}: {count} ({count/stats['total_records']*100:.2f}%)")
    
    if 'class_distribution' in stats:
        print("\nClass Distribution:")
        for class_name, count in stats['class_distribution'].items():
            print(f"  {class_name}: {count} ({count/stats['total_records']*100:.2f}%)")

if __name__ == "__main__":
    # Define paths - try both Windows and WSL paths
    input_dir = r"/mnt/c/Users/david/bodo/text2pydough/training/training_data/labeled_data/spider/raw"
    output_dir = r"/mnt/c/Users/david/bodo/text2pydough/training/training_data/labeled_data/spider/processed"
    
    # Run the aggregation
    aggregate_csv_files(input_dir, output_dir) 