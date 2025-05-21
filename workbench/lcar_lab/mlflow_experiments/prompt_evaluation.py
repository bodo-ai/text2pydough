# main.py

import argparse
import json
import os
import re
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
import aisuite as ai
from provider.ai_providers import *
from dynamic_prompt.generate_pydough_metadata import generate_metadata
from dynamic_prompt.mdgen import json_to_markdown
from sqlalchemy import create_engine, inspect, text
from gemini_wrapper import GeminiWrapper

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
    elif provider == "mistral":
        return MistralAIProvider(model_id)
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
    matches = re.findall(r"```python\n(.*?)```", text, re.DOTALL)
    return textwrap.dedent(matches[-1]).strip() if matches else ""

def prepare_db_markdown_map(df, metadata_base_path, db_base_path):
    db_names = df["db_name"]
    dataset_names = df["dataset_name"]
    db_markdown_map = {}
    print(f"[INFO] Preparing DB markdown map for {len(db_names)} databases in metadata base path: {metadata_base_path}")
    for db_name, dataset_name in zip(db_names, dataset_names):
        metadata_dir = os.path.join(metadata_base_path, dataset_name, "metadata")
        json_file = os.path.join(metadata_dir, f"{db_name}_graph.json")
        print(json_file)
        # Only generate if missing
        if not os.path.exists(json_file):
            print(f"[INFO] Generating JSON for: {db_name}")
            url = f"sqlite:///{os.path.join(db_base_path, dataset_name, "databases", f"{db_name}/{db_name}.sqlite")}"
            engine = create_engine(url)
            md= generate_metadata(engine,db_name)
            with open(json_file, "w") as f:
                json.dump(md, f, indent=2)

        if db_name not in db_markdown_map:
            with open(json_file, "r") as f:
                data = json.load(f)
                db_markdown_map[db_name] = data

    return db_markdown_map

def format_prompt(prompt, data, question, script, db_name=None, db_markdown_map=None):
    db_content = ""
    if db_name and db_markdown_map and db_name in db_markdown_map:
        db_content = db_markdown_map[db_name]

    recommendation = data.get(question, {}).get("context_id", "")
    similar_code = data.get(question, {}).get("similar_queries", "similar pydough code not found")
    question = data.get(question, {}).get("redefined_question", question)
    return "".join([f"\n\n\nQuestion: {question}\n", "\nDatabase schema:\n", str(db_content)]), prompt.format(
        script_content=script,
        database_content=json_to_markdown(db_content),
        similar_queries=similar_code,
        recomendation=recommendation
    )

def correct(client, question, code, prompt, db_name):
    extracted_code = extract_python_code(code)
    env= {"pydough": pydough, "datetime": datetime}
    print(extracted_code)
    result, error = execute_code_and_extract_result(extracted_code, env, db_name)
    if result is None:
        q = f"""Fix this Pydough code: {code}. Error: {error}. Question: {question}."""
        response = client.ask(q, prompt)
        if isinstance(response, tuple):  # Gemini returns (text, usage)
            return  "".join([code, response[0]])
        return "".join([code, response])
    return code

def get_response(client, prompt, data, row, script, db_markdown_map=None, **kwargs):
    question = row["question"]
    db_name = row.get("db_name", None)
    formatted_q, formatted_prompt = format_prompt(prompt, data, question, script, db_name, db_markdown_map)
    start = time.time()
    response1 = client.ask(formatted_q,formatted_prompt, **kwargs)
    duration = time.time() - start
    if isinstance(response1, tuple):  # Gemini returns (text, usage)
        #response= correct(client, formatted_q, response1[0], formatted_prompt, db_name=db_name)
        return response1[0], duration, response1[1]
    #response= correct(client, formatted_q, response1, formatted_prompt, db_name=db_name)
    return response1, duration, None

def process_questions(data, provider, model_id, prompt, questions_df, script, threads, db_markdown_map=None, **kwargs):
    def thread_wrapper(row):
        client = get_provider(provider, model_id)
        return get_response(client, prompt, data, row, script, db_markdown_map=db_markdown_map, **kwargs)

    with ThreadPoolExecutor(max_workers=threads) as executor:
        results = list(executor.map(thread_wrapper, [row for _, row in questions_df.iterrows()]))

    return results

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
    parser.add_argument("--experiment_name", type=str)
    parser.add_argument('--db-base-path', type=str, required=True,
                      help='Path to the SQLite database file')
    parser.add_argument('--metadata-base-path', type=str, required=True,
                      help='Path to the metadata graph JSON file')
    parser.add_argument("--pydough_file", type=str)
    parser.add_argument("--prompt_file", type=str)
    parser.add_argument("--questions", type=str)
    parser.add_argument("--provider", type=str)
    parser.add_argument("--model_id", type=str)
    parser.add_argument("--num_threads", type=int)
    parser.add_argument("--extra_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    kwargs = parse_extra_args(args.extra_args)
    MLFLOW_TRACKING_URI = "http://mlflow-alb-1071096006.us-east-2.elb.amazonaws.com"
    MLFLOW_TRACKING_TOKEN = os.environ["MLFLOW_TRACKING_TOKEN"] 
    mlflow.gemini.autolog()
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    experiment = mlflow.set_experiment("epoch change")
    with mlflow.start_run(description=args.description, run_name=args.name, tags={"GIT_COMMIT": git_hash}, experiment_id=experiment.experiment_id):

        prompt = read_file(args.prompt_file)
        script = read_file(args.pydough_file)

        with open("./queries_context.json") as f:
            data = json.load(f)

        df = pd.read_csv(args.questions)
        db_markdown_map = prepare_db_markdown_map(df, args.metadata_base_path, args.db_base_path)

        results = process_questions(data, args.provider.lower(), args.model_id, prompt, df, script, args.num_threads, db_markdown_map=db_markdown_map, **kwargs)

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
        tested_file, tested_df = compare_output(test_path, output_file, args.db_base_path, args.metadata_base_path)
        total_rows = len(tested_df)

        counts = tested_df['comparison_result'].value_counts()
        percentages = counts / total_rows
        filtered_args = {key: value for key, value in vars(args).items() if key not in ['name', 'description','extra_args']}

        mlflow.log_params(filtered_args)
        mlflow.log_params(kwargs)
        mlflow.log_metrics(percentages)
        mlflow.log_metric("total_queries", len(tested_df))
        mlflow.log_artifact(tested_file)

        percentages_dict = percentages.to_dict()
        metrics_json = json.dumps(percentages_dict, indent=4)

        metrics_path = "./metrics.json"
        with open(metrics_path, "w") as metrics_file:
            metrics_file.write(metrics_json)

        mlflow.pyfunc.log_model(
            artifact_path=args.model_id,
            python_model=GeminiWrapper(model_id=args.model_id),
            artifacts={
                "prompt_file": args.prompt_file,
                "pydough_file": args.pydough_file,
                "metrics.json": metrics_path
            }
        )

if __name__ == "__main__":
    cwd = os.getcwd()
    db_path = './test_data/TPCH.db'
    download_database(db_path)
    if untracked_files(cwd) or modified_files(cwd):
        autocommit(cwd)
    main(get_git_commit(cwd))