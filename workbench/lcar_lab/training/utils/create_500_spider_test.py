import pandas as pd

# Read CSV file
def load_csv(file_path):
    df = pd.read_csv(file_path)
    return df

# Function to filter the DataFrame for True values (training data)
def filter_dataframe(df):
    filtered_df = df[(df['dataframe_match'] == True) & (df['dataset_name'] == 'spider_data')]
    return filtered_df

# Get unique values for db_name, difficulty, and complexity
def get_unique_values(filtered_df):
    unique_db_names = filtered_df['db_name'].unique()
    unique_difficulties = filtered_df['difficulty'].unique()
    unique_complexities = filtered_df['complexity'].unique()
    return unique_db_names, unique_difficulties, unique_complexities

# Create a DataFrame with 500 rows for the spider test
def create_500_spider_test(df, unique_db_names, unique_difficulties, unique_complexities):
    # Filtrar por condiciones iniciales
    spider_test_df = df[(df['dataframe_match'] == False) & (df['dataset_name'] == 'spider_data')]

    # Aply filtering conditions
    filtered_spider_test = spider_test_df[
        (spider_test_df['db_name'].isin(unique_db_names)) &
        (spider_test_df['difficulty'].isin(unique_difficulties)) &
        (spider_test_df['complexity'].isin(unique_complexities))
    ]

    # Select 500 random rows
    selected_rows = filtered_spider_test.sample(n=min(500, len(filtered_spider_test)), random_state=42)
    return selected_rows

# Save the DataFrame to a CSV file
def save_to_csv(df, output_path):
    reformatted_questions = df[['question', 'ground_truth_sql', 'dataset_name', 'db_name']] \
        .rename(columns={'ground_truth_sql': 'sql'}) \
        .to_dict(orient='records')
        
    final_csv = pd.DataFrame(reformatted_questions)

    final_csv.to_csv(output_path, index=False)

# Example usage
file_path = '/home/gerald8525/repositories/mount-folder/datasets/Finetuning/labeling/labeled_data/spider/training_ready/labeled_training_data_with_schema_133702.csv'
output_path = '/home/gerald8525/repositories/output.csv'
df = load_csv(file_path)

filtered_df = filter_dataframe(df)
unique_db_names, unique_difficulties, unique_complexities = get_unique_values(filtered_df)
print(f"Unique DB names: {unique_db_names}")
print(f"Unique difficulties: {unique_difficulties}")    
print(f"Unique complexities: {unique_complexities}")

spider_test_df = create_500_spider_test(df, unique_db_names, unique_difficulties, unique_complexities)
save_to_csv(spider_test_df, output_path)