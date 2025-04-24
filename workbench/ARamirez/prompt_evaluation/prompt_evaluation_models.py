# main.py

import argparse
import io
import json
import os
import re
import tempfile
import textwrap
import time
from typing import List
import pandas as pd
from datetime import datetime
import multiprocessing
import mlflow
import mlflow.pyfunc
from mlflow.pyfunc import PythonModel
from concurrent.futures import ThreadPoolExecutor
import pydough
from utils import autocommit, get_git_commit, modified_files, untracked_files, download_database
from test_data.eval import compare_output, execute_code_and_extract_result
from claude import ClaudeModel, DeepseekModel, GeminiModel
import aisuite as ai
from provider.ai_providers import *

class GeminiWrapper(PythonModel):
    def __init__(self, model_id):
        self.model_id = model_id

    def load_context(self, context):
        self.client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    def predict(self, context, model_input: List[str]) -> List[str]:
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=model_input
        )
        return [response.text]
    
# === Helper Functions ===

def get_provider(provider, model_id, config=None):
    if provider == "azure":
        return AzureAIProvider(model_id)
    elif provider == "aws-thinking":
        return ClaudeAIProvider(model_id)
    elif provider == "aws-deepseek":
        return DeepSeekAIProvider(model_id)
    elif provider == "google":
        return GeminiAIProvider(model_id)
    else:
        return OtherAIProvider(provider, model_id, config)
    
def read_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise IOError(f"Failed to read file {path}: {e}")

def extract_python_code(text):
    if not isinstance(text, str): return ""
    matches = re.findall(r"```(?:\w+\n)?(.*?)```", text, re.DOTALL)
    return textwrap.dedent(matches[-1]).strip() if matches else ""

def format_prompt(prompt, data, question, script, db_name=None):
    if db_name:
        db_content = read_file(f"{os.path.dirname(__file__)}/data/database/{db_name}_graph.md")
    recommendation = data.get(question, {}).get("context_id", "")
    similar_code = data.get(question, {}).get("similar_queries", "similar pydough code not found")
    question = data.get(question, {}).get("redefined_question", question)
    return question, prompt.format(script_content=script, database_content=db_content,
                                   similar_queries=similar_code, recomendation=recommendation)

def correct(client, question, code, prompt, db_name=None):
    extracted_code = extract_python_code(code)
    result, error = execute_code_and_extract_result(extracted_code, {"pydough": pydough, "datetime": datetime}, db_name)
    if result is None:
        q = f"""Fix this Pydough code: {code}. Error: {error}. Question: {question}."""
        response = client.ask(q, prompt)
        return "".join([code, response])
    return code

def get_response(client, prompt, data, row, script, **kwargs):
    question = row["question"]
    db_name = row.get("db_name", None)
    formatted_q, formatted_prompt = format_prompt(prompt, data, question, script, db_name)
    start = time.time()
    response = client.ask(formatted_q, formatted_prompt, **kwargs)
    duration = time.time() - start

    if isinstance(response, tuple):  # Gemini returns (text, usage)
        return response[0], duration, response[1]
    return response, duration, None

def process_questions(data, provider, model_id, prompt, questions_df, script, threads, **kwargs):
    def thread_wrapper(row):
        client = get_provider(provider, model_id)

        return get_response(client, prompt, data, row, script, **kwargs)

    with ThreadPoolExecutor(max_workers=threads) as executor:
        results = list(executor.map(thread_wrapper, [row for _, row in questions_df.iterrows()]))

    return results


# === CLI Parser ===
def parse_extra_args(extra_args):
    kwargs = {}
    if extra_args:
        key = None
        for arg in extra_args:
            if arg.startswith("--"):
                key = arg.lstrip("--")
            elif key:
                try:
                    value = int(arg)
                except ValueError:
                    try:
                        value = float(arg)
                    except ValueError:
                        if arg.lower() == "true": value = True
                        elif arg.lower() == "false": value = False
                        else: value = arg
                kwargs[key] = value
                key = None
    return kwargs

# === Entry Point ===
def main(git_hash):
    parser = argparse.ArgumentParser()
    parser.add_argument("--description", type=str, default="MLFlow")
    parser.add_argument("--name", type=str, default="MLFlow project")
    parser.add_argument("--pydough_file", type=str)
    parser.add_argument("--prompt_file", type=str)
    parser.add_argument("--questions", type=str)
    parser.add_argument("--provider", type=str)
    parser.add_argument("--model_id", type=str)
    parser.add_argument("--num_threads", type=int)
    parser.add_argument("--extra_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    kwargs = parse_extra_args(args.extra_args)

    mlflow.set_tracking_uri("http://127.0.0.1:5000")
    experiment = mlflow.set_experiment("text2pydough")
    with mlflow.start_run(description=args.description, run_name=args.name, tags={"GIT_COMMIT": git_hash}, experiment_id=experiment.experiment_id):
        prompt = read_file(args.prompt_file)
        script = read_file(args.pydough_file)
        with open("./queries_context.json") as f: data = json.load(f)
        df = pd.read_csv(args.questions)
        results = process_questions(data, args.provider.lower(), args.model_id, prompt, df, script, args.num_threads, **kwargs)

        df["response"] = [r[0] for r in results]
        df["execution_time"] = [r[1] for r in results]
        df["extracted_python_code"] = df["response"].apply(extract_python_code)
        df["usage"] = [r[2] if len(r) > 2 else None for r in results]

        output_path = f"./results/{args.provider}/{args.model_id}"
        os.makedirs(output_path, exist_ok=True)
        output_file = f"{output_path}/responses_{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.csv"
        df.to_csv(output_file, index=False)

        test_path = f"{output_path}/test"
        os.makedirs(test_path, exist_ok=True)
        tested_file, tested_df = compare_output(test_path, output_file)
        total_rows = len(tested_df)

        counts = tested_df['comparison_result'].value_counts()
        percentages = counts / total_rows
        filtered_args = {key: value for key, value in vars(args).items() if key not in ['name', 'description','extra_args']}

        mlflow.log_params(filtered_args)
        mlflow.log_params(kwargs)
        mlflow.log_metrics(
            percentages,
        )
        mlflow.log_metric("total_queries", len(tested_df))
        mlflow.log_artifact(tested_file)

        percentages_dict = percentages.to_dict()  
        metrics_json = json.dumps(percentages_dict, indent=4) 


        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as temp_metrics_file:
            temp_metrics_file.write(metrics_json)
            temp_metrics = temp_metrics_file.name

        mlflow.pyfunc.log_model(
            artifact_path="Gemini Model",
            python_model=GeminiWrapper(model_id=args.model_id),
            artifacts={
                "prompt_file": args.prompt_file,
                "pydough_file": args.pydough_file,
                "metrics.json": temp_metrics
            }
        )

if __name__ == "__main__":
    cwd = os.getcwd()
    db_path = './test_data/TPCH.db'
    download_database(db_path)
    if untracked_files(cwd) or modified_files(cwd):
        autocommit(cwd)
    main(get_git_commit(cwd))

# %%