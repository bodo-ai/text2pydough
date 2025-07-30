import argparse
import pandas as pd
import sqlite3
import os
import asyncio
import aiofiles
import csv
from pathlib import Path
from typing import Dict, Any, Tuple

async def query_sqlite_db(query: str, db_path: str, timeout_seconds: int = 180) -> Tuple[bool, str | None]:
    """
    Runs the SQL query on a SQLite database and returns success or failure.
    Uses asyncio.to_thread to avoid blocking the event loop.
    Includes timeout protection to prevent hanging queries.
    """
    def _execute_query():
        conn = None
        cur = None
        try:
            conn = sqlite3.connect(db_path)
            # Set a timeout on the connection itself as additional protection
            conn.execute("PRAGMA busy_timeout = 30000")  # 30 seconds for database locks
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
    
    try:
        # Apply timeout to the entire query execution
        return await asyncio.wait_for(
            asyncio.to_thread(_execute_query), 
            timeout=timeout_seconds
        )
    except asyncio.TimeoutError:
        return False, f"Query execution exceeded maximum time limit of {timeout_seconds} seconds."

class CSVWriter:
    """Async CSV writer that handles real-time writing to files."""
    
    def __init__(self, filepath: str, fieldnames: list):
        self.filepath = filepath
        self.fieldnames = fieldnames
        self.file_handle = None
        self.writer = None
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def __aenter__(self):
        self.file_handle = await aiofiles.open(self.filepath, 'w', newline='', encoding='utf-8')
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.file_handle:
            await self.file_handle.close()
    
    async def write_row(self, row_dict: Dict[str, Any]):
        async with self._lock:
            if not self._initialized:
                # Write header
                header_line = ','.join(f'"{field}"' for field in self.fieldnames) + '\n'
                await self.file_handle.write(header_line)
                self._initialized = True
            
            # Write data row
            values = []
            for field in self.fieldnames:
                value = row_dict.get(field, '')
                # Escape quotes and wrap in quotes
                if isinstance(value, str):
                    value = value.replace('"', '""')
                values.append(f'"{value}"')
            
            row_line = ','.join(values) + '\n'
            await self.file_handle.write(row_line)
            await self.file_handle.flush()

async def process_query(row: pd.Series, db_base_path: str, valid_writer: CSVWriter, invalid_writer: CSVWriter, timeout_seconds: int = 180) -> None:
    """
    Processes a single query row and writes the result to appropriate CSV file.
    Includes timeout protection for long-running queries.
    """
    if 'ground_truth_sql' in row:
        sql_query = row['ground_truth_sql']
    else:
        sql_query = row['sql']
    
    db_name = row['db_name']
    dataset_name = row['dataset_name']
    db_path = os.path.join(db_base_path, dataset_name, "databases", f"{db_name}", f"{db_name}.sqlite")
    
    # Check if the database file exists
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        invalid_row = row.to_dict()
        invalid_row.update({
            "execution_result": "DB Not Found",
            "exception": f"Database {db_path} does not exist."
        })
        await invalid_writer.write_row(invalid_row)
        return
    
    print(f"🔄 Processing SQL query for DB: {db_name}")
    start_time = asyncio.get_event_loop().time()
    
    # Execute the SQL query with timeout protection
    success, error_message = await query_sqlite_db(sql_query, db_path, timeout_seconds)
    
    end_time = asyncio.get_event_loop().time()
    execution_time = end_time - start_time
    
    if success:
        print(f"✅ Success: {db_name} (took {execution_time:.2f}s)")
        valid_row = row.to_dict()
        await valid_writer.write_row(valid_row)
    else:
        if "exceeded maximum time limit" in str(error_message):
            print(f"⏰ Timeout: {db_name} (exceeded {timeout_seconds}s limit)")
        else:
            print(f"❌ Failed: {db_name} - {error_message}")
        
        invalid_row = row.to_dict()
        invalid_row.update({
            "execution_result": "Failed",
            "exception": error_message
        })
        await invalid_writer.write_row(invalid_row)

