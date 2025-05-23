import argparse
import pandas as pd

# Read CSV file
def load_csv(file_path):
    df = pd.read_csv(file_path)
    return df

# Filter the DataFrame for False values (data outside of the training set)
def filter_dataframe(df):
    filtered_df = df[(df['dataframe_match'] == True)]
    return filtered_df

# Get unique values for db_name, difficulty, and complexity
def get_relevant_dbs(filtered_df):
    # Filter by dataset name
    spider_df = filtered_df[filtered_df['dataset_name'] == 'spider_data']
    kaggle_df = filtered_df[filtered_df['dataset_name'] == 'kaggleDBQA']

    # Count occurrences of each db_name
    spider_counts = spider_df['db_name'].value_counts()
    kaggle_counts = kaggle_df['db_name'].value_counts()

    # Select the top 80% based on count
    spider_num = int(len(spider_counts) * 0.8)
    kaggle_num = int(len(kaggle_counts) * 0.8)

    spider_dbs = spider_counts.nlargest(spider_num).index.tolist()
    kaggle_dbs = kaggle_counts.nlargest(kaggle_num).index.tolist()

    # Combine the two lists
    unique_db_names = list(set(spider_dbs) | set(kaggle_dbs))

    return unique_db_names

# Function to create a testing dataset
def create_testing_dataset(df, unique_db_names, training_df_len):
    # Calculate target size for the testing dataset (10% of training size)
    test_size = int(training_df_len * 0.1)

    # Filter the DataFrame for unmatched rows
    filtered_test_df = df[(df['dataframe_match'] == False)]

    # Calculate proportional distribution for `difficulty` and `complexity`
    difficulty_proportions = filtered_test_df['difficulty'].value_counts(normalize=True).to_dict()
    complexity_proportions = filtered_test_df['complexity'].value_counts(normalize=True).to_dict()

    # Create the testing dataset by sampling
    testing_dataset = []

    for difficulty, difficulty_proportion in difficulty_proportions.items():
        # Calculate the target number of rows for this difficulty
        rows_for_difficulty = int(test_size * difficulty_proportion)

        # Filter rows matching the difficulty and valid conditions
        difficulty_subset = filtered_test_df[
            (filtered_test_df['difficulty'] == difficulty) &
            (filtered_test_df['db_name'].isin(unique_db_names))
        ]

        for complexity, complexity_proportion in complexity_proportions.items():
            # Calculate the target number of rows for this difficulty and complexity
            rows_for_complexity = int(rows_for_difficulty * complexity_proportion)

            # Filter rows matching this complexity
            complexity_subset = difficulty_subset[difficulty_subset['complexity'] == complexity]

            # Sample rows and append to the result
            sampled_rows = complexity_subset.sample(
                n=min(rows_for_complexity, len(complexity_subset)),
                random_state=42
            )
            testing_dataset.append(sampled_rows)

    # Combine all sampled rows into a single DataFrame
    testing_dataset = pd.concat(testing_dataset, ignore_index=True)

    # Adjust to ensure the testing dataset matches the desired test_size
    if len(testing_dataset) < test_size:
        # Calculate the deficit
        deficit = test_size - len(testing_dataset)

        # Sample additional rows from unmatched data without constraints
        additional_rows = filtered_test_df[
            ~(filtered_test_df.index.isin(testing_dataset.index))
        ].sample(n=min(deficit, len(filtered_test_df)), random_state=42)

        # Add the additional rows
        testing_dataset = pd.concat([testing_dataset, additional_rows], ignore_index=True)

    # Final adjustment to ensure the exact size
    if len(testing_dataset) > test_size:
        testing_dataset = testing_dataset.sample(n=test_size, random_state=42)

    return testing_dataset

# Save the DataFrame to a CSV file
def save_to_csv(df, output_path):
    reformatted_questions = df[['question', 'ground_truth_sql', 'dataset_name', 'db_name']] \
        .rename(columns={'ground_truth_sql': 'sql'}) \
        .to_dict(orient='records')
        
    final_csv = pd.DataFrame(reformatted_questions)

    final_csv.to_csv(output_path, index=False)

# Example usage
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_csv')
    parser.add_argument('output_csv')
    args = parser.parse_args()

    df = load_csv(args.input_csv)

    filtered_df = filter_dataframe(df)
    dbs_list = get_relevant_dbs(filtered_df)

    testing_dataset = create_testing_dataset(df, dbs_list, len(filtered_df))
    save_to_csv(testing_dataset, args.output_csv)