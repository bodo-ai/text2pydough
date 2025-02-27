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
import mlflow
from test_data.eval import compare_output
from utils import autocommit, get_git_commit, modified_files, untracked_files

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

def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

def setup_azure_client():
    """Initializes and returns the Azure ChatCompletionsClient."""
    endpoint = os.getenv("AZURE_BASE_URL")
    key = os.getenv("AZURE_API_KEY")

    if not endpoint or not key:
        raise ValueError("Azure environment variables are not set correctly.")

    return ChatCompletionsClient(endpoint=endpoint, credential=AzureKeyCredential(key))

def extract_python_code(text):
    """Extracts Python code from triple backticks in text."""
    if not isinstance(text, str):  # Ensure text is a string
        return ""

    match = re.search(r"```python\n(.*?)\n```", text, re.DOTALL)
    return match.group(1).strip() if match else ""

def get_azure_response(client, prompt, question, model_id):
    """Generates a response using Azure AI."""
    messages = [SystemMessage(prompt), UserMessage(question)]
    
    try:
        completion = client.complete(messages=messages, max_tokens=20000, model=model_id, stream=True)
        response = []
        for chunck in completion:
            if chunck.choices != []:
                response.append(chunck.choices[0]["delta"]["content"])
        result = "".join(response)
        return result
    except Exception as e:
        print(f"Azure AI error: {e}")
        return None

def get_other_provider_response(client, provider, model_id, prompt, question,temperature):
    """Generates a response using aisuite."""
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": question},

        #{"role": "system", "content": "You are a helpful assistant that can answer questions about PyDough queries a SQL-like language. Use the reference below to answer questions in PyDough "},
        #{"role": "user", "content": f"Using the following reference: {prompt} \n Answer the following question: {question}"},
    ]
    
    try:
        time.sleep(0.5)
        response = client.chat.completions.create(
            model=f"{provider}:{model_id}",
            messages=messages,
            temperature= temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"AI Suite error: {e}")
        return None

def process_questions(provider, model_id, formatted_prompt, questions, temperature):
    responses = []
    
    if provider == "azure":
        client = setup_azure_client()
        get_response = lambda q: get_azure_response(client, formatted_prompt, q, model_id)
    else:
        client = ai.Client()
        get_response = lambda q: get_other_provider_response(client, provider, model_id, formatted_prompt, q, temperature)
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        responses = list(executor.map(get_response, questions))

    return responses

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

        # Debugging the argument values
    print(f"Eval Results: {args.eval_results}")
    print(f"Eval Benchmark: {args.eval_benchmark}")
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

        # Read Questions
        questions_df = pd.read_csv(args.questions_csv, encoding="utf-8")
        similar_code = questions_df["similar_queries"].tolist()

        # Format prompt once
        formatted_prompt = prompt.format(script_content=script_content, database_content=database_content, similar_queries=similar_code)

        # Process questions
        responses = process_questions(args.provider.lower(), args.model_id, formatted_prompt, questions_df["question"].tolist(), args.temperature)

        # Save responses
        questions_df["response"] = responses
        output_file = f"{folder_path}/responses_{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.csv"
        questions_df["extracted_python_code"] = questions_df["response"].apply(extract_python_code).apply(replace_with_upper)

        questions_df.to_csv(output_file, index=False, encoding="utf-8")

        if args.eval_results:
            print("eval results if")
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
            
            # Format prompt once
            formatted_prompt = prompt.format(script_content=script_content, database_content=database_content, similar_queries=similar_code)

            # Process questions
            responses = process_questions(args.provider.lower(), args.model_id, formatted_prompt, questions_df["question"].tolist(), args.temperature)
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
                "model_id": args.model_id
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