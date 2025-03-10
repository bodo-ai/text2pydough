import argparse
import json
import multiprocessing
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
import mlflow
from test_data.eval import compare_output, execute_code_and_extract_result
from utils import autocommit, get_git_commit, modified_files, untracked_files
from claude import ClaudeModel
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

    def __init__(self, provider, model_id, temperature):
        self.client = ai.Client()
        self.provider = provider
        self.model_id = model_id
        self.temperature= temperature


    def ask(self, question, prompt):
        """Generates a response using AI Suite."""
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ]

        try:
            time.sleep(0.5)  # Simulate slight delay
            response = self.client.chat.completions.create(
                model=f"{self.provider}:{self.model_id}",
                messages=messages,
                temperature=self.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"AI Suite error: {e}")
            return None
        
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
    "sqrt": "SQRT",
    "calculate": "CALCULATE",
    "asc": "ASC",
    "desc": "DESC",
    "datetime": "DATETIME",
    "datediff": "DATEDIFF"
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
        recomendation = data[question]["context_id"]
        similar_code= data[question].get("similar_queries", "similar code not found")
    #contexts = (
    #    open(f"./data/pydough_files/{id}", 'r').read() if os.path.exists(f"./data/pydough_files/{id}") else ''
    #    for id in ids
    #)
    else:
        recomendation=""
        similar_code= "similar pydough code not found"
    #prompt_string = ' '.join(contexts)
    return prompt.format(script_content=script_content, database_content=database_content, similar_queries=similar_code, recomendation=recomendation)

def correct(client, question,  code, prompt):
    extracted_code= extract_python_code(code)
    local_env = {"pydough": pydough, "datetime": datetime}
    response= code    
    result, exception= execute_code_and_extract_result(extracted_code, local_env)
    
    if result is None:

        q= (f"""An error occurred while processing this code: {extracted_code}. "
        The error is: '{exception}'. "
        The original question was: '{question}'. "
        Can you help me fix the issue? Please make sure to use the right syntax and rules for creating pydough code.""")

        response=client.ask(q, prompt)

    return response
   
def get_azure_response(client, prompt, data, question, database_content, script_content):
    """Generates a response using Azure AI."""
    formatted_prompt = format_prompt(prompt,data,question,database_content, script_content)
    
    
    try:
        response= client.ask(question, formatted_prompt)
        corrected_response= correct(client,question,response, formatted_prompt)
        return corrected_response
    except Exception as e:
        print(f"Azure AI error: {e}")
        return None

def get_other_provider_response(client, prompt, data, question, database_content,script_content):
    """Generates a response using aisuite."""
    formatted_prompt = format_prompt(prompt,data,question,database_content,script_content)
   
    try:
        time.sleep(0.5)
        response=client.ask(question,formatted_prompt)
        corrected_response= correct(client, question, response,formatted_prompt)
        return corrected_response
    except Exception as e:
        print(f"AI Suite error: {e}")
        return None

def get_claude_response(client, prompt, data, question, database_content, script_content):
    """Generates a response using aisuite."""
    formatted_prompt = format_prompt(prompt,data,question,database_content,script_content)
    response= client.ask(question, formatted_prompt)
    corrected_response = correct(client, question, response,formatted_prompt)
    return corrected_response

def process_question_wrapper(args):
    """ Wrapper function to handle multiprocessing calls. """
    provider, model_id, formatted_prompt, data, q, temperature, database_content, script_content = args

    if provider == "azure":
        client = AzureAIProvider(model_id)
        return get_azure_response(client, formatted_prompt, data, q, database_content, script_content)
    elif provider == "aws-thinking":
        client = ClaudeAIProvider(provider, model_id)
        return get_claude_response(client, formatted_prompt, data, q, database_content, script_content)
    else:
        client = OtherAIProvider(provider, model_id, temperature)
        return get_other_provider_response(client, formatted_prompt, data, q, database_content, script_content)

def process_questions(data, provider, model_id, formatted_prompt, questions, temperature, database_content, script_content):
    """ Processes questions in parallel using multiprocessing. """
    with multiprocessing.Pool(processes=10) as pool:  # Adjust process count as needed
        original_responses = pool.map(
            process_question_wrapper, 
            [(provider, model_id, formatted_prompt, data, q, temperature, database_content, script_content) for q in questions]
        )
    
    return original_responses

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
        responses = process_questions(data,args.provider.lower(), args.model_id, prompt, questions_df["question"].tolist(), args.temperature,database_content,script_content)

        # Save responses
        questions_df["response"] = responses
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

        if args.eval_benchmark:
            folder_path = f"./results/{args.provider}/{args.model_id}/benchmark"
            os.makedirs(folder_path, exist_ok=True)
            questions_df = pd.read_csv("./TPCH Queries - All Queries.csv", encoding="utf-8")
            
            # Process questions
            responses = process_questions(args.provider.lower(), args.model_id, prompt, questions_df["question"].tolist(), args.temperature)
            questions_df["response"] = responses
            output_file = f"{folder_path}/responses_{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.csv"
            questions_df["extracted_python_code"] = questions_df["response"].apply(extract_python_code).apply(replace_with_upper)

            questions_df.to_csv(output_file, index=False, encoding="utf-8")
            output_file, responses= compare_output(folder_path,output_file, "./test_data/tpch.db")
            total_rows = len(responses)

            counts = responses['comparison_result'].dropna().value_counts()
            total = counts.sum()
            percentages = counts / total
            key_mapping = {
                'Match': 'Match_benchmark',
                'No match': 'No_Match_benchmark',
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