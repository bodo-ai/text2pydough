# %%
import argparse
import os
import traceback
import re
import matplotlib.pyplot as plt
import pandas as pd
import aisuite as ai
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import UserMessage, SystemMessage
from azure.core.credentials import AzureKeyCredential
from azure.core.pipeline.transport import RequestsTransport
from ai_providers import GeminiAIProvider
import pydough
from pydough.unqualified import transform_cell
from pandas.testing import assert_frame_equal, assert_series_equal
import re
from rapidfuzz import fuzz, process
pydough.active_session.load_metadata_graph(f"./test_data/tpch_demo_graph.json", "TPCH")
pydough.active_session.connect_database("sqlite", database=f"../../AAraya/demo/test_data/tpch.db", check_same_thread=False)

with open('./demo_queries.json', "r") as json_file:
    demo_dict = json.load(json_file)

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

def format_prompt(script_content, prompt, data, question, database_content, definitions, include_comments):
    ids = data[question]["context_id"]
    prompt_string = ' '.join(ids)
    comment_note = "" if include_comments else "IMPORTANT: Do not include comments in the code."
    return prompt.format(
        script_content=script_content,
        database_content=database_content,
        similar_queries="",
        definitions=definitions,
        recomendation=f"{prompt_string}. {comment_note}"
    )

def extract_python_code(text):
    """Extract all Python code between triple backticks."""
    if not isinstance(text, str):
        return ""

    matches = re.findall(r"```(?:python)?\s*(.*?)```", text, re.DOTALL)
    combined_code = "\n".join(match.strip() for match in matches)
    return combined_code

def remove_comments_from_code(code):
    """Remove Python-style and inline # comments from code."""
    if not code:
        return code
    lines = code.splitlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if "#" in line:
            quote_count = line.count('"') + line.count("'")
            if quote_count % 2 == 0:
                line = line.split("#")[0].rstrip()
        cleaned.append(line)
    return "\n".join(cleaned)

class Result:
    def __init__(
        self, pydough_code=None, full_explanation=None, df=None, exception=None, 
        original_question=None, sql_output=None, base_prompt=None, cheat_sheet=None, 
        knowledge_graph=None
    ):
        self.code = pydough_code
        self.full_explanation = full_explanation
        self.df = df
        self.exception = exception
        self.original_question = original_question
        self.sql = sql_output
        self.base_prompt = base_prompt
        self.cheat_sheet = cheat_sheet
        self.knowledge_graph = knowledge_graph
        
class PydoughCodeError(Exception):
    """Custom exception for errors related to Pydough code execution."""
    pass

def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