async def process_sql_queries(csv_file_path: str, db_base_path: str, max_concurrent: int = 10, timeout_seconds: int = 180):
    """
    Reads a CSV file, processes the `sql` column, and checks if the queries run successfully.
    Writes results to CSV files in real time using asyncio.
    Includes timeout protection for long-running queries.
    """
    # Read the CSV into a DataFrame
    print(f"📖 Reading CSV file: {csv_file_path}")
    df = pd.read_csv(csv_file_path)
    
    # Ensure the necessary columns exist
    required_cols = ['db_name', 'dataset_name']
    sql_col = 'ground_truth_sql' if 'ground_truth_sql' in df.columns else 'sql'
    
    if sql_col not in df.columns:
        raise ValueError("The CSV must contain either 'sql' or 'ground_truth_sql' column.")
    
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"The CSV must contain '{col}' column.")
    
    print(f"📊 Found {len(df)} queries to process")
    print(f"⏱️  Timeout set to {timeout_seconds} seconds ({timeout_seconds//60} minutes)")
    print(f"🔄 Max concurrent queries: {max_concurrent}")
    
    # Generate file paths for the outputs
    base_name, ext = os.path.splitext(csv_file_path)
    valid_file_path = f"{base_name}_sql_checked{ext}"
    invalid_file_path = f"{base_name}_removed_questions{ext}"
    
    # Get all column names for CSV headers
    valid_fieldnames = list(df.columns)
    invalid_fieldnames = list(df.columns) + ['execution_result', 'exception']
    
    # Create CSV writers
    valid_writer = CSVWriter(valid_file_path, valid_fieldnames)
    invalid_writer = CSVWriter(invalid_file_path, invalid_fieldnames)
    
    print(f"💾 Writing valid queries to: {valid_file_path}")
    print(f"💾 Writing invalid queries to: {invalid_file_path}")
    
    # Process queries with controlled concurrency
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_semaphore(row):
        async with semaphore:
            await process_query(row, db_base_path, valid_writer, invalid_writer, timeout_seconds)
    
    async with valid_writer, invalid_writer:
        tasks = [process_with_semaphore(row) for _, row in df.iterrows()]
        
        # Process all tasks with progress tracking
        completed = 0
        start_time = asyncio.get_event_loop().time()
        
        for task in asyncio.as_completed(tasks):
            await task
            completed += 1
            if completed % 10 == 0 or completed == len(tasks):
                elapsed = asyncio.get_event_loop().time() - start_time
                print(f"📈 Progress: {completed}/{len(tasks)} queries processed ({completed/len(tasks)*100:.1f}%) - Elapsed: {elapsed:.1f}s")
    
    total_time = asyncio.get_event_loop().time() - start_time
    print(f"🎉 Processing completed in {total_time:.2f} seconds!")
    print(f"💾 Valid queries saved to: {valid_file_path}")
    print(f"💾 Invalid queries saved to: {invalid_file_path}")

async def main():
    parser = argparse.ArgumentParser(description="Process SQL queries asynchronously with real-time CSV output")
    parser.add_argument('input_csv', help='Path to input CSV file')
    parser.add_argument('--db-base-path', default="/home/gerald8525/repositories/mount-folder/datasets/",
                       help='Base path for database files')
    parser.add_argument('--max-concurrent', type=int, default=10,
                       help='Maximum number of concurrent database connections')
    parser.add_argument('--timeout', type=int, default=180,
                       help='Maximum time in seconds for each query execution (default: 180 = 3 minutes)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_csv):
        print(f"❌ Error: Input CSV file '{args.input_csv}' not found.")
        return
    
    if args.timeout <= 0:
        print(f"❌ Error: Timeout must be a positive number of seconds.")
        return
    
    print("🚀 Starting async SQL query processing...")
    await process_sql_queries(args.input_csv, args.db_base_path, args.max_concurrent, args.timeout)
    print("✅ SQL query processing completed.")

if __name__ == '__main__':
    asyncio.run(main())