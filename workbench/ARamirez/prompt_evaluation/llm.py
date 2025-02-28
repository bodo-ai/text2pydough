# %%
import argparse
import os
import re
import pandas as pd
import aisuite as ai
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import UserMessage, SystemMessage
from azure.core.credentials import AzureKeyCredential
from azure.core.pipeline.transport import RequestsTransport
import pydough
from pydough.unqualified import transform_cell
from pandas.testing import assert_frame_equal, assert_series_equal
import re

pydough.active_session.load_metadata_graph(f"{os.path.dirname(__file__)}/test_data/tpch_demo_graph.json", "TPCH")
pydough.active_session.connect_database("sqlite", database=f"{os.path.dirname(__file__)}/test_data/tpch.db")

WORDS_MAP = {
    "partition": "PARTITION",
    "group_by": "PARTITION",
    "where": "WHERE",
    "count": "COUNT",
    "sum": "SUM",
    "avg": "AVG",
    "min": "MIN",
    "max": "MAX",
    "ndistinct": "NDISTINCT",
    "has": "HAS",
    "hasnot": "HASNOT",
    "order_by": "ORDER_BY",
    "top_k": "TOP_K",
    "ranking": "RANKING",
    "percentile": "PERCENTILE",
    "lower": "LOWER",
    "upper": "UPPER",
    "length": "LENGTH",
    "startswith": "STARTSWITH",
    "endswith": "ENDSWITH",
    "contains": "CONTAINS",
    "like": "LIKE",
    "join_strings": "JOIN_STRINGS",
    "year": "YEAR",
    "month": "MONTH",
    "day": "DAY",
    "hour": "HOUR",
    "minute": "MINUTE",
    "second": "SECOND",
    "iff": "IFF",
    "isin": "ISIN",
    "default_to": "DEFAULT_TO",
    "present": "PRESENT",
    "absent": "ABSENT",
    "keep_if": "KEEP_IF",
    "monotonic": "MONOTONIC",
    "abs": "ABS",
    "round": "ROUND",
    "power": "POWER",
    "sqrt": "SQRT"
}

def replace_with_upper(text):
    # Use regex to match words that appear in the words_map (case-insensitive)
    def replacer(match):
        word = match.group(0)
        # Check if the lowercase version of the word is in the map
        lower_word = word.lower()
        if lower_word in WORDS_MAP:
            return WORDS_MAP[lower_word]
        else:
            return word
    
    # Replace the matched words using the replacer function
    return re.sub(r'\b\w+\b', replacer, text)

def extract_python_code(text):
    """Extracts all Python code from triple backticks in the given text and combines them."""
    if not isinstance(text, str):  # Ensure text is a string
        return ""

    # Find all Python code blocks wrapped in triple backticks
    matches = re.findall(r"```python\n(.*?)\n```", text, re.DOTALL)
    
    # Combine all the matched code snippets into a single string, separated by newlines
    combined_code = "\n".join([match.strip() for match in matches])

    return combined_code

class PydoughCodeError(Exception):
    """Custom exception for errors related to Pydough code execution."""
    pass

def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()
    
class LLMClient:
    def __init__(self, provider, model, database_file='./tcph_graph.md', prompt_file='./prompt4.md', script_file="./cheatsheet_v4_examples.md"):
        """
        Initializes the LLMClient with the provider and model.
        """
        self.provider = provider
        self.model = model
        self.client = ai.Client()
        prompt= read_file(prompt_file)
        script_content= read_file(script_file)
        database_content= read_file(database_file)
        formatted_prompt = prompt.format(script_content=script_content, database_content=database_content)
        self.prompt_file = formatted_prompt
        

    def get_pydough_code(self,text):
        try:
            local_env = {"pydough": pydough, "datetime": datetime}
            extracted_code = extract_python_code(text)
            extracted_code = replace_with_upper(extracted_code)
            transformed_source = transform_cell(extracted_code, "pydough.active_session.metadata", set(local_env))
            exec(transformed_source, {}, local_env)
            last_variable = list(local_env.values())[-1]
            result_df = pydough.to_df(last_variable)
            return extracted_code, result_df
        except Exception as e:
           raise PydoughCodeError(f"An error occurred while processing the code: {str(e)}")
    
    def ask(self, question):
        """Generates a response using aisuite."""
        messages = [{"role": "system", "content": self.prompt_file}, {"role": "user", "content": question}]
        try:
            response = self.client.chat.completions.create(
                model=f"{self.provider}:{self.model}",
                messages=messages,
                temperature=0.0
            )
            
            code,pydough_df= self.get_pydough_code(response.choices[0].message.content)
            return code, pydough_df
        except Exception as e:
            raise PydoughCodeError(f"An error occurred while asking the llm: {str(e)}")
    

# %%
