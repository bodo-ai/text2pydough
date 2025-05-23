import json
import pandas as pd
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

class KaggleDBQAProcessor:
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize the processor with the path to the KaggleDBQA dataset.
        
        Args:
            base_path: Optional path to the KaggleDBQA dataset. If None, will look in:
                      - Current directory
                      - Parent directory
                      - labeling_agent/datasets/kaggle directory
        """
        if base_path is None:
            # Try to find the dataset in common locations
            possible_paths = [
                Path("."),  # Current directory
                Path("KaggleDBQA"),
                Path("../KaggleDBQA"),
                Path("../../KaggleDBQA"),
                Path("labeling_agent/datasets/kaggle/KaggleDBQA"),
                Path(__file__).parent / "KaggleDBQA",
                Path(__file__).parent  # Current script directory
            ]
            
            for path in possible_paths:
                if path.exists():
                    # Check if this is a directory with JSON files
                    if path.is_dir():
                        json_files = list(path.glob("*.json"))
                        if json_files:
                            self.base_path = path
                            self.examples_path = path
                            break
                    # Check if this is a directory containing an examples subdirectory
                    elif (path / "examples").exists():
                        self.base_path = path
                        self.examples_path = path / "examples"
                        break
            else:
                raise FileNotFoundError(
                    "Could not find KaggleDBQA dataset. Please specify the path manually."
                )
        else:
            self.base_path = Path(base_path)
            self.examples_path = self.base_path / "examples" if (self.base_path / "examples").exists() else self.base_path
        
    def load_json_file(self, file_path: Union[str, Path]) -> List[Dict]:
        """Load a single JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_available_datasets(self) -> List[str]:
        """Get list of available datasets."""
        files = os.listdir(self.examples_path)
        # Get unique dataset names (removing _test.json and _fewshot.json)
        datasets = set(f.replace('_test.json', '').replace('_fewshot.json', '').replace('.json', '') 
                      for f in files if f.endswith('.json'))
        return sorted(list(datasets))
    
    def load_dataset(self, dataset_name: str, split: Optional[str] = None) -> pd.DataFrame:
        """
        Load a specific dataset into a DataFrame.
        
        Args:
            dataset_name: Name of the dataset (e.g., 'WorldSoccerDataBase')
            split: Optional split to load ('test' or 'fewshot'). If None, loads the main dataset.
        
        Returns:
            pd.DataFrame: DataFrame containing the dataset
        """
        if split:
            file_name = f"{dataset_name}_{split}.json"
        else:
            file_name = f"{dataset_name}.json"
            
        file_path = self.examples_path / file_name
        if not file_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {file_path}")
            
        data = self.load_json_file(file_path)
        
        # Convert to DataFrame
        # The JSON structure is a list of query objects
        df = pd.DataFrame(data)
        
        # Add metadata about the source
        df['source_file'] = file_name
        df['split'] = split if split else 'main'
        df['dataset_name'] = dataset_name
        
        return df
    
    def load_all_datasets(self, split: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Load all available datasets.
        
        Args:
            split: Optional split to load ('test' or 'fewshot'). If None, loads the main datasets.
        
        Returns:
            Dict[str, pd.DataFrame]: Dictionary mapping dataset names to their DataFrames
        """
        datasets = self.get_available_datasets()
        result = {}
        
        for dataset in datasets:
            try:
                result[dataset] = self.load_dataset(dataset, split)
            except Exception as e:
                print(f"Error loading dataset {dataset}: {str(e)}")
                
        return result
    
    def get_dataset_info(self, df: pd.DataFrame) -> Dict:
        """Get basic information about a loaded dataset."""
        return {
            'num_queries': len(df),
            'columns': list(df.columns),
            'db_ids': df['db_id'].unique().tolist(),
            'example_query': df['query'].iloc[0] if len(df) > 0 else None
        }
    
    def aggregate_all_datasets(self, include_splits: bool = True) -> pd.DataFrame:
        """
        Aggregate all datasets into a single DataFrame.
        
        Args:
            include_splits: If True, includes test and few-shot splits. If False, only includes main datasets.
        
        Returns:
            pd.DataFrame: Combined DataFrame containing all datasets
        """
        all_dataframes = []
        
        if include_splits:
            # Load all splits for each dataset
            for dataset_name in self.get_available_datasets():
                try:
                    # Load main dataset
                    main_df = self.load_dataset(dataset_name)
                    all_dataframes.append(main_df)
                    
                    # Load test split if available
                    try:
                        test_df = self.load_dataset(dataset_name, split="test")
                        all_dataframes.append(test_df)
                    except FileNotFoundError:
                        pass
                    
                    # Load few-shot split if available
                    try:
                        fewshot_df = self.load_dataset(dataset_name, split="fewshot")
                        all_dataframes.append(fewshot_df)
                    except FileNotFoundError:
                        pass
                except Exception as e:
                    print(f"Error processing dataset {dataset_name}: {str(e)}")
        else:
            # Load only main datasets
            all_dataframes = [self.load_dataset(dataset) 
                            for dataset in self.get_available_datasets()]
        
        # Combine all DataFrames
        if all_dataframes:
            combined_df = pd.concat(all_dataframes, ignore_index=True)
            
            # Add a unique identifier for each query
            combined_df['query_id'] = range(1, len(combined_df) + 1)
            
            return combined_df
        else:
            return pd.DataFrame()
    
    def get_aggregated_stats(self, df: pd.DataFrame) -> Dict:
        """
        Get statistics about the aggregated dataset.
        
        Args:
            df: The aggregated DataFrame
            
        Returns:
            Dict: Statistics about the aggregated dataset
        """
        if df.empty:
            return {}
            
        stats = {
            'total_queries': len(df),
            'unique_datasets': df['dataset_name'].nunique(),
            'splits_present': df['split'].unique().tolist(),
            'queries_per_dataset': df.groupby('dataset_name').size().to_dict(),
            'queries_per_split': df.groupby('split').size().to_dict(),
            'unique_db_ids': df['db_id'].nunique(),
            'avg_query_length': df['query'].str.len().mean(),
            'max_query_length': df['query'].str.len().max(),
            'min_query_length': df['query'].str.len().min()
        }
        
        return stats

# Example usage
if __name__ == "__main__":
    # Try to find the dataset automatically
    processor = KaggleDBQAProcessor(base_path="/mnt/c/Users/david/bodo/KaggleDBQA")
    
    # Get available datasets
    available_datasets = processor.get_available_datasets()
    print("Available datasets:", available_datasets)
    
    # Aggregate all datasets
    print("\nAggregating all datasets...")
    combined_df = processor.aggregate_all_datasets()
    
    # Get statistics about the aggregated dataset
    stats = processor.get_aggregated_stats(combined_df)
    print("\nAggregated Dataset Statistics:")
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Save the aggregated dataset
    output_path = Path(__file__).parent / "kaggle_dbqa_combined.csv"
    combined_df.to_csv(output_path, index=False)
    print(f"\nAggregated dataset saved to {output_path}") 