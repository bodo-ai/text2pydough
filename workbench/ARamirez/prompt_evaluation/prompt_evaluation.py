# main.py

import argparse
import json
import os
import re
import textwrap
import time
import pandas as pd
from datetime import datetime
import multiprocessing
import mlflow
from concurrent.futures import ThreadPoolExecutor
import pydough
from utils import autocommit, get_git_commit, modified_files, untracked_files, download_database
from test_data.eval import compare_output, execute_code_and_extract_result
from claude import ClaudeModel, DeepseekModel, GeminiModel
import aisuite as ai
from provider.ai_providers import *
from dynamic_prompt.generate_pydough_metadata import generate_metadata
from dynamic_prompt.mdgen import json_to_markdown
from sqlalchemy import create_engine, inspect, text

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

def prepare_db_markdown_map(df, base_path="test_data"):
    db_names = df["db_name"].dropna().unique()
    db_markdown_map = {}

    for db_name in db_names:
        json_file = os.path.join(base_path, f"{db_name}_graph.json")
        
        # Only generate if missing
        if not os.path.exists(json_file):
            print(f"[INFO] Generating JSON for: {db_name}")
            url = f"sqlite:///{os.path.join(base_path, f"{db_name}.db")}"
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

    return question, prompt.format(
        script_content=script,
        database_content=db_content,
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
    response1 = client.ask(formatted_q, formatted_prompt, **kwargs)
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

        with open("./queries_context.json") as f:
            data = json.load(f)

        df = pd.read_csv(args.questions)
        db_markdown_map = prepare_db_markdown_map(df)

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
        tested_file, tested_df = compare_output(test_path, output_file)
        total_rows = len(tested_df)

        counts = tested_df['comparison_result'].value_counts()
        percentages = counts / total_rows
        filtered_args = {key: value for key, value in vars(args).items() if key not in ['name', 'description','extra_args']}

        mlflow.log_params(filtered_args)
        mlflow.log_params(kwargs)
        mlflow.log_metrics(percentages)
        mlflow.log_metric("total_queries", len(tested_df))
        mlflow.log_artifact(tested_file)

if __name__ == "__main__":
    cwd = os.getcwd()
    db_path = './test_data/TPCH.db'
    download_database(db_path)
    if untracked_files(cwd) or modified_files(cwd):
        autocommit(cwd)
    main(get_git_commit(cwd))