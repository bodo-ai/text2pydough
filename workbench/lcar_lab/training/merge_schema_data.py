import os
import pandas as pd
import json
from pathlib import Path
from datetime import datetime

def print_database_stats(df, title, id_col='db_name'):
    """Print statistics about database names in the DataFrame."""
    print(f"\n{title}:")
    stats = df[id_col].value_counts()
    total = len(df)
    print(f"Total records: {total}")
    print("\nDatabase distribution:")
    for db_name, count in stats.items():
        percentage = (count / total) * 100
        print(f"  {db_name}: {count} records ({percentage:.2f}%)")

def load_questions_data(questions_path):
    """Load the questions data that maps question IDs to database names."""
    df = pd.read_csv(questions_path)
    print(f"\nQuestions data columns: {df.columns.tolist()}")
    return df

def load_schema_data(schema_dir, db_name):
    """Load the schema data for a specific database."""
    schema_file = schema_dir / f"{db_name}_graph.json"
    if not schema_file.exists():
        print(f"Warning: Schema file not found for {db_name}")
        return None
    try:
        with open(schema_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading schema for {db_name}: {str(e)}")
        return None

def merge_schema_with_data(processed_data, questions_data, schema_dir, output_dir):
    """Merge schema data with processed data based on question IDs."""
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Print column information
    print("\nProcessed data columns:", processed_data.columns.tolist())
    print("Questions data columns:", questions_data.columns.tolist())
    
    # Map column names
    question_id_col = 'question_id'  # Column in processed data
    questions_id_col = 'query_id'    # Column in questions data
    db_name_col = 'db_name'          # Column in questions data
    
    # Verify required columns exist
    if question_id_col not in processed_data.columns:
        print(f"Error: Column '{question_id_col}' not found in processed data")
        print("Available columns:", processed_data.columns.tolist())
        return None
    
    if questions_id_col not in questions_data.columns:
        print(f"Error: Column '{questions_id_col}' not found in questions data")
        print("Available columns:", questions_data.columns.tolist())
        return None
    
    if db_name_col not in questions_data.columns:
        print(f"Error: Column '{db_name_col}' not found in questions data")
        print("Available columns:", questions_data.columns.tolist())
        return None
    
    # Print initial database statistics
    print_database_stats(questions_data, "Initial Database Distribution in Questions Data", db_name_col)
    
    # Initialize list to store merged data
    merged_data = []
    
    # Process each row in the processed data
    for _, row in processed_data.iterrows():
        # Get the question ID from the row
        question_id = row.get(question_id_col)
        if not question_id:
            print(f"Warning: No question ID found in row")
            continue
            
        # Find the corresponding database name from questions data
        db_info = questions_data[questions_data[questions_id_col] == question_id]
        if db_info.empty:
            print(f"Warning: No database found for question_id {question_id}")
            continue
            
        db_name = db_info[db_name_col].iloc[0]
        
        # Load the schema data
        schema_data = load_schema_data(schema_dir, db_name)
        if not schema_data:
            continue
            
        # Create a new row with schema data
        new_row = row.copy()
        new_row['database_schema'] = json.dumps(schema_data)
        new_row['db_name'] = db_name
        merged_data.append(new_row)
    
    # Convert to DataFrame
    merged_df = pd.DataFrame(merged_data)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Save the merged data
    output_file = output_dir / f'training_data_with_schema_{timestamp}.csv'
    merged_df.to_csv(output_file, index=False)
    print(f"Merged data saved to {output_file}")
    
    # Print final database statistics
    print_database_stats(merged_df, "Final Database Distribution in Merged Data")
    
    # Print merge statistics
    print("\nMerge Statistics:")
    print(f"Total records processed: {len(processed_data)}")
    print(f"Successfully merged records: {len(merged_df)}")
    print(f"Success rate: {len(merged_df)/len(processed_data)*100:.2f}%")
    
    return merged_df

def main():
    DATASET = "spider"
    # Define paths
    base_path = Path("/home/arami/bodo/text2pydough/workbench/lcar_lab/training/training_data/labeled_data/" + DATASET)
    
    processed_data_path = base_path / "processed" / (DATASET + "_without_schema_20250513_085755.csv")
    questions_path = base_path / "questions" / (DATASET + "_data_full.csv")
    schema_dir = base_path / "metadata"
    output_dir = base_path / "training_ready"
    
    # Load the processed data
    print("Loading processed data...")
    processed_data = pd.read_csv(processed_data_path)
    
    # Load the questions data
    print("Loading questions data...")
    questions_data = load_questions_data(questions_path)
    
    # Merge schema data
    print("Merging schema data...")
    merged_data = merge_schema_with_data(processed_data, questions_data, schema_dir, output_dir)
    
    if merged_data is not None:
        # Print column information
        print("\nColumns in merged data:")
        print(merged_data.columns.tolist())

if __name__ == "__main__":
    main() 