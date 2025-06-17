# %%
import collections
from datetime import datetime
import os
import pandas as pd
import pydough
from pydough.unqualified import transform_cell
from pandas.testing import assert_frame_equal, assert_series_equal
import re
from pandas.testing import assert_frame_equal, assert_series_equal
from pandas.api.types import is_numeric_dtype
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
metadata_lock = Lock()
from pandas.testing import assert_frame_equal   # works in every supported pandas version

def deduplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols = df.columns.tolist()
    if len(cols) != len(set(cols)):
        duplicates = [
            item for item, count in collections.Counter(cols).items() if count > 1
        ]
        for dup in duplicates:
            indices = [i for i, x in enumerate(cols) if x == dup]
            for i in indices:
                cols[i] = f"{dup}_{i}"
        df.columns = cols
    return df

import pandas as pd
import re
from typing import Optional, List, Tuple
import logging

def normalize_table(
    df: pd.DataFrame, query_category: str, question: str, sql: str = None
) -> pd.DataFrame:
    """
    Normalizes a dataframe by:
    1. removing all duplicate rows
    2. sorting columns in alphabetical order
    3. sorting rows using values from first column to last (if query_category is not 'order_by' and question does not ask for ordering)
    4. resetting index
    """
    # remove duplicate rows, if any
    df = df.drop_duplicates()

    # sort columns in alphabetical order of column names
    sorted_df = df.reindex(sorted(df.columns), axis=1)

    # check if query_category is 'order_by' and if question asks for ordering
    has_order_by = False
    pattern = re.compile(r"\b(order|sort|arrange)\b", re.IGNORECASE)
    in_question = re.search(pattern, question.lower())  # true if contains
    if query_category == "order_by" or in_question:
        has_order_by = True

        if sql:
            # determine which columns are in the ORDER BY clause of the sql generated, using regex
            pattern = re.compile(r"ORDER BY[\s\S]*", re.IGNORECASE)
            order_by_clause = re.search(pattern, sql)
            if order_by_clause:
                order_by_clause = order_by_clause.group(0)
                # get all columns in the ORDER BY clause, by looking at the text between ORDER BY and the next semicolon, comma, or parantheses
                pattern = re.compile(r"(?<=ORDER BY)(.*?)(?=;|,|\)|$)", re.IGNORECASE)
                order_by_columns = re.findall(pattern, order_by_clause)
                order_by_columns = (
                    order_by_columns[0].split() if order_by_columns else []
                )
                order_by_columns = [
                    col.strip().rsplit(".", 1)[-1] for col in order_by_columns
                ]

                ascending = False
                # if there is a DESC or ASC in the ORDER BY clause, set the ascending to that
                if "DESC" in [i.upper() for i in order_by_columns]:
                    ascending = False
                elif "ASC" in [i.upper() for i in order_by_columns]:
                    ascending = True

                # remove whitespace, commas, and parantheses
                order_by_columns = [col.strip() for col in order_by_columns]
                order_by_columns = [
                    col.replace(",", "").replace("(", "") for col in order_by_columns
                ]
                order_by_columns = [
                    i
                    for i in order_by_columns
                    if i.lower()
                    not in ["desc", "asc", "nulls", "last", "first", "limit"]
                ]

                # get all columns in sorted_df that are not in order_by_columns
                other_columns = [
                    i for i in sorted_df.columns.tolist() if i not in order_by_columns
                ]

                # only choose order_by_columns that are in sorted_df
                order_by_columns = [
                    i for i in order_by_columns if i in sorted_df.columns.tolist()
                ]
                sorted_df = sorted_df.sort_values(
                    by=order_by_columns + other_columns, ascending=ascending
                )

                sorted_df = sorted_df[other_columns + order_by_columns]

    if not has_order_by:
        # sort rows using values from first column to last
        sorted_df = _sort_by_all_columns(sorted_df)

    # reset index
    sorted_df = deduplicate_columns(sorted_df)
    sorted_df = sorted_df.reset_index(drop=True)
    return sorted_df


