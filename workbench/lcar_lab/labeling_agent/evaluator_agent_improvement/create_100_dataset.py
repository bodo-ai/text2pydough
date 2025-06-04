import pandas as pd
import os
import sys

def filter_data(training_csv_path=str, golden_csv_path=str, testing_dataset_path=str, validation_dataset_path=str):

    training_df = pd.read_csv(training_csv_path)
    golden_df = pd.read_csv(golden_csv_path)
    testing_df = pd.read_csv(testing_dataset_path)
    validation_df = pd.read_csv(validation_dataset_path)

    # Step 1: Filter rows where dataframe_match is False
    print("Filtering out rows where 'dataframe_match' is False (out of training data)...")
    filtered_training_df = training_df[training_df['dataframe_match'] == False]

    # Step 2: Filter out rows where 'question' exists in either golden_csv or testing_dataset
    golden_questions = set(golden_df['question'])
    testing_questions = set(testing_df['question'])
    validation_questions = set(validation_df['question'])

    print("Filtering out questions from golden dataset, testing dataset, and validation dataset...")
    final_filtered_df = filtered_training_df[
        ~filtered_training_df['question'].isin(golden_questions | testing_questions | validation_questions)
    ]

    # Step 3: Filter rows where 'difficulty' column has the value 'medium' or 'hard'
    print("Filtering rows with 'difficulty' value as 'medium' or 'hard'...")
    final_filtered_df = final_filtered_df[final_filtered_df['difficulty'].isin(['medium', 'hard'])]
    print(f"Filtered DataFrame shape: {final_filtered_df.shape}")

    # Return the final filtered DataFrame
    return final_filtered_df

def select_proportional_samples(filtered_df, total_samples):
    # Calculate representation proportions for dataset_name
    dataset_counts = filtered_df['dataset_name'].value_counts()
    print(f"Dataset counts:\n{dataset_counts}")

    dataset_proportions = dataset_counts / dataset_counts.sum()

    # Determine sample count for each dataset
    samples_per_dataset = (dataset_proportions * total_samples).round().astype(int)
    print(f"Samples per dataset:\n{samples_per_dataset}")

    # Select proportional samples per dataset and difficulty
    sampled_df_list = []
    for dataset, dataset_sample_count in samples_per_dataset.items():
        dataset_subset = filtered_df[filtered_df['dataset_name'] == dataset]

        # Calculate representation proportions for difficulty within the dataset
        difficulty_counts = dataset_subset['difficulty'].value_counts()
        difficulty_proportions = difficulty_counts / difficulty_counts.sum()

        # Ensure 50% medium and 50% hard if possible, adjusting as needed
        medium_samples = round(dataset_sample_count * 0.5)
        hard_samples = dataset_sample_count - medium_samples

        difficulty_samples = {
            'medium': min(medium_samples, difficulty_counts.get('medium', 0)),
            'hard': min(hard_samples, difficulty_counts.get('hard', 0))
        }

        print(f"Difficulty samples for dataset '{dataset}':\n{difficulty_samples}")

        # Sample based on difficulty proportions
        for difficulty, sample_count in difficulty_samples.items():
            difficulty_subset = dataset_subset[dataset_subset['difficulty'] == difficulty]
            sampled_subset = difficulty_subset.sample(n=sample_count, random_state=42)  # Ensure reproducibility
            sampled_df_list.append(sampled_subset)

    # Combine the sampled dataframes
    proportional_sampled_df = pd.concat(sampled_df_list, ignore_index=True)
    return proportional_sampled_df

if __name__ == "__main__":
    # Load the CSV files
    training_csv_path = "/home/gerald8525/repositories/mount-folder/datasets/Finetuning/labeling/labeled_data/spider_kaggle_data/spider_kaggle_full_sql_checked.csv"
    golden_csv_path = "/home/gerald8525/repositories/mount-folder/datasets/Finetuning/labeling/validation_dataset/golden_dataset_sql_checked.csv"
    testing_dataset_path = "/home/gerald8525/repositories/mount-folder/datasets/Finetuning/labeling/validation_dataset/testing_dataset.csv"
    validation_dataset_path = "/home/gerald8525/repositories/mount-folder/datasets/Finetuning/labeling/validation_dataset/validation_dataset_30.csv"

    # Filter the data
    filtered_df = filter_data(training_csv_path, golden_csv_path, testing_dataset_path, validation_dataset_path)

    # Select 200 proportional samples
    proportional_sampled_df = select_proportional_samples(filtered_df, total_samples=100)

    # Save to CSV
    proportional_sampled_df.to_csv("100_dataset.csv", index=False)
    print("Proportional samples saved to 'proportional_sampled_data.csv'")