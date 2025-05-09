import collections
from datetime import datetime
import os
import pandas as pd
import pydough
from pydough.unqualified import transform_cell
from pandas.testing import assert_frame_equal, assert_series_equal
import re
from concurrent.futures import ThreadPoolExecutor

pydough.active_session.load_metadata_graph("/mnt/c/Users/david/bodo/TPCH/test_data/tpch_demo_graph.json", "TPCH")
pydough.active_session.connect_database("sqlite", database="/mnt/c/Users/david/bodo/TPCH/test_data/tpch.db",  check_same_thread=False)

local_env = {"pydough": pydough, "datetime": datetime}

extracted_code = """nation_counts = nations.CALCULATE(
    nation_name=name,
    n_customers=COUNT(customers),
    n_suppliers=COUNT(suppliers)
).ORDER_BY(nation_name.ASC())"""

def execute_code_and_extract_result(extracted_code, local_env):
    """Executes the Python code and returns the result or raises an exception."""
    try:
        transformed_source = transform_cell(extracted_code, "pydough.active_session.metadata", set(local_env))
        exec(transformed_source, {}, local_env)
        last_variable = list(local_env.values())[-1]
        print(last_variable)
        result_df = pydough.to_df(last_variable)
        return result_df, None  # Return result and no exception
    except Exception as e:
        return None, str(e)  # Return None as result and exception message

result, exception = execute_code_and_extract_result(extracted_code, local_env)
print(result)
print(exception)