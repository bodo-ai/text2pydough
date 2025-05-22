import pandas as pd
from query_classification import clasificate_queries

# File paths
spider_path = '/home/gerald8525/repositories/mount-folder/datasets/Finetuning/labeling/labeled_data/spider/training_ready/labeled_training_data_with_schema_133702.csv'
kaggledbqa_path = '/home/gerald8525/repositories/mount-folder/datasets/Finetuning/labeling/labeled_data/kaggledbqa/training_ready/training_data_with_schema_20250512_155042.csv'

output_path = '/home/gerald8525/repositories/mount-folder/datasets/Finetuning/labeling/labeled_data/spider_kaggle_data/spider_kaggle_full.csv'

spider_df = pd.read_csv(spider_path)
kaggle_df = pd.read_csv(kaggledbqa_path)
    
spider_df = spider_df[spider_df['dataframe_match'] == True]
kaggle_df = kaggle_df[kaggle_df['dataframe_match'] == True]

# Replace 'sql' with 'ground_truth_sql' in both DataFrames
if 'sql' in spider_df.columns:
    spider_df = spider_df.rename(columns={'sql': 'ground_truth_sql'})
if 'sql' in kaggle_df.columns:
    kaggle_df = kaggle_df.rename(columns={'sql': 'ground_truth_sql'})

# Classify queries in both datasets
spider_df = clasificate_queries(spider_df)
kaggle_df = clasificate_queries(kaggle_df)

# Combine the filtered and classified data
combined_df = pd.concat([spider_df, kaggle_df], ignore_index=True)

# Save the combined data to the output file
combined_df.to_csv(output_path, index=False)

print(f"Combined CSV saved to {output_path}")
