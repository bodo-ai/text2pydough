import argparse
import pandas as pd
import sqlite3
import os
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
    if dataset_name == "kaggleDBQA":
        dataset_name = "KaggleDBQA"
    db_path = os.path.join(db_base_path, dataset_name, "databases", f"{db_name}", f"{db_name}.sqlite")

    # Check if the database file exists
    if not os.path.exists(db_path):
        return {
            "question": row.get("question", ""),
            "sql": sql_query,
            "db_name": db_name,
            "dataset_name": dataset_name,
            "execution_result": "DB Not Found",
            "exception": f"Database {db_path} does not exist.",
            "row": row
        }
    
    
    print(f"Processing SQL query for DB: {db_name}")
    print(f"Processing sql query: {sql_query}")

    # Execute the SQL query and record the result
    success, error_message = query_sqlite_db(sql_query, db_path)
    return {
        "question": row.get("question", ""),
        "sql": sql_query,
        "db_name": db_name,
        "dataset_name": dataset_name,
        "execution_result": "Success" if success else "Failed",
        "exception": error_message,
        "row": row
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

    # Separate successful and failed queries
    valid_rows = []
    invalid_rows = []

    for result in results:
        if result['execution_result'] == "Success":
            valid_rows.append(result['row'])
        else:
            invalid_row = result['row'].to_dict()
            invalid_row['execution_result'] = result['execution_result']
            invalid_row['exception'] = result['exception']
            invalid_rows.append(invalid_row)

    # Create DataFrames for valid and invalid queries
    valid_df = pd.DataFrame(valid_rows)
    invalid_df = pd.DataFrame(invalid_rows)

    # Generate file paths for the outputs
    base_name, ext = os.path.splitext(csv_file_path)
    valid_file_path = f"{base_name}_sql_checked{ext}"
    invalid_file_path = f"{base_name}_removed_questions{ext}"

    # Save the resulting DataFrames
    valid_df.to_csv(valid_file_path, index=False)
    invalid_df.to_csv(invalid_file_path, index=False)

    print(f"Valid queries saved to: {valid_file_path}")
    print(f"Removed queries saved to: {invalid_file_path}")

# Example usage:
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_csv')
    args = parser.parse_args()

    input_csv = args.input_csv
    db_base_path = "/home/gerald8525/repositories/mount-folder/datasets/"

    print("Starting SQL query processing...")
    process_sql_queries(input_csv, db_base_path)
    print("SQL query processing completed.")
