# %%
import collections
from datetime import datetime
import os
import pandas as pd
import pydough
from pydough.unqualified import transform_cell
from pandas.testing import assert_frame_equal, assert_series_equal
import re

pydough.active_session.load_metadata_graph(f"{os.path.dirname(__file__)}/tpch_demo_graph.json", "TPCH")
pydough.active_session.connect_database("sqlite", database=f"{os.path.dirname(__file__)}/tpch.db")



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
        sorted_df = sorted_df.sort_values(by=list(sorted_df.columns))

    # reset index
    sorted_df = deduplicate_columns(sorted_df)
    sorted_df = sorted_df.reset_index(drop=True)
    return sorted_df

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

    # perform same checks again for normalized tables
    if df_gold.shape != df_gen.shape:
        return False
    # fill NaNs with -99999 to handle NaNs in the dataframes for comparison
    df_gen.fillna(-99999, inplace=True)
    df_gold.fillna(-99999, inplace=True)
    is_equal = df_gold.values == df_gen.values
    try:
        return is_equal.all()
    except:
        return is_equal
    
def convert_to_df(last_variable):
    return pydough.to_df(last_variable)

def execute_code_and_extract_result(extracted_code, local_env):
    """Executes the Python code and returns the result or raises an exception."""
    try:
        transformed_source = transform_cell(extracted_code, "pydough.active_session.metadata", set(local_env))
        exec(transformed_source, {}, local_env)
        last_variable = list(local_env.values())[-1]
        print(last_variable)
        result_df = convert_to_df(last_variable)
        return result_df, None  # Return result and no exception
    except Exception as e:
        return None, str(e)  # Return None as result and exception message

def query_sqlite_db(
    query: str,
    db_creds: str = None,
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
      
        conn = sqlite3.connect(db_creds)
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
        return df
    except Exception as e:
        if cur:
            cur.close()
        if conn:
            conn.close()
        raise e
    
def process_row(row, db_path):
    extracted_code = row.get('extracted_python_code')
    question= row.get('question')
    
    if pd.notna(extracted_code): 
        local_env = {"pydough": pydough, "datetime": datetime}
        
        result, exception = execute_code_and_extract_result(extracted_code, local_env)
        
        if result is not None:
            extracted_sql = query_sqlite_db(row["sql"], db_path)
            comparison_result = compare_df(result, extracted_sql,query_category="a", question="a")
            
            return 'Match' if comparison_result else 'No Match', None
        else:
            return 'Query Error', exception
    return 'Unknown', None  

def compare_output(folder_path, csv_file_path, db_path):
    """
    Extracts and returns the value of a specific variable from Python code in a CSV file.
    Returns:
        pd.DataFrame: The modified dataframe with the results.
    """
    # Read the CSV file into a Pandas DataFrame
    df = pd.read_csv(csv_file_path)

    results = df.apply(lambda row: process_row(row, db_path), axis=1)

    # Extract the results into the appropriate columns
    df['comparison_result'] = [result[0] for result in results]
    df['exception'] = [result[1] for result in results]
    
    output_file = f"{folder_path}/test_execution_{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.csv"
    # Save the modified DataFrame to a new CSV
    df.to_csv(output_file, index=False)

    return output_file, df

# %%
#compare_output("../results/aws/us.anthropic.claude-3-7-sonnet-20250219-v1:0/test", "../results/aws/us.anthropic.claude-3-7-sonnet-20250219-v1:0/responses_2025_02_26-10_08_45.csv","./tpch.db")
# %%
