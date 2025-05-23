import argparse
import ast
import json
import multiprocessing
import os
import re
import pandas as pd
import aisuite as ai
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import UserMessage, SystemMessage
from azure.core.credentials import AzureKeyCredential
import mlflow
from test_data.eval import compare_df, compare_output, execute_code_and_extract_result
from utils import autocommit, get_git_commit, modified_files, untracked_files
from claude import ClaudeModel, DeepseekModel
from collections import defaultdict
import pydough
from abc import ABC, abstractmethod

# === Abstract Class for AI Providers ===
class AIProvider(ABC):
    """Abstract class defining the interface for AI providers."""

    @abstractmethod
    def ask(self, question):
        """Returns a response for a given question."""
        pass


# === Azure AI Provider ===
class AzureAIProvider(AIProvider):
    """Handles responses from Azure AI."""

    def __init__(self, model_id):
        self.client = self.setup_azure_client()
        self.model_id = model_id

    def setup_azure_client(self):
        """Initializes and returns the Azure ChatCompletionsClient."""
        endpoint = os.getenv("AZURE_BASE_URL")
        key = os.getenv("AZURE_API_KEY")

        if not endpoint or not key:
            raise ValueError("Azure environment variables are not set correctly.")

        return ChatCompletionsClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    def ask(self, question, prompt):
        """Generates a response using Azure AI."""
        formatted_prompt = prompt
        messages = [SystemMessage(formatted_prompt), UserMessage(question)]

        try:
            completion = self.client.complete(messages=messages, max_tokens=20000, model=self.model_id, stream=True)
            response = [chunk.choices[0]["delta"]["content"] for chunk in completion if chunk.choices]
            return "".join(response)
        except Exception as e:
            print(f"Azure AI error: {e}")
            return None

class DeepSeekAIProvider(AIProvider):
    """Handles responses from Claude AI."""

    def __init__(self, provider, model_id, temperature):
        self.client = DeepseekModel(temperature)
        self.provider = provider
        self.model_id = model_id

    def ask(self, question, prompt):
        """Generates a response using Claude AI."""
        return self.client.ask_claude_with_stream(question, prompt, self.model_id, self.provider)


# === Claude AI Provider ===
class ClaudeAIProvider(AIProvider):
    """Handles responses from Claude AI."""

    def __init__(self, provider, model_id):
        self.client = ClaudeModel()
        self.provider = provider
        self.model_id = model_id

    def ask(self, question, prompt):
        """Generates a response using Claude AI."""
        return self.client.ask_claude_with_stream(question, prompt, self.model_id, self.provider)


# === Other AI Providers (e.g., AI Suite) ===
class OtherAIProvider(AIProvider):
    """Handles responses from other AI providers like AI Suite."""

    def __init__(self, provider, model_id, temperature, config= None):
        self.client = ai.Client(config) if config else ai.Client()
        self.provider = provider
        self.model_id = model_id
        self.temperature= temperature


    def ask(self, question, prompt):
        """Generates a response using AI Suite."""
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"{question}"},
        ]

        try:
            time.sleep(0.5)  # Simulate slight delay
            response = self.client.chat.completions.create(
                model=f"{self.provider}:{self.model_id}",
                messages=messages,
                temperature=self.temperature,
                topP=0,
                topK=0
            
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"AI Suite error: {e}")
            return None, None 
        