def _should_preserve_original_order(query_category: str, question: str) -> bool:
    """Determine if the original row order should be preserved based on query intent."""
    if query_category.lower() == "order_by":
        return True
    
    # More precise regex pattern for ordering keywords
    order_pattern = re.compile(
        r'\b(?:order|sort|arrange|rank|bottom|first|last|highest|lowest)\b',
        re.IGNORECASE
    )
    return bool(order_pattern.search(question))


def _extract_order_by_info(sql: str) -> Tuple[List[str], bool]:
    """
    Extract ORDER BY columns and direction from SQL query.
    
    Returns:
        Tuple of (column_names, is_ascending)
    """
    # Find ORDER BY clause
    order_by_match = re.search(r'ORDER\s+BY\s+(.+?)(?:LIMIT|;|$)', sql, re.IGNORECASE | re.DOTALL)
    if not order_by_match:
        return [], True
    
    order_clause = order_by_match.group(1).strip()
    
    # Extract column names and direction
    columns = []
    is_ascending = True
    
    # Split by comma to handle multiple columns
    column_parts = [part.strip() for part in order_clause.split(',')]
    
    for part in column_parts:
        # Remove table prefixes and extract column name
        column_match = re.search(r'(?:\w+\.)?(\w+)', part)
        if column_match:
            column_name = column_match.group(1)
            # Skip SQL keywords
            if column_name.upper() not in ['ASC', 'DESC', 'NULLS', 'FIRST', 'LAST']:
                columns.append(column_name)
        
        # Check for DESC (default to ASC)
        if re.search(r'\bDESC\b', part, re.IGNORECASE):
            is_ascending = False
    
    return columns, is_ascending


def _clean_mixed_type_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean columns with mixed data types (e.g., numeric values mixed with empty strings).
    
    This handles common data quality issues like:
    - Numeric columns with empty strings or whitespace
    - Mixed numeric/string data
    - Various representations of missing values
    """
    cleaned_df = df
    
    for col in cleaned_df.columns:
        if cleaned_df[col].dtype == 'object':
            # Convert the column to handle mixed types
            cleaned_df[col] = _clean_mixed_column(cleaned_df[col])
    
    return cleaned_df


def _clean_mixed_column(series: pd.Series) -> pd.Series:
    """
    Clean a single column with mixed data types.
    
    Strategy:
    1. Try to convert to numeric (handles strings like '45.3')
    2. Replace empty strings and whitespace with NaN
    3. If mostly numeric, keep as numeric; otherwise keep as cleaned strings
    """
    # First, standardize empty/whitespace values to NaN
    cleaned_series = series
    
    # Replace empty strings, whitespace, and common null representations
    null_representations = ['', ' ', 'null', 'NULL', 'None', 'nan', 'NaN', 'n/a', 'N/A']
    cleaned_series = cleaned_series.replace(null_representations, pd.NA)
    
    # Try to convert to numeric
    numeric_series = pd.to_numeric(cleaned_series, errors='coerce')
    
    # Count how many values successfully converted to numeric
    non_null_original = cleaned_series.notna().sum()
    non_null_numeric = numeric_series.notna().sum()
    
    # If most values (>80%) are numeric, use numeric version
    if non_null_original > 0 and (non_null_numeric / non_null_original) > 0.8:
        return numeric_series
    else:
        # Keep as cleaned strings, but ensure consistent string representation
        return cleaned_series.astype(str).replace(['nan', 'None', '<NA>'], pd.NA)


def _apply_sql_ordering(df: pd.DataFrame, sql: str) -> pd.DataFrame:
    """Apply ordering based on SQL ORDER BY clause with mixed-type handling."""
    try:
        order_columns, is_ascending = _extract_order_by_info(sql)
        
        if not order_columns:
            return df
        
        # Clean mixed-type columns before sorting
        cleaned_df = _clean_mixed_type_columns(df)
        
        # Filter to columns that exist in the dataframe
        valid_columns = [col for col in order_columns if col in cleaned_df.columns]
        
        if valid_columns:
            # Add remaining columns for stable sorting
            remaining_columns = [col for col in cleaned_df.columns if col not in valid_columns]
            all_sort_columns = valid_columns + remaining_columns
            
            # Sort with proper error handling
            sorted_df = cleaned_df.sort_values(
                by=all_sort_columns, 
                ascending=is_ascending,
                na_position='last'  # Handle NaN values consistently
            )
            
            # Reorder columns to put ORDER BY columns first
            column_order = remaining_columns + valid_columns
            return sorted_df[column_order]
        
    except Exception as e:
        logging.warning(f"Failed to apply SQL ordering: {e}. Using default sorting.")
    
    return df


def _sort_by_all_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Sort dataframe by all columns with proper error handling for mixed types."""
    try:
        # Clean mixed-type columns before sorting
        cleaned_df = _clean_mixed_type_columns(df)
        return cleaned_df.sort_values(
            by=list(cleaned_df.columns), 
            ascending=True,
            na_position='last'
        )
    except Exception as e:
        logging.warning(f"Failed to sort by all columns: {e}. Returning unsorted dataframe.")
        return df
    
