import pandas as pd
import argparse

def analyze_dataset(file_path, output_path):
    """Analyze the dataset and generate metrics."""
    df = pd.read_csv(file_path)

    # Lists to hold the results for saving to CSV
    database_counts_list = []
    difficulty_counts_list = []
    complexity_counts_list = []
    db_difficulty_counts_list = []
    db_complexity_counts_list = []
    combo_counts_list = []

    # Print Dataset Information
    print("///////////////////////////////////////////////////////////////////////////////////")
    print("Let´s see the Dataset information:")
    df.info()

    print("///////////////////////////////////////////////////////////////////////////////////")
    print("First look what datasets we have:")
    print(df['dataset_name'].value_counts())
    print("Let´s analyze every dataset")

    for dataset_name in df['dataset_name'].unique():
        sub_df = df[df['dataset_name'] == dataset_name]
        print(f"================= Analysis for dataset_name: {dataset_name} =================")
        
        # Database counts
        print("\nHow much databases we have in the dataset, and how much queries there are for each database:")
        db_counts = sub_df['db_name'].value_counts()
        print(db_counts)
        db_counts_df = db_counts.reset_index()
        db_counts_df.columns = ['db_name', 'count']
        db_counts_df['dataset_name'] = dataset_name
        database_counts_list.append(db_counts_df)
        
        # Difficulty counts
        print("\nHow much queries there are for each difficulty level:")
        difficulty_counts = sub_df['difficulty'].value_counts()
        print(difficulty_counts)
        difficulty_counts_df = difficulty_counts.reset_index()
        difficulty_counts_df.columns = ['difficulty', 'count']
        difficulty_counts_df['dataset_name'] = dataset_name
        difficulty_counts_list.append(difficulty_counts_df)
        
        # Complexity counts
        print("\nHow much queries there are for each complexity level:")
        complexity_counts = sub_df['complexity'].value_counts()
        print(complexity_counts)
        complexity_counts_df = complexity_counts.reset_index()
        complexity_counts_df.columns = ['complexity', 'count']
        complexity_counts_df['dataset_name'] = dataset_name
        complexity_counts_list.append(complexity_counts_df)
        
        # Groupby database and difficulty
        print("\nMake a groupby to see the relation between database and difficulty level:")
        db_difficulty_counts = sub_df.groupby(['db_name', 'difficulty']).size().reset_index(name='count')
        print(db_difficulty_counts.sort_values('count', ascending=False))
        db_difficulty_counts['dataset_name'] = dataset_name
        db_difficulty_counts_list.append(db_difficulty_counts)
        
        # Groupby database and complexity
        print("\nMake a groupby to see the relation between database and complexity level:")
        db_complexity_counts = sub_df.groupby(['db_name', 'complexity']).size().reset_index(name='count')
        print(db_complexity_counts.sort_values('count', ascending=False))
        db_complexity_counts['dataset_name'] = dataset_name
        db_complexity_counts_list.append(db_complexity_counts)
        
        # Groupby database, difficulty, and complexity
        print("\nMake a groupby to see how many queries there are for each combination of database, difficulty and complexity:")
        combo_counts = sub_df.groupby(['db_name', 'difficulty', 'complexity']).size().reset_index(name='count')
        print(combo_counts.sort_values('count', ascending=False))
        combo_counts['dataset_name'] = dataset_name
        combo_counts_list.append(combo_counts)
        print("=================================================================================")

    # Combine and save to CSV
    database_counts_df = pd.concat(database_counts_list)
    difficulty_counts_df = pd.concat(difficulty_counts_list)
    complexity_counts_df = pd.concat(complexity_counts_list)
    db_difficulty_counts_df = pd.concat(db_difficulty_counts_list)
    db_complexity_counts_df = pd.concat(db_complexity_counts_list)
    combo_counts_df = pd.concat(combo_counts_list)

    # Save each to a CSV file
    database_counts_df.to_csv(f"{output_path}/database_counts.csv", index=False)
    difficulty_counts_df.to_csv(f"{output_path}/difficulty_counts.csv", index=False)
    complexity_counts_df.to_csv(f"{output_path}/complexity_counts.csv", index=False)
    db_difficulty_counts_df.to_csv(f"{output_path}/db_difficulty_counts.csv", index=False)
    db_complexity_counts_df.to_csv(f"{output_path}/db_complexity_counts.csv", index=False)
    combo_counts_df.to_csv(f"{output_path}/combo_counts.csv", index=False)

    print("CSV files created successfully!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Analyze dataset and generate metrics.")
    parser.add_argument('--input_path')
    parser.add_argument('--output_path')
    args = parser.parse_args()

    analyze_dataset(args.input_path, args.output_path)

