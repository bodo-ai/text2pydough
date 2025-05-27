import pandas as pd
import sqlite3
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

def query_sqlite_db(query: str, db_path: str) -> tuple[bool, str | None]:
    """
    Runs the SQL query on a SQLite database and returns success or failure.
    """
    conn = None
    cur = None
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(query)
        cur.fetchall()  # Fetch results to ensure the query executes fully.
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def process_query(row, db_base_path):
    """
    Processes a single query row and returns the result as a dictionary.
    """
    sql_query = row['sql']
    db_name = row['db_name']
    dataset_name = row['dataset_name']
    db_path = os.path.join(db_base_path, dataset_name, "databases", f"{db_name}", f"{db_name}.sqlite")

    print(f"Processing SQL query for DB: {db_name}")
    print(f"Processing sql query: {sql_query}")

    # Check if the database file exists
    if not os.path.exists(db_path):
        return {
            "question": row.get("question", ""),
            "sql": sql_query,
            "db_name": db_name,
            "dataset_name": dataset_name,
            "execution_result": "DB Not Found",
            "exception": f"Database {db_path} does not exist."
        }

    # Execute the SQL query and record the result
    success, error_message = query_sqlite_db(sql_query, db_path)
    return {
        "question": row.get("question", ""),
        "sql": sql_query,
        "db_name": db_name,
        "dataset_name": dataset_name,
        "execution_result": "Success" if success else "Failed",
        "exception": error_message
    }

def process_sql_queries(csv_file_path: str, db_base_path: str):
    """
    Reads a CSV file, processes the `sql` column, and checks if the queries run successfully in parallel.
    """
    # Read the CSV into a DataFrame
    df = pd.read_csv(csv_file_path)
    
    # Ensure the necessary columns exist
    if 'sql' not in df.columns or 'db_name' not in df.columns or 'dataset_name' not in df.columns:
        raise ValueError("The CSV must contain 'sql', 'db_name', and 'dataset_name' columns.")
    
    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda row: process_query(row, db_base_path), [row for _, row in df.iterrows()]))
    
    # Create a new DataFrame for the results
    result_df = pd.DataFrame(results)
    
    # Save the results to a new CSV
    timestamp = datetime.now().strftime('%Y_%m_%d-%H_%M_%S')
    result_df.to_csv(f"sql_execution_results_{timestamp}.csv", index=False)
    print(f"Results saved")

# Example usage:
process_sql_queries("/home/gerald8525/repositories/text2pydough/workbench/lcar_lab/training/utils/test_execution_2025_05_26-14_43_53_golden_flash25.csv", "/home/gerald8525/repositories/mount-folder/datasets/")

