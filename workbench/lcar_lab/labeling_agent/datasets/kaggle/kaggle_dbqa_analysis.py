# KaggleDBQA Dataset Analysis
# This script can be converted to a Jupyter notebook

import sys
import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Add the current directory to the Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Import our processor
from process_kaggle_dbqa import KaggleDBQAProcessor

# Initialize the processor
print("Initializing processor...")
processor = KaggleDBQAProcessor()

# Get available datasets
print("\nGetting available datasets...")
available_datasets = processor.get_available_datasets()
print("Available datasets:", available_datasets)

# Load and explore a specific dataset
print("\nLoading WorldSoccerDataBase dataset...")
dataset_name = "WorldSoccerDataBase"
df = processor.load_dataset(dataset_name)

# Display basic information
print(f"\nDataset: {dataset_name}")
print(f"Number of queries: {len(df)}")
print("\nColumns:", df.columns.tolist())
print("\nFirst few rows:")
print(df.head())

# Analyze query patterns
print("\nAnalyzing query patterns...")
df['query_length'] = df['query'].str.len()
print("\nQuery length statistics:")
print(df['query_length'].describe())

# Plot query length distribution
plt.figure(figsize=(10, 6))
sns.histplot(data=df, x='query_length', bins=30)
plt.title('Distribution of Query Lengths')
plt.xlabel('Query Length')
plt.ylabel('Count')
plt.savefig(current_dir / 'query_length_distribution.png')
plt.close()

# Compare different splits
print("\nComparing dataset splits...")
main_df = processor.load_dataset(dataset_name)
test_df = processor.load_dataset(dataset_name, split="test")
fewshot_df = processor.load_dataset(dataset_name, split="fewshot")

print(f"\nMain dataset size: {len(main_df)} queries")
print(f"Test dataset size: {len(test_df)} queries")
print(f"Few-shot dataset size: {len(fewshot_df)} queries")

print("\nAverage query lengths:")
print(f"Main: {main_df['query'].str.len().mean():.2f} characters")
print(f"Test: {test_df['query'].str.len().mean():.2f} characters")
print(f"Few-shot: {fewshot_df['query'].str.len().mean():.2f} characters")

# Example queries
print("\nExample queries from each split:")
print("\nMain dataset example:")
print(main_df['query'].iloc[0])
print("\nTest dataset example:")
print(test_df['query'].iloc[0])
print("\nFew-shot dataset example:")
print(fewshot_df['query'].iloc[0])

# Load all datasets
print("\nLoading all datasets...")
all_datasets = processor.load_all_datasets()

# Create summary
summary_data = []
for name, df in all_datasets.items():
    summary_data.append({
        'Dataset': name,
        'Number of Queries': len(df),
        'Average Query Length': df['query'].str.len().mean(),
        'Unique DB IDs': len(df['db_id'].unique())
    })

summary_df = pd.DataFrame(summary_data)
print("\nDataset Summary:")
print(summary_df)

# Save the summary
summary_df.to_csv(current_dir / 'dataset_summary.csv', index=False)
print(f"\nSummary saved to {current_dir / 'dataset_summary.csv'}") 