class LLMClient:
    def __init__(
        self, 
        database_file='./tcph_graph.md', 
        prompt_file='./prompt.md', 
        script_file="./cheatsheet.md", 
        temperature=0.0,
        definitions=[],
        include_comments=True
    ):
        """
        Initializes the LLMClient with the provider and model.
        """
        # default_provider = "aws"
        # default_model = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
        
        default_provider = "google"
        default_model = "gemini-2.5-pro-exp-03-25"
        
        # default_provider = "aws-deepseek"
        # default_model = "us.deepseek.r1-v1:0"
        
        self.provider = default_provider
        self.model = default_model
        self.client =  GeminiAIProvider(model_id=self.model)
        self.prompt = read_file(prompt_file)
        self.script = read_file(script_file)
        self.database = read_file(database_file)
        self.temperature = temperature
        self.definitions = definitions
        self.include_comments = include_comments

    def add_definition(self, new_definition):
        """Add a new definition to definitions list."""
        if not new_definition:
            return "You need to provide a new definition."
        self.definitions.append(new_definition)
        print(f"The new definition has been added to the definition list.")
        
    def get_pydough_sql(self, text):
        try:
            local_env = {"pydough": pydough, "datetime": datetime}
            transformed_source = transform_cell(text, "pydough.active_session.metadata", set(local_env))
            exec(transformed_source, {}, local_env)
            last_variable = list(local_env.values())[-1]
            result_sql = pydough.to_sql(last_variable)
            return result_sql
        except Exception as e:
            tb_str = traceback.format_exc()
            raise PydoughCodeError(f"An error occurred while processing the code:\n\n{tb_str}")
            
    def get_pydough_code(self, text):
        try:
            local_env = {"pydough": pydough, "datetime": datetime}
            transformed_source = transform_cell(text, "pydough.active_session.metadata", set(local_env))
            exec(transformed_source, {}, local_env)
            last_variable = list(local_env.values())[-1]
            result_df = pydough.to_df(last_variable)
            return result_df
        except Exception as e:
            tb_str = traceback.format_exc()
            raise PydoughCodeError(f"An error occurred while processing the code:\n\n{tb_str}")
        
    def discourse(self, follow_up):
        response = self.client.chat(follow_up)
        return response.text
    
    def ask(self, question, is_corrected = True):
        """Generates a response using aisuite and returns a Result object."""
        result = Result(original_question=question)  # Initialize the result object

        try:
            # Look up the most similar question in the dictionary with a threshold of 60%.
            match = process.extractOne(
                query=question,
                choices=demo_dict.keys(),
                scorer=fuzz.token_sort_ratio  
            )
            
            if match:
                best_match, score, *_ = match  # Unpack answer
                if score >= 60:  # If similarity score is 60% or more
                    # Use the most similar question found
                    formatted_prompt = format_prompt(
                        self.script,
                        self.prompt,
                        demo_dict,
                        best_match,  
                        self.database,
                        self.definitions,
                        self.include_comments
                    )
                else:
                    # If no adequate match is found, use the standard prompt
                    formatted_prompt = self.prompt.format(
                        script_content=self.script,
                        database_content=self.database,
                        similar_queries="",
                        definitions=self.definitions,
                        recomendation="" if self.include_comments else "IMPORTANT: Do not include comments in the code."
                    )
            else:
                # If not in dict, use the standard prompt.
                formatted_prompt = self.prompt.format(
                    script_content=self.script, 
                    database_content=self.database,
                    similar_queries="",
                    definitions=self.definitions,
                    recomendation="" if self.include_comments else "IMPORTANT: Do not include comments in the code."
                )
            if isinstance(question, tuple):  # Soporte para (result, follow_up)
                question = self.discourse(*question)
            messages = [
                {"role": "system", "content": formatted_prompt}, 
                {"role": "user", "content": f"{question}. Let´s solve the query step by step"}
            ]
            if self.client.chat_session is None:
                raw_response, _ = self.client.start_chat(
                    question=f"{question}. Let’s solve the query step by step",
                    prompt=formatted_prompt,
                    temperature=self.temperature,
                    top_p=0,
                    top_k=0
                )
            else:
                raw_response = self.client.chat(
                    question=f"{question}. Let’s solve the query step by step"
                )
            print("RAW RESPONSE TEXT:\n", response_text)
            response = "".join(
                part.text for part in raw_response.candidates[0].content.parts if part.text
            )
            extracted_code = extract_python_code(response)
            
            if not self.include_comments:
                extracted_code = remove_comments_from_code(extracted_code)
                
            extracted_code = replace_with_upper(extracted_code)
            
            
            result.code = extracted_code
            result.full_explanation = response
            result.base_prompt = self.prompt
            result.cheat_sheet = self.script
            result.knowledge_graph = self.database
            
            print(extracted_code)
            
            pydough_sql = self.get_pydough_sql(extracted_code)
            pydough_df = self.get_pydough_code(extracted_code)
            
            result.df = pydough_df
            result.sql = pydough_sql
            
            return result
        
        except Exception as e:
            result.exception = traceback.format_exc()
            if not is_corrected:
                print("Solvin an issue in the code...")
                return self.correct(result)
            return result  

    def correct(self, result):
        """Try to correct a Result object if an exception exists."""
        
        if result.exception:
            try:
                formatted_prompt = self.prompt.format(
                    script_content=self.script, 
                    similar_queries="", 
                    database_content=self.database, 
                    definitions=self.definitions,
                    recomendation=""
                )
                corrective_question = (
                    f"An error occurred while processing this code: {result.code}. "
                    f"The error is: '{result.exception}'. "
                    f"The original question was: '{result.original_question}'. "
                    f"Can you help me fix the issue? Take into account the context: '{formatted_prompt}'. "
                )
                corrected_result = self.ask(corrective_question, is_corrected=True)
                return corrected_result
            except Exception as e:
                return Result(original_question=result.original_question, exception=e)
        return result
    
    def reset_chat(self):
        self.client.chat_session = None
# %%