# Enhanced version with additional features
def normalize_table_enhanced(
    df: pd.DataFrame,
    query_category: str,
    question: str,
    sql: Optional[str] = None,
    preserve_dtypes: bool = True,
    handle_mixed_types: bool = True
) -> pd.DataFrame:
    """
    Enhanced version with additional normalization features.
    
    Additional features:
    - Data type preservation
    - Mixed type handling
    - Better error handling and logging
    - Performance optimizations
    """
    if df.empty:
        return df.copy()
    
    original_dtypes = df.dtypes.to_dict() if preserve_dtypes else None
    
    try:
        # Core normalization steps
        result = normalize_table(df, query_category, question, sql)
        
        # Restore data types if requested
        if preserve_dtypes and original_dtypes:
            for col, dtype in original_dtypes.items():
                if col in result.columns:
                    if handle_mixed_types:
                        result[col] = pd.to_numeric(result[col], errors='ignore')
                    else:
                        try:
                            result[col] = result[col].astype(dtype)
                        except (ValueError, TypeError):
                            logging.warning(f"Could not restore dtype {dtype} for column {col}")
        
        return result
        
    except Exception as e:
        logging.error(f"Normalization failed: {e}")
        return df.copy()  # Return original dataframe on failure
    
def hard_match(left, right, atol=1e-6, rtol=1e-6,
                 ignore_order=True, **kwargs) -> bool:
    """
    Return True if two DataFrames are equal within the given tolerances.
    Parameters
    ----------
    atol, rtol : float
        Absolute / relative tolerance for numeric differences.
    ignore_order : bool
        If True, sort both on column names and index labels before comparing.
    **kwargs
        Any other assert_frame_equal keyword (e.g. check_dtype=False).
    """
    if ignore_order:
        left  = left.sort_index(axis=0).sort_index(axis=1)
        right = right.sort_index(axis=0).sort_index(axis=1)
    try:
        assert_frame_equal(
            left, right,
            check_exact=False,     # turn on tolerance mode
            atol=atol, rtol=rtol,
            **kwargs               # pass things like check_dtype, check_names, etc.
        )
        return True
    except AssertionError:
        return False

