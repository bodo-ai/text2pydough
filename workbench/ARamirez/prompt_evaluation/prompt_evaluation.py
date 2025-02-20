import argparse
import os
import re
import time
import pandas as pd
import aisuite as ai
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import UserMessage, SystemMessage
from azure.core.credentials import AzureKeyCredential
from azure.core.pipeline.transport import RequestsTransport
import mlflow
from test_data.eval import compare_output
from utils import autocommit, get_git_commit, modified_files, untracked_files

def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

def setup_azure_client():
    """Initializes and returns the Azure ChatCompletionsClient."""
    endpoint = os.getenv("AZURE_BASE_URL")
    key = os.getenv("AZURE_API_KEY")

    if not endpoint or not key:
        raise ValueError("Azure environment variables are not set correctly.")

    # Configure the transport with a timeout of 800 seconds
    transport = RequestsTransport(read_timeout=800)

    return ChatCompletionsClient(endpoint=endpoint, credential=AzureKeyCredential(key), transport=transport)

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
        response = client.complete(messages=messages, max_tokens=800, model=model_id)
        return response.choices[0].message.content
    except Exception as e:
        print(f"Azure AI error: {e}")
        return None

def get_other_provider_response(client, provider, model_id, prompt, question):
    """Generates a response using aisuite."""
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": question},
    ]
    
    try:
        response = client.chat.completions.create(
            model=f"{provider}:{model_id}",
            messages=messages,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"AI Suite error: {e}")
        return None

def process_questions(provider, model_id, formatted_prompt, questions):
    responses = []
    
    if provider == "azure":
        client = setup_azure_client()
        get_response = lambda q: get_azure_response(client, formatted_prompt, q, model_id)
    else:
        client = ai.Client()
        get_response = lambda q: get_other_provider_response(client, provider, model_id, formatted_prompt, q)
    
    with ThreadPoolExecutor(max_workers=1) as executor:
        responses = list(executor.map(get_response, questions))

    return responses

def main(git_hash):
    # Argument Parser
    parser = argparse.ArgumentParser(description="Process a script file and questions CSV.")
    parser.add_argument("description", type=str, default="MLFlow")
    parser.add_argument("name", type=str, default="MLFlow project")
    parser.add_argument("script_file", type=str, help="Path to the script file.")
    parser.add_argument("database_structure", type=str, help="Path to the database file.")
    parser.add_argument("prompt_file", type=str, help="Path to the prompt file.")
    parser.add_argument("questions_csv", type=str, help="Path to the questions CSV file.")
    parser.add_argument("provider", type=str, help="Model provider (either 'azure' or another provider).")
    parser.add_argument("model_id", type=str, help="Model ID.")
   # Use `store_true` to set eval_results to True if argument is passed
    parser.add_argument("--eval_results", action="store_true", help="Evaluate the LLM output against the ground truth data.")
    
    # Use `store_false` if --no-eval_results is passed
    parser.add_argument("--no-eval_results", action="store_false", dest="eval_results", help="Do not evaluate the LLM output.")

    # Default value for eval_results is False
    parser.set_defaults(eval_results=False)
    args = parser.parse_args()

    # Create result directory if not exists
    folder_path = f"./results/{args.provider}/{args.model_id}"
    os.makedirs(folder_path, exist_ok=True)
    
    mlflow.set_tracking_uri("http://127.0.0.1:5000")

    with mlflow.start_run(description=args.description, run_name=args.name, tags={"GIT_COMMIT": git_hash}):
        # Read Files Efficiently
        with open(args.prompt_file, "r", encoding="utf-8") as f:
            prompt = f.read()

        with open(args.script_file, "r", encoding="utf-8") as f:
            script_content = f.read()

        with open(args.database_structure, "r", encoding="utf-8") as f:
            database_content = f.read()

        # Read Questions
        questions_df = pd.read_csv(args.questions_csv, encoding="utf-8")
        questions = questions_df["question"].tolist()

        # Format prompt once
        formatted_prompt = prompt.format(script_content=script_content, database_content=database_content)

        # Process questions
        responses = process_questions(args.provider.lower(), args.model_id, formatted_prompt, questions_df["question"].tolist())

        # Save responses
        questions_df["response"] = responses
        output_file = f"{folder_path}/responses_{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.csv"
        questions_df["extracted_python_code"] = questions_df["response"].apply(extract_python_code)

        questions_df.to_csv(output_file, index=False, encoding="utf-8")

        if args.eval_results:
            folder_path = f"./results/{args.provider}/{args.model_id}/test"
            os.makedirs(folder_path, exist_ok=True)

            output_file, responses= compare_output(folder_path,output_file, "./test_data/tpch.db")
        
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
        #mlflow.log_artifact(output_file)
    

if __name__ == "__main__":

    cwd = os.getcwd()
    untracked= untracked_files(cwd)
    modified= modified_files(cwd)
    
    if untracked or modified:
        autocommit(cwd)

    git_hash= get_git_commit(cwd)
    
    main(git_hash)