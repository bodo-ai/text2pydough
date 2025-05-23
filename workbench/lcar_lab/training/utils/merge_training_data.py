import pandas as pd
import argparse
from query_classification import clasificate_queries

# Right now we are only using the spider dataset and kaggle dataset, but we can add more datasets in the future
# Add the 'dataframe_match' column filter if you want to only filter the training set

def load_data(spider_path, kaggledbqa_path):
    """Load datasets from the specified paths."""
    spider_df = pd.read_csv(spider_path)
    kaggle_df = pd.read_csv(kaggledbqa_path)
    return spider_df, kaggle_df

def preprocess_data(spider_df, kaggle_df):
    """Preprocess data by renaming columns and filtering queries."""
    # Rename 'sql' to 'ground_truth_sql' if present, this is to unify the column names when combining datasets
    if 'sql' in spider_df.columns:
        spider_df = spider_df.rename(columns={'sql': 'ground_truth_sql'})
    if 'sql' in kaggle_df.columns:
        kaggle_df = kaggle_df.rename(columns={'sql': 'ground_truth_sql'})
    
    # Classify queries in both datasets
    spider_df = clasificate_queries(spider_df)
    kaggle_df = clasificate_queries(kaggle_df)
    return spider_df, kaggle_df

def combine_and_save(spider_df, kaggle_df, output_path):
    """Combine the processed datasets and save to the specified path."""
    combined_df = pd.concat([spider_df, kaggle_df], ignore_index=True)
    combined_df.to_csv(output_path, index=False)
    print(f"Combined CSV saved to {output_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Process and combine datasets.")
    parser.add_argument('spider_path')
    parser.add_argument('kaggledbqa_path')
    parser.add_argument('output_path')
    args = parser.parse_args()

    # Load datasets
    spider_df, kaggle_df = load_data(args.spider_path, args.kaggledbqa_path)
    
    # Preprocess datasets
    spider_df, kaggle_df = preprocess_data(spider_df, kaggle_df)
    
    # Combine and save the final dataset
    combine_and_save(spider_df, kaggle_df, args.output_path)


