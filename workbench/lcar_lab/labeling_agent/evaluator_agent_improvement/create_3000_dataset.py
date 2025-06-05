import pandas as pd
import os
import sys

def filter_data(training_csv_path=str, golden_csv_path=str, testing_dataset_path=str, validation_dataset_path=str, new_tuning_dataset_path=str):

    training_df = pd.read_csv(training_csv_path)
    golden_df = pd.read_csv(golden_csv_path)
    testing_df = pd.read_csv(testing_dataset_path)
    validation_df = pd.read_csv(validation_dataset_path)
    new_tuning_dataset_path = pd.read_csv(new_tuning_dataset_path)

    # Step 1: Filter rows where dataframe_match is False
    print("Filtering out rows where 'dataframe_match' is False (out of training data)...")
    filtered_training_df = training_df[training_df['dataframe_match'] == False]

    # Step 2: Filter out rows where 'question' exists in either golden_csv or testing_dataset
    print("Filtering out questions from golden dataset, testing dataset, validation dataset, and new tuning dataset...")
    golden_questions = set(golden_df['question'])
    testing_questions = set(testing_df['question'])
    validation_questions = set(validation_df['question'])
    new_tuning_questions = set(new_tuning_dataset_path['question'])

    final_filtered_df = filtered_training_df[~filtered_training_df['question'].isin(golden_questions | testing_questions | validation_questions | new_tuning_questions)]

    # Step 3: Filter rows where 'difficulty' column has the value 'extra'
    print("Filtering rows with 'difficulty' value as 'extra/medium/hard'...")
    final_filtered_df = final_filtered_df[final_filtered_df['difficulty'].isin(['medium', 'hard', 'extra'])]
    print(f"Filtered DataFrame shape: {final_filtered_df.shape}")

    # Return the final filtered DataFrame
    return final_filtered_df

if __name__ == "__main__":
    # Load the CSV files
    training_csv_path = "/home/gerald8525/repositories/mount-folder/datasets/Finetuning/labeling/labeled_data/spider_kaggle_data/spider_kaggle_full_sql_checked.csv"
    golden_csv_path = "/home/gerald8525/repositories/mount-folder/datasets/Finetuning/labeling/validation_dataset/golden_dataset_sql_checked.csv"
    testing_dataset_path = "/home/gerald8525/repositories/mount-folder/datasets/Finetuning/labeling/validation_dataset/testing_dataset.csv"
    validation_dataset_path = "/home/gerald8525/repositories/mount-folder/datasets/Finetuning/labeling/validation_dataset/validation_dataset_30.csv"
    new_tuning_dataset_path = "/home/gerald8525/repositories/text2pydough/workbench/lcar_lab/labeling_agent/evaluator_agent_improvement/new_tuning_dataset.csv"

    # Filter the data
    filtered_df = filter_data(training_csv_path, golden_csv_path, testing_dataset_path, validation_dataset_path, new_tuning_dataset_path)

    # Save to CSV
    filtered_df.to_csv("3000_dataset.csv", index=False)