WORDS_MAP = {
    "partition": "PARTITION",
    "group_by": "PARTITION",
    "where": "WHERE",
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
    "sqrt": "SQRT",
    "calculate": "CALCULATE",
    "asc": "ASC",
    "desc": "DESC",
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

def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

def extract_python_code(text):
    """Extracts Python code from triple backticks in text."""
    if not isinstance(text, str):  # Ensure text is a string
        return ""

    match = re.search(r"```python\n(.*?)\n```", text, re.DOTALL)
    if match:
        python_code = match.group(1).strip()
        # Convert the extracted code to uppercase
        return python_code
    else:
        return ""

import os

def format_prompt(prompt, data, question, database_content, script_content):
    if question in data:
        recomendation = data[question].get("context_id", "")
        similar_code= data[question].get("similar_queries", "similar code not found")
        question = data[question].get("redefined_question", question)
    #contexts = (
    #    open(f"./data/pydough_files/{id}", 'r').read() if os.path.exists(f"./data/pydough_files/{id}") else ''
    #    for id in ids
    #)
    else:
        recomendation=""
        similar_code= "similar pydough code not found"
    #prompt_string = ' '.join(contexts)
    return question, prompt.format(script_content=script_content, database_content=database_content, similar_queries=similar_code, recomendation=recomendation)

def correct(client, question,  code, prompt):
    extracted_code= extract_python_code(code)
    local_env = {"pydough": pydough, "datetime": datetime}
    response= code    
    result, exception= execute_code_and_extract_result(extracted_code, local_env)
    
    if result is None:

        q= (f"""
        Review and correct the provided Pydough code based on the given exception and original question.
        - Analyze the provided Pydough code for syntax errors, logical errors, and exceptions.
        - Identify the specific line or section where the exception occurs. 
        - Consider the context of the original question to ensure that the code aligns with the intended functionality.
        - Do not assume if a method exists.
        - Follow the rules provided in pydough.    
        - Return the same output but with the corrected code.
        An error occurred while processing this code: {code}. 
        The error is: '{exception}'. 
        The original question was: '{question}'. 
        Can you help me fix the issue? Please make sure to use the right syntax and rules for creating pydough code.""")

        response=client.ask(q, prompt)

    return response
   
def get_azure_response(client, prompt, data, question, database_content, script_content):
    """Generates a response using Azure AI."""
    formatted_prompt = format_prompt(prompt,data,question,database_content, script_content)
    
    
    try:
        response= client.ask(question, formatted_prompt)
        corrected_response= correct(client,question,response, formatted_prompt)
        return corrected_response, None
    except Exception as e:
        print(f"Azure AI error: {e}")
        return None
    
def generate_hash(df):
    return hashlib.md5(pd.util.hash_pandas_object(df).values.tobytes()).hexdigest()


def ensembling_process(client, updated_question, formatted_prompt):
    """
    Performs an ensembling process to generate multiple responses from an AI client.
    Uses a direct comparison approach to identify matching results.
    """
    dfs_and_responses = []
    counts = defaultdict(list)

    try:
        for i in range(5):
            response = client.ask(updated_question, formatted_prompt)
            extracted_code = extract_python_code(response)
            local_env = {"pydough": pydough, "datetime": datetime}
            result, exception = execute_code_and_extract_result(extracted_code, local_env)

            if result is not None:
                dfs_and_responses.append((result, response))
            else:
                print(f"The PyDough code has the exception: {exception}")
        
        if dfs_and_responses == []:
            return response
        else: 
            for i in range(len(dfs_and_responses)):
                for j in range(i + 1, len(dfs_and_responses)):
                    df_gold = dfs_and_responses[i][0]
                    df_gen = dfs_and_responses[j][0]

                    if compare_df(
                        df_gold=df_gold,
                        df_gen=df_gen,
                        query_category="",
                        question=""
                    ):
                        counts[i].append(j)

            most_common_index = max(counts, key=lambda k: len(counts[k]), default=None)

            if most_common_index is not None:
                return dfs_and_responses[most_common_index][1]
            else:
                print("No common result found, returning the first response as fallback.")
                return dfs_and_responses[0][1] if dfs_and_responses else None

    except Exception as e:
        print(f"AI Suite error: {e}")
        return None



def get_other_provider_response(client, prompt, data, question, database_content,script_content):
    """Generates a response using aisuite."""
    updated_question, formatted_prompt = format_prompt(prompt,data,question,database_content,script_content)
   
    try:
        start_time = time.time()
        response = ensembling_process(client, updated_question,formatted_prompt)
        end_time = time.time()
        execution_time = end_time - start_time
        return response, execution_time
    except Exception as e:
        print(f"AI Suite error: {e}")
        return None

def get_claude_response(client, prompt, data, question, database_content, script_content):
    """Generates a response using aisuite."""
    updated_question, formatted_prompt = format_prompt(prompt,data,question,database_content,script_content)
    response= client.ask(updated_question, formatted_prompt)
    corrected_response = correct(client, updated_question, response,formatted_prompt)
    return corrected_response, None

def process_question_wrapper(args):
    """ Wrapper function to handle multiprocessing calls. """
    provider, model_id, formatted_prompt, data, q, temperature, database_content, script_content = args

    if provider == "azure":
        client = AzureAIProvider(model_id)
        return get_azure_response(client, formatted_prompt, data, q, database_content, script_content)
    elif provider == "aws-thinking":
        client = ClaudeAIProvider(provider, model_id)
        return get_claude_response(client, formatted_prompt, data, q, database_content, script_content)
    elif provider == "aws-deepseek":
        client = DeepSeekAIProvider(provider, model_id, temperature)
        return get_claude_response(client, formatted_prompt, data, q, database_content, script_content)
    else:
        client = OtherAIProvider(provider, model_id, temperature)
        return get_other_provider_response(client, formatted_prompt, data, q, database_content, script_content)

def process_questions(data, provider, model_id, formatted_prompt, questions, temperature, database_content, script_content):
    """ Processes questions in parallel using multiprocessing. """
    with multiprocessing.Pool(processes=1) as pool:  # Adjust process count as needed
        original_responses = pool.map(
            process_question_wrapper, 
            [(provider, model_id, formatted_prompt, data, q, temperature, database_content, script_content) for q in questions]
        )
    
    return original_responses

def parse_dict(value):
    try:
        return ast.literal_eval(value) 
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid dictionary: {value}")
    
def main(git_hash):
    # Argument Parser
    # this is an example: python prompt_evaluation.py  "Experiment for testing azure" "Azure test" cheatsheet_v4_examples.md tcph_graph.md prompt2.txt questions.csv google gemini-1.5-pro-001 --eval_results
    parser = argparse.ArgumentParser(description="Process a script file and questions CSV.")
    parser.add_argument("--description", type=str, default="MLFlow")
    parser.add_argument("--name", type=str, default="MLFlow project")
    parser.add_argument("--script_file", type=str, help="Path to the script file.")
    parser.add_argument("--database_structure", type=str, help="Path to the database file.")
    parser.add_argument("--prompt_file", type=str, help="Path to the prompt file.")
    parser.add_argument("--questions_csv", type=str, help="Path to the questions CSV file.")
    parser.add_argument("--provider", type=str, help="Model provider (either 'azure' or another provider).")
    parser.add_argument("--model_id", type=str, help="Model ID.")
    parser.add_argument("--temperature", type=float, help="Set the temperature to the model")
    parser.add_argument("--eval_results", action="store_true", help="Evaluate the LLM output against the ground truth data.")
    parser.add_argument("--eval_benchmark", action="store_true", help="Evaluate the TPCH Benchmark")
    parser.add_argument("--no-eval_results", action="store_false", dest="eval_results", help="Do not evaluate the LLM output.")
    parser.add_argument("--no-eval_benchmark", action="store_false", dest="eval_benchmark", help="Do not evaluate the TPCH Benchmark")
    parser.add_argument("--config", type=parse_dict, help="Path to the database file.", default=None)

    # Default value for eval_results and eval_benchmark is False
    parser.set_defaults(eval_results=False, eval_benchmark=False)
    args = parser.parse_args()
    
    # Create result directory if not exists
    folder_path = f"./results/{args.provider}/{args.model_id}"
    os.makedirs(folder_path, exist_ok=True)
    
    mlflow.set_tracking_uri("http://127.0.0.1:5000")
    expr_name = "text2pydough"  # create a new experiment (do not replace)
    #mlflow.create_experiment(expr_name, s3_bucket)
    experiment= mlflow.set_experiment(expr_name)
    with mlflow.start_run(description=args.description, run_name=args.name, tags={"GIT_COMMIT": git_hash},experiment_id=experiment.experiment_id):
        # Read Files Efficiently
        with open(args.prompt_file, "r", encoding="utf-8") as f:
            prompt = f.read()

        with open(args.script_file, "r", encoding="utf-8") as f:
            script_content = f.read()

        with open(args.database_structure, "r", encoding="utf-8") as f:
            database_content = f.read()

        with open("./queries_context.json","r") as json_data:
            data = json.load(json_data)

        # Read Questions
        questions_df = pd.read_csv(args.questions_csv, encoding="utf-8")

        # Format prompt once
        #formatted_prompt = prompt.format(script_content=script_content, database_content=database_content, similar_queries=similar_code)

        # Process questions
        #questions_df['instructions'] = questions_df['instructions'].fillna('')

        #questions_df['combined'] = questions_df['question'] + " " + questions_df['instructions']

        # Convert the 'combined' column into a list
        combined_list = questions_df['question'].tolist()

        responses = process_questions(data,args.provider.lower(), args.model_id, prompt, combined_list, args.temperature,database_content,script_content)

        # Save responses
        # Convert the responses into separate columns for 'response' and 'execution_time'
        response_column = [response[0] for response in responses]  # Extract corrected responses
        execution_time_column = [response[1] for response in responses]  # Extract execution times

        # Save responses and execution times into the DataFrame
        questions_df["response"] = response_column
        questions_df["execution_time"] = execution_time_column

        output_file = f"{folder_path}/responses_{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.csv"
        questions_df["extracted_python_code"] = questions_df["response"].apply(extract_python_code).apply(replace_with_upper)

        questions_df.to_csv(output_file, index=False, encoding="utf-8")

        if args.eval_results:
            folder_path = f"./results/{args.provider}/{args.model_id}/test"
            os.makedirs(folder_path, exist_ok=True)

            output_file, responses= compare_output(folder_path,output_file, "./test_data/tpch.db")
            total_rows = len(responses)

            counts = responses['comparison_result'].dropna().value_counts()
            percentages = counts / total_rows

            mlflow.log_metrics(
                    percentages,
                )
            mlflow.log_metric("total_script_queries", total_rows)
            mlflow.log_artifact(output_file)

        if args.eval_benchmark:
            folder_path = f"./results/{args.provider}/{args.model_id}/benchmark"
            os.makedirs(folder_path, exist_ok=True)
            questions_df = pd.read_csv("./benchmark.csv", encoding="utf-8")
            
            # Process questions
            responses = process_questions(data,args.provider.lower(), args.model_id, prompt, questions_df["question"].tolist(), args.temperature,database_content,script_content)
            questions_df["response"] = responses
            output_file = f"{folder_path}/responses_benchmark{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.csv"
            questions_df["extracted_python_code"] = questions_df["response"].apply(extract_python_code).apply(replace_with_upper)

            questions_df.to_csv(output_file, index=False, encoding="utf-8")
            output_file, responses= compare_output(folder_path,output_file, "./test_data/tpch.db")
            total_rows = len(responses)

            counts = responses['comparison_result'].dropna().value_counts()
            total = counts.sum()
            percentages = counts / total
            key_mapping = {
                'Match': 'Match_benchmark',
                'No Match': 'No_Match_benchmark',
                'Query error': 'Query_error_bechmark'
            }
            counts = counts.rename(key_mapping)
            percentages = percentages.rename(key_mapping)

            mlflow.log_metrics(
                    percentages
                )
            mlflow.log_metric("total_benchmark_queries", total_rows)

        mlflow.log_params(
            {
                "script_file": args.script_file,
                "database_structure": args.database_structure,
                "prompt_file": args.prompt_file,
                "prompt": prompt,
                "questions_file": args.questions_csv,
                "provider": args.provider,
                "model_id": args.model_id,
                "temperature": args.temperature
            }
        )
       
        mlflow.set_tag("llm_output", output_file)
        mlflow.set_tag("csv" ,responses) 
        mlflow.log_artifact(output_file)
    

if __name__ == "__main__":

    cwd = os.getcwd()
    untracked= untracked_files(cwd)
    modified= modified_files(cwd)
    
    if untracked or modified:
        autocommit(cwd)

    git_hash= get_git_commit(cwd)
    
    main(git_hash)