import pandas as pd
import os
import hashlib
from pathlib import Path
import fcntl  
import time
from sqlalchemy import create_engine


class SqliteCache:
    
    """ Init example: cache = SqliteCache("./sql_cache", False)"""
    
    def __init__(self, cache_path: str, read_only: bool = False):
        self.cache_path = cache_path
        self.read_only = read_only
        Path(cache_path).mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, database_path: str, sql: str):
        cache_string = f"{database_path}|{sql.strip()}"
        return hashlib.md5(cache_string.encode('utf-8')).hexdigest()
    
    def _get_cache_file(self, cache_key: str):
        return os.path.join(self.cache_path, f"{cache_key}.parquet")
    
    def _save_to_cache(self, cache_key: str, df: pd.DataFrame):
        data_file = self._get_cache_file(cache_key)        
        try:
            with open(data_file + '.lock', 'w') as lock_file:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                df.to_parquet(data_file, index=False)
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        finally:
            lock_file_path = data_file + '.lock'
            if os.path.exists(lock_file_path):
                try:
                    os.remove(lock_file_path)
                except:
                    pass
    
    def _load_from_cache(self, cache_key: str):
        data_file = self._get_cache_file(cache_key)        
        if not os.path.exists(data_file):
            return None            
        try:
            with open(data_file + '.lock', 'w') as lock_file:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_SH)
                df = pd.read_parquet(data_file)
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                return df
        except Exception as e:
            print(f"Error loading from cache: {e}")
            return None
        finally:
            lock_file_path = data_file + '.lock'
            if os.path.exists(lock_file_path):
                try:
                    os.remove(lock_file_path)
                except:
                    pass
    
    def execute(self, database_path: str, sql: str):
       
        cache_key = self._get_cache_key(database_path, sql)        
       
        cached_df = self._load_from_cache(cache_key)
        
        if cached_df is not None:
            print("Cache found for query")
            return cached_df
        
        print(f"Cache not found for query")        
        df, error = convert_sql_to_dataframe(database_path, sql)

        if not self.read_only:
            self._save_to_cache(cache_key, df)
        
        return df
    
    
def convert_sql_to_dataframe(db_path: str, sql_query: str) -> pd.DataFrame:
    """Execute SQL query and return results as DataFrame or None if error."""
    try:
        if not db_path.startswith('sqlite://'):
            db_url = f'sqlite:///{db_path}'
        else:
            db_url = db_path
        engine = create_engine(db_url)    
        df = pd.read_sql_query(sql_query, engine)
        return df      
    except Exception as e:
        df = pd.DataFrame({"Exec_error": [str(e)]})
        return df
    

if __name__ == "__main__":

    """just to test the cache using the bird_validation_sql_checked.csv, remember to set the mount-folder and update the path"""

    db_base_path = "/home/gard/mount-folder/datasets/"
    questions = pd.read_csv("/home/gard/mount-folder/datasets/BIRD-SQL/bird_validation_sql_checked.csv")
    start_1 = time.time()
    process_questions(db_base_path, questions)
    end_1 = time.time()
    start_2 = time.time()
    process_questions(db_base_path, questions)
    end_2 = time.time()
    print(f"first exec: {end_1 - start_1:.2f} s")
    print(f"second exec: {end_2 - start_2:.2f} s")