def compare_df(
    df_gold: pd.DataFrame,
    df_gen: pd.DataFrame,
    query_category: str,
    question: str,
    query_gold: str = None,
    query_gen: str = None,
) -> bool:
    """
    Compares two dataframes and returns True if they are the same, else False.
    query_gold and query_gen are the original queries that generated the respective dataframes.
    """
    # drop duplicates to ensure equivalence
    try:
        is_equal = df_gold.values == df_gen.values
        if is_equal.all():
            return True
    except:
        try:
            is_equal = df_gold.values == df_gen.values
            if is_equal:
                return True
        except:
            pass
    
    df_gold = normalize_table(df_gold, query_category, question, query_gold)
    df_gen = normalize_table(df_gen, query_category, question, query_gen)
    print("df_gold", df_gold)
    print("df_gen", df_gen)
    # perform same checks again for normalized tables
    if df_gold.shape != df_gen.shape:
        return False
    # fill NaNs with -99999 to handle NaNs in the dataframes for comparison
    df_gen.fillna(-99999, inplace=True)
    df_gold.fillna(-99999, inplace=True)
    is_equal = df_gold.values == df_gen.values
    if is_equal.all() == True:
        return True
    
    return secondary_check(df_gold, df_gen)
    
def series_contents_equal(s1: pd.Series, s2: pd.Series, numeric_tolerance= 1e-5) -> bool:
    """
    Checks if two Series have identical dtypes and values in the same order.
    Their original indices/names are ignored for the comparison itself, but they must
    have the same length (which should be pre-checked at the DataFrame level).
    """
    if is_numeric_dtype(s1) and is_numeric_dtype(s2):
        # Check if the numeric values are equal within a small tolerance
        return (s1 - s2).abs().max() < numeric_tolerance
    
    if s1.dtype != s2.dtype:
        return False
    return s1.reset_index(drop=True).equals(s2.reset_index(drop=True))

def secondary_check(df_gold: pd.DataFrame, df_gen: pd.DataFrame) -> bool:
    """
    Checks if all column contents of DataFrame A can be uniquely matched to column
    contents in DataFrame B. Column names and the order of columns in both
    DataFrames are ignored. Only dtype and values (in order) within each column matter.

    Args:
        df_gold (pd.DataFrame): The dataframe obtained by running the reference SQL.
        df_gen (pd.DataFrame): The dataframe obtained by running the generated PyDough code.

    Returns:
        bool: True if all column contents of df_gold can be uniquely matched in df_gen, False otherwise.
    """

    num_gold_cols = df_gold.shape[1]
    num_gen_cols = df_gen.shape[1]
    num_gold_rows = df_gold.shape[0]
    num_gen_rows = df_gen.shape[0]

    # 1. Handle df_gold having zero columns
    if num_gold_cols == 0:
        if num_gold_rows == 0: # df_gold is 0x0
            print("Info: df_gold has 0 columns and 0 rows. Trivially True.")
            return True
        else: # df_gold is Rx0 (R > 0)
            # For "exact values" across 0 columns but R rows, df_gen must also have R rows.
            result = num_gold_rows == num_gen_rows
            return result

    # 2. Row count mismatch (unless df_gold was 0x0, handled above)
    if num_gold_rows != num_gen_rows:
        return False

    # 3. Not enough columns in df_gen to match all of df_gold's columns
    if num_gold_cols > num_gen_cols:
        return False
    
    # --- Greedy Matching ---
    b_cols_used = [False] * num_gen_cols # Tracks which columns in df_gen have been matched

    for i in range(num_gold_cols):
        series_gold = df_gold.iloc[:, i]
        found_match_for_s_gold = False
        for j in range(num_gen_cols):
            if not b_cols_used[j]: # If df_gen's j-th column is not yet used
                series_gen = df_gen.iloc[:, j]
                if series_contents_equal(series_gold, series_gen):
                    b_cols_used[j] = True
                    found_match_for_s_gold = True
                    break # Move to the next column in df_gold
        
        if not found_match_for_s_gold:
            return False
        
    return True    
    
def convert_to_df(last_variable):
    return pydough.to_df(last_variable)

def execute_code_and_extract_result(extracted_code, local_env, cheatsheet_path, db_name, database_path):
    """Executes the Python code and returns the result or raises an exception."""
    try:
        with metadata_lock:
            pydough.active_session.load_metadata_graph(cheatsheet_path, db_name)
            pydough.active_session.connect_database("sqlite", database=database_path, check_same_thread=False)

        transformed_source = transform_cell(extracted_code, "pydough.active_session.metadata", set(local_env))
        exec(transformed_source, {}, local_env)
        last_variable = list(local_env.values())[-1]
        result_df = convert_to_df(last_variable)
        
        return result_df, None  # Return result and no exception
    except Exception as e:
        return None, e  # Return None as result and exception message


def query_sqlite_db(
    query: str,
    db_path: str = None,
    decimal_points: int = None,
) -> pd.DataFrame:
    """
    Runs query on sqlite db and returns results as a dataframe.
    This assumes that you have the evaluation databases set up in defog_data/sqlite_dbs/.
    If you don't, you can follow the instructions in the README of the defog-data repo to set it up.

    timeout: time in seconds to wait for query to finish before timing out
    decimal_points: number of decimal points to round floats to
    """
    import sqlite3

    conn = None
    cur = None
    try:
      
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(query)
        results = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]
        cur.close()
        conn.close()
        # make into a dataframe
        df = pd.DataFrame(results, columns=colnames)
      
        # round floats to decimal_points
        if decimal_points:
            df = df.round(decimal_points)
        return df, None
    except Exception as e:
        if cur:
            cur.close()
        if conn:
            conn.close()
        return None, str(e)
    
def process_row(row,db_base_path,metadata_base_path):
    extracted_code = row.get('extracted_python_code')
    question= row.get('question')
    
    if pd.notna(extracted_code): 
        local_env = {"pydough": pydough, "datetime": datetime}
        db_name = row['db_name']
        dataset_name = row['dataset_name']

        db_path = os.path.join(db_base_path, dataset_name, "databases", f"{db_name}/{db_name}.sqlite")
        metadata_dir = os.path.join(metadata_base_path, dataset_name, "metadata")
        metadata_path = os.path.join(metadata_dir, f"{db_name}_graph.json")
        print(question, db_name)

        result, exception = execute_code_and_extract_result(extracted_code, local_env, metadata_path, db_name, db_path)
        
        if result is not None:
            extracted_sql, db_exception = query_sqlite_db(row["sql"],db_path )
            if extracted_sql is None:
                return 'SQL error', db_exception  # If query failed, return 'Unknown' and exception

            comparison_result = compare_df(result, extracted_sql,query_category="a", question=question)
            
            return 'Match' if comparison_result else 'No Match', None
        else:
            return 'Query Error', exception
    return 'Unknown', None  

def compare_output(folder_path, csv_file_path, db_base_path, metadata_base_path):
    """
    Extracts and returns the value of a specific variable from Python code in a CSV file.
    Returns:
        pd.DataFrame: The modified dataframe with the results.
    """
    # Read the CSV file into a Pandas DataFrame
    df = pd.read_csv(csv_file_path)

    def process_and_return(row):
        return process_row(row, db_base_path, metadata_base_path)

    
    results = list(map(process_and_return, [row for index, row in df.iterrows()]))

    # Extract the results into the appropriate columns
    df['comparison_result'] = [result[0] for result in results]
    df['exception'] = [result[1] for result in results]
    
    output_file = f"{folder_path}/test_execution_{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.csv"
    # Save the modified DataFrame to a new CSV
    df.to_csv(output_file, index=False)

    return output_file, df

compare_output("/home/arami/bodo/text2pydough/workbench/lcar_lab/mlflow_experiments/results/google/gemini-2.0-flash-001/test", "/home/arami/bodo/text2pydough/workbench/lcar_lab/mlflow_experiments/results/google/gemini-2.0-flash-001/responses_2025_05_21-11_35_42.csv","/home/arami/mount-folder/datasets/", "/home/arami/mount-folder/datasets/")
