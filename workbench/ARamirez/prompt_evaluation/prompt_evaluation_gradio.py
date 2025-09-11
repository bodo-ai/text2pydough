# prompt_evaluation.py

import argparse
import json
import os
import sys
import re
import textwrap
import time
from typing import List
import pandas as pd
from pydough import parse_json_metadata_from_file
from datetime import datetime
import multiprocessing
import mlflow
from mlflow.pyfunc import PythonModel
from concurrent.futures import ThreadPoolExecutor
import pydough
from utils import autocommit, get_git_commit, modified_files, untracked_files, download_database
from test_data.eval import custom_eval, execute_code_and_extract_result, compare_df, symetric_compare_df
import aisuite as ai
from provider.ai_providers_v2 import *
from dynamic_prompt.generate_pydough_metadata import generate_metadata
from dynamic_prompt.mdgen_v2 import json_to_markdown
from sqlalchemy import create_engine, inspect, text
from gemini_wrapper import GeminiWrapper
from collections import defaultdict
import random
import json
import gradio_agent_v2
from contextlib import contextmanager
from gradio_agent import process_question as gradio_process_question
from dotenv import load_dotenv
from pathlib import Path
from profile_to_metadata import map_all_profiles_to_markdown, map_all_profiles_to_metadata_format
from dynamic_prompt.mdgen_v2 import generate_markdown_from_metadata
from ensemble_logic import ensemble_result

# === Custom Tee class for dual output ===
class Tee:
    """
    A class that writes to multiple file-like objects simultaneously.
    Useful for writing to both terminal and file at the same time.
    """
    def __init__(self, *files):
        self.files = files
    
    def write(self, data):
        for f in self.files:
            f.write(data)
            f.flush()  # Ensure immediate output
    
    def flush(self):
        for f in self.files:
            f.flush()

# === Timeout helpers (60s) ===
def _execute_code_child(extracted_code, cheatsheet_path, db_name, database_path, start_of_week="Monday"):
    # Recreate minimal environment in the child process to avoid pickling issues
    import pydough as _pydough
    from datetime import datetime as _datetime
    from test_data.eval import execute_code_and_extract_result as _inner_exec
    env = {"pydough": _pydough, "datetime": _datetime}
    return _inner_exec(extracted_code, env, cheatsheet_path, db_name, database_path, start_of_week=start_of_week)

# Top-level runner function for multiprocessing (must be picklable on spawn-based platforms like macOS/Windows)
def _mp_runner(q, fn, a, k):
    try:
        res = fn(*a, **k)
        q.put(("ok", res))
    except BaseException as e:
        # Return the exception as a string to avoid pickling issues
        try:
            q.put(("err", str(e)))
        except Exception:
            q.put(("err", "Unhandled error in child process"))

# Top-level wrapper for calling gradio agent in a child process
def _gradio_agent_child(*c_args, **c_kwargs):
    import gradio_agent_v2 as _gav2
    return _gav2.process_question(*c_args, **c_kwargs)

def _call_in_process_with_timeout(target, args=(), kwargs=None, timeout_seconds=60, label=""):
    import multiprocessing as _mp
    if kwargs is None:
        kwargs = {}
    result_queue = _mp.Queue()

    p = _mp.Process(target=_mp_runner, args=(result_queue, target, args, kwargs))
    p.daemon = True
    p.start()
    try:
        status, payload = result_queue.get(timeout=timeout_seconds)
    except Exception:
        if p.is_alive():
            p.terminate()
        p.join()
        try:
            name = label or getattr(target, "__name__", "<call>")
        except Exception:
            name = label or "<call>"
        print(f"[TIMEOUT] {name} exceeded {timeout_seconds} seconds. Terminated child process.")
        return None, f"Timeout after {timeout_seconds} seconds"
    else:
        p.join()
        if status == "ok":
            return payload, None
        return None, payload

def execute_code_with_timeout(extracted_code, cheatsheet_path, db_name, database_path, start_of_week="Monday", timeout_seconds=60):
    payload, err = _call_in_process_with_timeout(
        _execute_code_child,
        args=(extracted_code, cheatsheet_path, db_name, database_path, start_of_week),
        timeout_seconds=timeout_seconds,
        label="execute_code_and_extract_result",
    )
    if err:
        return None, err, None
    return payload

def gradio_process_question_with_timeout(*args, timeout_seconds=180, **kwargs):
    payload, err = _call_in_process_with_timeout(
        _gradio_agent_child, args=args, kwargs=kwargs, timeout_seconds=timeout_seconds, label="gradio_agent_v2.process_question"
    )
    if err:
        return {"dataframe": None}
    return payload

# === Credential for google cloud ===
def load_google_credentials(selected_keys=[1]):
    """
    Load Google API credentials based on selected key indices (1-based).
    If selected_keys is None, load just key number 1.
    Sets the global google_credentials variable.
    """
        # Find the .env file in your home directory
    env_path = ".env"
    load_dotenv(dotenv_path=env_path)
    global google_credentials
    all_credentials = [
        [os.getenv("GOOGLE_API_KEY_1"), os.getenv("GOOGLE_PROJECT_ID_1")],
        [os.getenv("GOOGLE_API_KEY_2"), os.getenv("GOOGLE_PROJECT_ID_2")],
        [os.getenv("GOOGLE_API_KEY_3"), os.getenv("GOOGLE_PROJECT_ID_3")],
        [os.getenv("GOOGLE_API_KEY_4"), os.getenv("GOOGLE_PROJECT_ID_4")],
        [os.getenv("GOOGLE_API_KEY_5"), os.getenv("GOOGLE_PROJECT_ID_5")],
        [os.getenv("GOOGLE_API_KEY_6"), os.getenv("GOOGLE_PROJECT_ID_6")],
    ]
    if selected_keys is None:
        selected_keys = [1]
    indices = [int(k) - 1 for k in selected_keys if 1 <= int(k) <= 6]
    google_credentials = [all_credentials[i] for i in indices]
    

# === Helper Functions ===

def get_provider(provider, model_id, config=None):
    backend = config.get("backend", "vertex") if config else "vertex"

    if provider == "anthropic":
        return ClaudeAIProvider(model_id, config=config)
    elif provider == "azure":
        return AzureAIProvider(model_id, config=config)
    elif provider == "aws-deepseek":
        return DeepSeekAIProvider(model_id, config=config)
    elif provider == "google":
        return GeminiAIProvider(model_id, config=config)
    elif provider == "mistral":
        return MistralAIProvider(model_id, config=config)
    elif provider == "qwen":
        return QwenAIProvider(model_id, config=config)
    elif provider == "Chatgpt-oss":
        return ChatgptOssAIProvider(model_id, config=config)
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
    if not isinstance(text, str):
        return ""
    
    # Try to extract code from a python code block
    matches = re.findall(r"```python\n(.*?)```", text, re.DOTALL)
    if matches:
        return textwrap.dedent(matches[-1]).strip()
    
    answer_match = re.search(r"Answer:\s*(.*)", text, flags=re.IGNORECASE | re.DOTALL)

    if answer_match:
        print(f"[DEBUG] Extracted answer split: {answer_match.group(1).strip()}")

        answer_text = answer_match.group(1).strip()
        return answer_text
    
    return ""

def prepare_db_markdown_map(df, metadata_base_path, db_base_path):
    db_names = df["db_name"]
    dataset_names = df["dataset_name"]
    db_markdown_map = {}
    for db_name, dataset_name in zip(db_names, dataset_names):
        json_file = os.path.join(metadata_base_path, dataset_name, "metadata", f"{db_name}_graph.json")
        print(json_file)
        # Only generate if missing
        if not os.path.exists(json_file):
            print(f"[INFO] Generating JSON for: {db_name}")
            url = f"sqlite:///{os.path.join(db_base_path, dataset_name, 'databases', db_name, f'{db_name}.sqlite')}"
            print("DB URL:", url)
            engine = create_engine(url)
            md= generate_metadata(engine,db_name)
            with open(json_file, "w") as f:
                json.dump(md, f, indent=2)

        if db_name not in db_markdown_map:
            with open(json_file, "r") as f:
                data = json.load(f)
                db_markdown_map[db_name] ={
                    "metadata": data,
                    "json_file_path": json_file}

    return db_markdown_map

def format_prompt(prompt, data, question, script, db_name=None, db_markdown_map=None, extra_metadata=None):
    db_content = ""
    if db_name and db_markdown_map and db_name in db_markdown_map:
        db_content = db_markdown_map[db_name]

    recommendation = data.get(question, {}).get("context_id", "")
    similar_code = data.get(question, {}).get("similar_queries", "similar pydough code not found")
    question = data.get(question, {}).get("redefined_question", question)

    parts = [f"{question}\n\nDatabase Schema:\n\n", json_to_markdown(db_content['metadata'])]

    if extra_metadata:
        print(extra_metadata)
        parts.append(f"\n\nCollection you must focus on to solve the querie:\n{extra_metadata}")

    return "".join(parts), prompt.format(
        script_content=script,
        #database_content=json_to_markdown(db_content['metadata']),
        similar_queries=similar_code,
        recommendation=recommendation
    )

def correct(client, question, code, prompt, db_name):
    extracted_code = extract_python_code(code)
    env= {"pydough": pydough, "datetime": datetime}
    print(extracted_code)
    result, error, sql = execute_code_and_extract_result(extracted_code, env, db_name, start_of_week="Monday")
    if result is None:
        q = f"""Fix this Pydough code: {code}. Error: {error}. Question: {question}."""
        response = client.ask(q, prompt)
        if isinstance(response, tuple):  # Gemini returns (text, usage)
            return  "".join([code, response[0]])
        return "".join([code, response])
    return code

def get_response(client, prompt, data, row, script, db_markdown_map=None, extra_metadata=None, **kwargs):
    question = row["question"]
    db_name = row.get("db_name", None)
    formatted_q, formatted_prompt = format_prompt(prompt, data, question, script, db_name, db_markdown_map, extra_metadata)
    start = time.time()
    print(f"[INFO] Asking question: {question}")
    response1 = client.ask(formatted_q,formatted_prompt, **kwargs)
    duration = time.time() - start
    if isinstance(response1, tuple):  # Gemini returns (text, usage)
        #response= correct(client, formatted_q, response1[0], formatted_prompt, db_name=db_name)
        return response1[0], duration, response1[1]
    #response= correct(client, formatted_q, response1, formatted_prompt, db_name=db_name)
    return response1, duration, None 

def log_mlflow_metrics_and_artifacts(tested_df, output_path, args, kwargs, tested_file, debug_log="debug_log.txt"):
    total_rows = len(tested_df)
    
    # Calculate metrics for both evaluation methods
    custom_eval_counts = tested_df['custom_eval'].value_counts()
    custom_eval_percentages = custom_eval_counts / total_rows
    custom_eval_percentages_dict = custom_eval_percentages.to_dict()
    
    bird_eval_counts = tested_df['bird_eval'].value_counts()
    bird_eval_percentages = bird_eval_counts / total_rows
    bird_eval_percentages_dict = bird_eval_percentages.to_dict()

    # Filter parameters for logging
    filtered_args = {
        key: value
        for key, value in vars(args).items()
        if key not in ['name', 'description', 'extra_args']
    }

    try:
        # === Conditional Custom Metrics ===
        if "difficulty" in tested_df.columns and "complexity" in tested_df.columns:
            total_per_difficulty = tested_df["difficulty"].value_counts()
            total_per_complexity = tested_df["complexity"].value_counts()
            total_per_combo = tested_df.groupby(["difficulty", "complexity"]).size()

            # Custom eval metrics by difficulty/complexity
            custom_eval_match_df = tested_df[tested_df["custom_eval"] == "Match"]
            custom_eval_non_match_df = tested_df[tested_df["custom_eval"] != "Match"]

            custom_eval_matches_per_difficulty = custom_eval_match_df["difficulty"].value_counts()
            custom_eval_matches_per_complexity = custom_eval_match_df["complexity"].value_counts()
            custom_eval_matches_per_combo = custom_eval_match_df.groupby(["difficulty", "complexity"]).size()

            custom_eval_match_pct_difficulty = custom_eval_matches_per_difficulty / total_per_difficulty
            custom_eval_match_pct_complexity = custom_eval_matches_per_complexity / total_per_complexity
            custom_eval_match_pct_combo = custom_eval_matches_per_combo / total_per_combo

            # Bird eval metrics by difficulty/complexity (only for available results)
            bird_eval_available_df = tested_df[tested_df["bird_eval"].isin(["Match", "No Match"])]
            if len(bird_eval_available_df) > 0:
                bird_eval_match_df = tested_df[tested_df["bird_eval"] == "Match"]
                
                bird_eval_matches_per_difficulty = bird_eval_match_df["difficulty"].value_counts()
                bird_eval_matches_per_complexity = bird_eval_match_df["complexity"].value_counts()
                bird_eval_matches_per_combo = bird_eval_match_df.groupby(["difficulty", "complexity"]).size()

                # Only calculate percentages for cases where bird_eval was available
                bird_eval_total_per_difficulty = bird_eval_available_df["difficulty"].value_counts()
                bird_eval_total_per_complexity = bird_eval_available_df["complexity"].value_counts()
                bird_eval_total_per_combo = bird_eval_available_df.groupby(["difficulty", "complexity"]).size()

                bird_eval_match_pct_difficulty = bird_eval_matches_per_difficulty / bird_eval_total_per_difficulty
                bird_eval_match_pct_complexity = bird_eval_matches_per_complexity / bird_eval_total_per_complexity
                bird_eval_match_pct_combo = bird_eval_matches_per_combo / bird_eval_total_per_combo

            # Grouping by db_name, difficulty, and complexity for custom_eval
            custom_eval_matches_per_combo_db = custom_eval_match_df.groupby(["difficulty", "complexity", "db_name"]).size()
            total_per_combo_db = tested_df.groupby(["difficulty", "complexity", "db_name"]).size()

            custom_eval_matches_per_difficulty_db = custom_eval_match_df.groupby(["difficulty", "db_name"]).size()
            total_per_difficulty_db = tested_df.groupby(["difficulty", "db_name"]).size()

            custom_eval_matches_per_complexity_db = custom_eval_match_df.groupby(["complexity", "db_name"]).size()
            total_per_complexity_db = tested_df.groupby(["complexity", "db_name"]).size()

            # === Save calculated metrics as CSVs ===
            os.makedirs(output_path, exist_ok=True)

            # Custom eval metrics
            custom_eval_match_pct_combo_df = (custom_eval_matches_per_combo_db / total_per_combo_db).reset_index()
            custom_eval_match_pct_combo_df.columns = ["difficulty", "complexity", "db_name", "custom_eval_match_percentage"]
            custom_eval_match_pct_combo_path = f"{output_path}/custom_eval_match_percentage_per_difficulty_complexity_db.csv"
            custom_eval_match_pct_combo_df.to_csv(custom_eval_match_pct_combo_path, index=False)
            mlflow.log_artifact(custom_eval_match_pct_combo_path)

            # Custom eval match % per difficulty+db
            custom_eval_match_pct_difficulty_df = (custom_eval_matches_per_difficulty_db / total_per_difficulty_db).reset_index()
            custom_eval_match_pct_difficulty_df.columns = ["difficulty", "db_name", "custom_eval_match_percentage"]
            custom_eval_match_pct_difficulty_path = f"{output_path}/custom_eval_match_percentage_per_difficulty_db.csv"
            custom_eval_match_pct_difficulty_df.to_csv(custom_eval_match_pct_difficulty_path, index=False)
            mlflow.log_artifact(custom_eval_match_pct_difficulty_path)

            # Custom eval match % per complexity+db
            custom_eval_match_pct_complexity_df = (custom_eval_matches_per_complexity_db / total_per_complexity_db).reset_index()
            custom_eval_match_pct_complexity_df.columns = ["complexity", "db_name", "custom_eval_match_percentage"]
            custom_eval_match_pct_complexity_path = f"{output_path}/custom_eval_match_percentage_per_complexity_db.csv"
            custom_eval_match_pct_complexity_df.to_csv(custom_eval_match_pct_complexity_path, index=False)
            mlflow.log_artifact(custom_eval_match_pct_complexity_path)

            # Bird eval metrics (only if available)
            if len(bird_eval_available_df) > 0:
                # Similar metrics for bird_eval where applicable
                bird_eval_matches_per_combo_db = bird_eval_match_df.groupby(["difficulty", "complexity", "db_name"]).size()
                bird_eval_total_per_combo_db = bird_eval_available_df.groupby(["difficulty", "complexity", "db_name"]).size()
                
                bird_eval_match_pct_combo_df = (bird_eval_matches_per_combo_db / bird_eval_total_per_combo_db).reset_index()
                bird_eval_match_pct_combo_df.columns = ["difficulty", "complexity", "db_name", "bird_eval_match_percentage"]
                bird_eval_match_pct_combo_path = f"{output_path}/bird_eval_match_percentage_per_difficulty_complexity_db.csv"
                bird_eval_match_pct_combo_df.to_csv(bird_eval_match_pct_combo_path, index=False)
                mlflow.log_artifact(bird_eval_match_pct_combo_path)

            # === Save Raw Match Counts ===
            custom_eval_matches_per_difficulty.to_csv(f"{output_path}/custom_eval_match_count_per_difficulty.csv")
            custom_eval_matches_per_complexity.to_csv(f"{output_path}/custom_eval_match_count_per_complexity.csv")
            custom_eval_matches_per_combo.to_csv(f"{output_path}/custom_eval_match_count_per_difficulty_complexity.csv")

            mlflow.log_artifact(f"{output_path}/custom_eval_match_count_per_difficulty.csv")
            mlflow.log_artifact(f"{output_path}/custom_eval_match_count_per_complexity.csv")
            mlflow.log_artifact(f"{output_path}/custom_eval_match_count_per_difficulty_complexity.csv")

            if len(bird_eval_available_df) > 0:
                bird_eval_matches_per_difficulty.to_csv(f"{output_path}/bird_eval_match_count_per_difficulty.csv")
                bird_eval_matches_per_complexity.to_csv(f"{output_path}/bird_eval_match_count_per_complexity.csv")
                bird_eval_matches_per_combo.to_csv(f"{output_path}/bird_eval_match_count_per_difficulty_complexity.csv")

                mlflow.log_artifact(f"{output_path}/bird_eval_match_count_per_difficulty.csv")
                mlflow.log_artifact(f"{output_path}/bird_eval_match_count_per_complexity.csv")
                mlflow.log_artifact(f"{output_path}/bird_eval_match_count_per_difficulty_complexity.csv")

            # === Distribution Reports ===
            output_dir = f"{output_path}/distribution_reports"
            os.makedirs(output_dir, exist_ok=True)

            # db_name + difficulty + complexity
            count_combo = tested_df.groupby(['db_name', 'difficulty', 'complexity']).size().reset_index(name='count')
            total_combo = count_combo['count'].sum()
            count_combo['percentage'] = (count_combo['count'] / total_combo) * 100
            combo_path = f"{output_dir}/distribution_db_difficulty_complexity.csv"
            os.makedirs(output_dir, exist_ok=True)

            # db_name + difficulty + complexity
            count_combo = tested_df.groupby(['db_name', 'difficulty', 'complexity']).size().reset_index(name='count')
            total_combo = count_combo['count'].sum()
            count_combo['percentage'] = (count_combo['count'] / total_combo) * 100
            combo_path = f"{output_dir}/distribution_difficulty_complexity.csv"
            count_combo.to_csv(combo_path, index=False)

            # db_name + complexity
            count_complexity_db = tested_df.groupby(['db_name', 'complexity']).size().reset_index(name='count')
            total_complexity = count_complexity_db['count'].sum()
            count_complexity_db['percentage'] = (count_complexity_db['count'] / total_complexity) * 100
            complexity_db_path = f"{output_dir}/distribution_complexity_db.csv"
            count_complexity_db.to_csv(complexity_db_path, index=False)

            # db_name + difficulty
            count_difficulty_db = tested_df.groupby(['db_name', 'difficulty']).size().reset_index(name='count')
            total_difficulty = count_difficulty_db['count'].sum()
            count_difficulty_db['percentage'] = (count_difficulty_db['count'] / total_difficulty) * 100
            difficulty_db_path = f"{output_dir}/distribution_difficulty_db.csv"
            count_difficulty_db.to_csv(difficulty_db_path, index=False)

            # overall difficulty
            count_difficulty = tested_df.groupby('difficulty').size().reset_index(name='count')
            total_difficulty = count_difficulty['count'].sum()
            count_difficulty['percentage'] = (count_difficulty['count'] / total_difficulty) * 100
            overall_difficulty_path = f"{output_dir}/overall_distribution_difficulty.csv"
            count_difficulty.to_csv(overall_difficulty_path, index=False)

            # overall complexity
            count_complexity = tested_df.groupby('complexity').size().reset_index(name='count')
            total_complexity = count_complexity['count'].sum()
            count_complexity['percentage'] = (count_complexity['count'] / total_complexity) * 100
            overall_complexity_path = f"{output_dir}/overall_distribution_complexity.csv"
            count_complexity.to_csv(overall_complexity_path, index=False)

            # Log artifacts once
            count_combo.to_csv(combo_path, index=False)

            # db_name + complexity
            count_complexity_db = tested_df.groupby(['db_name', 'complexity']).size().reset_index(name='count')
            total_complexity = count_complexity_db['count'].sum()
            count_complexity_db['percentage'] = (count_complexity_db['count'] / total_complexity) * 100
            complexity_db_path = f"{output_dir}/distribution_complexity_db.csv"
            count_complexity_db.to_csv(complexity_db_path, index=False)

            # db_name + difficulty
            count_difficulty_db = tested_df.groupby(['db_name', 'difficulty']).size().reset_index(name='count')
            total_difficulty = count_difficulty_db['count'].sum()
            count_difficulty_db['percentage'] = (count_difficulty_db['count'] / total_difficulty) * 100
            difficulty_db_path = f"{output_dir}/distribution_difficulty_db.csv"
            count_difficulty_db.to_csv(difficulty_db_path, index=False)

            # overall difficulty
            count_difficulty = tested_df.groupby('difficulty').size().reset_index(name='count')
            total_difficulty = count_difficulty['count'].sum()
            count_difficulty['percentage'] = (count_difficulty['count'] / total_difficulty) * 100
            overall_difficulty_path = f"{output_dir}/overall_distribution_difficulty.csv"
            count_difficulty.to_csv(overall_difficulty_path, index=False)

            # overall complexity
            count_complexity = tested_df.groupby('complexity').size().reset_index(name='count')
            total_complexity = count_complexity['count'].sum()
            count_complexity['percentage'] = (count_complexity['count'] / total_complexity) * 100
            overall_complexity_path = f"{output_dir}/overall_distribution_complexity.csv"
            count_complexity.to_csv(overall_complexity_path, index=False)

            # Log artifacts once
            mlflow.log_artifact(combo_path)
            mlflow.log_artifact(complexity_db_path)
            mlflow.log_artifact(difficulty_db_path)
            mlflow.log_artifact(overall_complexity_path)
            mlflow.log_artifact(overall_difficulty_path)
    except Exception as e:
        print(f"Error in logging MLflow metrics: {e}")
        raise
    
    mlflow.log_params(filtered_args)
    mlflow.log_params(kwargs)
    
    # Log metrics for both evaluation methods
    custom_eval_metrics = {f"custom_eval_{k}": v for k, v in custom_eval_percentages_dict.items()}
    bird_eval_metrics = {f"bird_eval_{k}": v for k, v in bird_eval_percentages_dict.items()}
    
    mlflow.log_metrics(custom_eval_metrics)
    mlflow.log_metrics(bird_eval_metrics)
    mlflow.log_metric("total_queries", total_rows)
    mlflow.log_artifact(tested_file)
    debug_log = f"debug_log.txt"
    mlflow.log_artifact(debug_log)

    # Create combined metrics JSON
    combined_metrics = {
        "custom_eval": custom_eval_percentages_dict,
        "bird_eval": bird_eval_percentages_dict,
        "total_queries": total_rows
    }
    metrics_json = json.dumps(combined_metrics, indent=4)
    metrics_path = "./metrics.json"

    with open(metrics_path, "w") as metrics_file:
        metrics_file.write(metrics_json)

def prepare_eval_data(args):
    prompt = read_file(args.prompt_file)
    script = read_file(args.pydough_file)
    with open("./queries_context.json") as f:
        data = json.load(f)
    df = pd.read_csv(args.questions)
    db_markdown_map = prepare_db_markdown_map(df, args.metadata_base_path, args.db_base_path)
    return prompt, script, data, df, db_markdown_map

def run_models_parallel(
    mlflow_run_id, prompt, data, row, script, models_to_test,
    db_base_path, metadata_base_path, db_markdown_map=None,
    tries=1, ensemble_selection_method="size", extra_metadata=None,
    use_gradio_agent=True, **kwargs
):
    question = row["question"]
    question_idx = row.get("question_index", "?")
    db_name = row.get("db_name", None)
    dataset_name = row.get("dataset_name", None)
    formatted_q, formatted_prompt = format_prompt(
        prompt, data, question, script, db_name,
        db_markdown_map, extra_metadata
    )

    db_path = os.path.join(
        db_base_path, dataset_name, 'databases', db_name, f"{db_name}.sqlite"
    )
    metadata_path = os.path.join(
        metadata_base_path, dataset_name, "metadata", f"{db_name}_graph.json"
    )
    
    print(f"[DEBUG] [Q{question_idx}] Running models for: {question}")

    def run_model(model_info, attempt):
        attempt = attempt + 1
        provider_name = model_info["provider"]
        model_id = model_info["model_id"]
        config = model_info["config"]
        print(f"[DEBUG] [Q{question_idx}] Running model {model_info['name']} (attempt {attempt})")
        # Handle Gradio agent as a special model candidate
        if model_info["name"] == "gradio_agent":
            try:
                start = time.time()
                endpoint = config.get("endpoint", "http://10.128.0.5:2025/")
                architecture = config.get("architecture", "SQLATS")
                timeout_seconds = config.get("timeout_seconds", 180)
                ga_response = gradio_process_question_with_timeout(
                    endpoint,
                    question,
                    "BIRD",
                    db_name,
                    mlflow_run_id,
                    question_id=question_idx,
                    architecture=architecture,
                    timeout_seconds=timeout_seconds,
                )
                duration = time.time() - start
                gradio_df = ga_response.get("dataframe") if isinstance(ga_response, dict) else None
                gen_df_json = None
                if gradio_df is not None:
                    gen_df_json = gradio_df.to_json(orient="records", date_format="iso")

                return {
                    "question_index": question_idx,
                    "question": question,
                    "model_name": model_info["name"],
                    "attempt": attempt,
                    "response": ga_response,
                    "code": None,
                    "duration": duration,
                    "usage": None,
                    "df": gradio_df,
                    "gen_df_json": gen_df_json,
                    "sql": row.get("sql", ""),
                    "generated_sql": None,
                    "dataset_name": row.get("dataset_name", ""),
                    "db_name": db_name,
                }
            except Exception as e:
                print(f"[ERROR] [Q{question_idx}] Gradio agent failed on attempt {attempt}: {e}")
                return {
                    "question_index": question_idx,
                    "question": question,
                    "model_name": model_info["name"],
                    "attempt": attempt,
                    "response": None,
                    "code": None,
                    "duration": time.time() - start,
                    "usage": None,
                    "df": None,
                    "gen_df_json": None,
                    "sql": row.get("sql", ""),
                    "generated_sql": None,
                    "dataset_name": row.get("dataset_name", ""),
                    "db_name": db_name,
                }
        client = get_provider(provider_name, model_id, config=config)
        start = time.time()
        model_specific_kwargs = dict(kwargs)
        gen_df_json = "No valid generated df"
        gen_sql = "No valid SQL"
        if model_info["name"] == "gemini":
            model_specific_kwargs.pop("use_stream", None)
        try:
            raw_response, usage, code, gen_df = None, None, None, None
            response = client.ask(formatted_q, formatted_prompt, **model_specific_kwargs)
            duration = time.time() - start
            if isinstance(response, tuple):
                raw_response, usage = response
            else:
                raw_response, usage = response, None
            code = extract_python_code(raw_response)
            print(f"[DEBUG] [Q{question_idx}] Code generated by {model_info['name']}:\n{code}")

            gen_df_json = None
            if code:
                print(f"[DEBUG] [Q{question_idx}] Executing code for {model_info['name']}")
                env = {"pydough": pydough, "datetime": datetime}
                # Execute with 60s timeout in a separate process
                gen_df, _, gen_sql = execute_code_with_timeout(
                    code, metadata_path, db_name, db_path, start_of_week="Monday", timeout_seconds=300
                )
                if gen_df is not None:
                    gen_df_json = gen_df.to_json(orient="records", date_format="iso")
                if not gen_sql:
                    gen_sql = "Faulty generated SQL"
                print(f"[DEBUG] [Q{question_idx}] DataFrame from {model_info['name']} is {'valid' if gen_df is not None else 'None'}")
            else:
                gen_df, gen_sql = None, "No code generated"

        except Exception as e:
            raw_response, code, duration, usage, gen_df = None, None, time.time() - start, None, None
            print(f"[ERROR] [Q{question_idx}] Model {model_info['name']} failed on attempt {attempt}: {e}")

        return {
            "question_index": question_idx,
            "question": question,
            "model_name": model_info["name"],
            "attempt": attempt,
            "response": raw_response,
            "code": code,
            "duration": duration,
            "usage": usage,
            "df": gen_df,
            "gen_df_json": gen_df_json,
            "sql": row.get("sql", ""),
            "generated_sql": gen_sql,
            "dataset_name": row.get("dataset_name", ""),
            "db_name": db_name,
        }

    all_runs = []
    for attempt in range(tries):
        for model in models_to_test:   # <-- now sequential
            result = run_model(model, attempt)
            all_runs.append(result)

    print(f"[DEBUG] [Q{question_idx}] Completed all runs. Total: {len(all_runs)}")
    for run in all_runs:
        print(f"[DEBUG] [Q{question_idx}] {run['model_name']} | Attempt: {run['attempt']} | DF: {'✅' if run['df'] is not None else '❌'}")

    # Group runs by model name
    grouped = {}
    for run in all_runs:
        grouped.setdefault(run["model_name"], []).append(run)

    # Fallback: use ensemble result
    print(f"[INFO] [Q{question_idx}] No early match found. Running ensemble fallback...")
    ensemble = ensemble_result(
        mlflow_run_id, all_runs, question, dataset_name, db_name,
        question_idx, ensemble_selection_method=ensemble_selection_method,
        use_gradio_agent=use_gradio_agent
    )
    return ensemble, all_runs

def favourite_based_selection(all_runs, question, dataset_name, db_name, question_idx="?"):
    """
    Selects the Gemini result if available (response not empty and df not None), otherwise Claude (same), otherwise Gradio agent.
    Returns: response, duration, usage, model_name, gen_df_json
    """
    # Find gemini and claude runs (assume only one try per model)
    gemini_run = next((r for r in all_runs if r["model_name"] == "gemini"), None)
    claude_run = next((r for r in all_runs if r["model_name"] == "claude"), None)

    # Prefer Gemini if response is not empty and df is not None
    if gemini_run and gemini_run["response"] and gemini_run["df"] is not None:
        print(f"[INFO] [Q{question_idx}] Early match found. Returning Gemini result.")
        return gemini_run["response"], gemini_run["duration"], gemini_run["usage"], gemini_run["model_name"], gemini_run["gen_df_json"], gemini_run["generated_sql"]
    # Otherwise, prefer Claude if response is not empty and df is not None
    if claude_run and claude_run["response"] and claude_run["df"] is not None:
        print(f"[INFO] [Q{question_idx}] Early match found. Returning Claude result.")
        return claude_run["response"], claude_run["duration"], claude_run["usage"], claude_run["model_name"], claude_run["gen_df_json"], claude_run["generated_sql"]
    # Otherwise, call Gradio agent
    print(f"[INFO] [Q{question_idx}] No Gemini or Claude response with valid DataFrame, calling Gradio agent...")
    response, gradio_df = gradio_process_question(question, dataset_name, db_name)
    if gradio_df is None:
        print(f"[WARNING] [Q{question_idx}] Gradio agent returned None dataframe. Falling back to random valid run.")
        fallback = random.choice(all_runs)
        return fallback["response"], fallback["duration"], fallback["usage"], fallback["model_name"], fallback["gen_df_json"], fallback.get("generated_sql")
    gen_df_json = gradio_df.to_json(orient="records", date_format="iso")
    # Use the other fields from the Claude run if available, else None
    duration = claude_run["duration"] if claude_run else None
    usage = claude_run["usage"] if claude_run else None
    # TODO: Add response, duration and usage from Gradio agent
    print(f"[INFO] [Q{question_idx}] Choosing Gradio agent result.")
    return response, duration, usage, "Gradio agent", gen_df_json, None

def frequency_based_selection(valid_runs, question, question_idx="?"):
    consensus = defaultdict(int)
    response_matches = defaultdict(lambda: defaultdict(int))
    model_matches = defaultdict(int)  # Track matches by model name

    for i in range(len(valid_runs)):
        for j in range(i + 1, len(valid_runs)):
            if symetric_compare_df(valid_runs[i]["df"], valid_runs[j]["df"], query_category="a", question=question):
                consensus[i] += 1
                consensus[j] += 1
                # Track which models matched with each other
                
                model_i = valid_runs[i]["model_name"]
                model_j = valid_runs[j]["model_name"]
                model_matches[model_i] += 1
                model_matches[model_j] += 1
                response_matches[i][model_j] += 1
                response_matches[j][model_i] += 1

    if len(consensus) > 0:
        best_index = max(consensus, key=lambda i: consensus[i])
        best = valid_runs[best_index]
        best_matches = response_matches[best_index]
        best_model = best['model_name']
        
        # Build the detailed consensus message
        match_breakdown = []
        for model_name, match_count in model_matches.items():
            match_breakdown.append(f"{match_count} {model_name} matches")
        
        response_breakdown = []
        for model_name, match_count in best_matches.items():
            response_breakdown.append(f"{match_count} {model_name} matches")
        
        consensus_details = " and ".join(match_breakdown)
        response_details = " and ".join(response_breakdown)
        print(f"[INFO] [Q{question_idx}] Ensemble selected: {best_model} with {consensus[best_index]} matches. {response_details} for the chosen response. {consensus_details} globally. ")
        return best["response"], best["duration"], best["usage"], best["model_name"], best["gen_df_json"], best["generated_sql"]

    gemini_runs = [r for r in valid_runs if r["model_name"] == "gemini"]
    if gemini_runs:
        fallback = random.choice(gemini_runs)
        print(f"[INFO] [Q{question_idx}] No consensus found. Falling back to Gemini run.")
        return fallback["response"], fallback["duration"], fallback["usage"], fallback["model_name"], fallback["gen_df_json"], fallback["generated_sql"]
    else:
        print(f"[WARNING] [Q{question_idx}] No Gemini runs available. Falling back to random valid run.")
        fallback = random.choice(valid_runs)
        return fallback["response"], fallback["duration"], fallback["usage"], fallback["model_name"], fallback["gen_df_json"], fallback["generated_sql"]
    
def size_based_selection(valid_runs, question, dataset_name, db_name, question_idx="?"):
    """
    Selects the run with the largest dataframe size.
    If multiple runs have the same largest size, prioritize the response from the model named "claude".
    """
    
    size_dict = defaultdict(int)
    for i in range(len(valid_runs)):
        if "df" in valid_runs[i] and valid_runs[i]["df"] is not None:
            size_dict[i] = valid_runs[i]["df"].size
        else:
            size_dict[i] = -1  # Mark as invalid

    if size_dict and max(size_dict.values()) > -1:
        # Compute all candidates with the maximum size
        max_size = max(size_dict.values())
        candidates = [i for i, s in size_dict.items() if s == max_size]
        # If tie, use deterministic random tie-break
        if len(candidates) == 1:
            best_index = candidates[0] 
            best = valid_runs[best_index]
            print(f"[INFO] [Q{question_idx}] Size-based selection: {best['model_name']} with size {size_dict[best_index]}.")
            return best["response"], best["duration"], best["usage"], best["model_name"], best["gen_df_json"], best["generated_sql"]
        else:
#             print("Calling gradio agent SQLATS to choose the best result")
#             response = gradio_process_question_with_timeout("http://10.128.0.5:2025/", question, "BIRD", db_name, question_id=question_idx, architecture="SQLATS", timeout_seconds=180)
#             gradio_df = response['dataframe']

#             if gradio_df is None:
#                 best_index = candidates[0] 
#                 best = valid_runs[best_index]
#                 print(f"[INFO] [Q{question_idx}] Size-based selection: {best['model_name']} with size {size_dict[best_index]}.")
#                 return best["response"], best["duration"], best["usage"], best["model_name"], best["gen_df_json"], best["generated_sql"]

#             gen_df_json = gradio_df.to_json(orient="records", date_format="iso")

#             # Attempt to reuse duration/usage from a previous Claude run if it exists
#             claude_run = next((r for r in valid_runs if r["model_name"] == "claude"), None)
#             duration = claude_run["duration"] if claude_run else None
#             usage = claude_run["usage"] if claude_run else None

#             print(f"[INFO] [Q{question_idx}] Choosing Gradio agent result.")
#             return response, duration, usage, "Gradio agent", gen_df_json
            best_index = candidates[0] 
            best = valid_runs[best_index]
            print(f"[INFO] [Q{question_idx}] Size-based selection: {best['model_name']} with size {size_dict[best_index]}.")
            return best["response"], best["duration"], best["usage"], best["model_name"], best["gen_df_json"], best["generated_sql"]

    else:
        print(f"[WARNING] [Q{question_idx}] No valid dataframes found in size_based_selection.")
        return None, 0.0, None, None, None, None

def process_questions(
    mlflow_run_id,
    data,
    provider,
    model_id,
    prompt,
    questions_df,
    script,
    threads, 
    db_base_path,
    metadata_base_path,
    db_markdown_map=None,
    use_parallel=False,
    use_extrametadata=False,
    ensemble_selection_method="size",
    tries=1,
    use_gradio_agent=True,
    **kwargs
):
    print(f"[INFO] Processing {len(questions_df)} questions using provider: {provider}, model_id: {model_id}")
    num_keys = len(google_credentials)

    def process_single_question(index, row):
        row["question_index"] = index + 1
        question = row["question"]
        db_name = row.get("db_name", None)
        dataset_name = row.get("dataset_name", None)
        mapping_metadata = None

        if use_extrametadata:
            if db_name and db_markdown_map and db_name in db_markdown_map:
                db_content = db_markdown_map[db_name]
            if dataset_name == "spider_data":
                dataset_name = "Spider"
            result = gradio_process_question(question, "BIRD", db_name)
            if result:
                json_data = result.get("json_data", None)
                mapping_metadata = map_all_profiles_to_markdown(
                    db_content["metadata"], json_data, db_name
                )

        # Selección round-robin de credenciales
        api_key, project_id = google_credentials[index % num_keys]

        models_to_test = [
            {
                "name": "gemini",
                "provider": "google",
                "model_id": "projects/316936339319/locations/us-central1/endpoints/5954430508988366848",
                "config": {
                    "api_key": api_key,
                    "project": project_id,
                    "region": "us-central1"
                }
            }
        ]

        # Optionally include Gradio agent as another model candidate
        if use_gradio_agent:
            models_to_test.append({
                "name": "gradio_agent",
                "provider": "gradio",
                "model_id": "SQLATS",
                "config": {
                    "endpoint": "http://localhost:2025/",
                    "architecture": "SQLATS",
                    "timeout_seconds": 180,
                },
            })

        if use_parallel:
            ensemble_result, all_runs = run_models_parallel(
                mlflow_run_id=mlflow_run_id,
                prompt=prompt,
                data=data,
                row=row,
                script=script,
                models_to_test=models_to_test,
                db_base_path=db_base_path,
                metadata_base_path=metadata_base_path,
                db_markdown_map=db_markdown_map,
                ensemble_selection_method=ensemble_selection_method,
                tries=tries,
                extra_metadata=mapping_metadata,
                use_gradio_agent=use_gradio_agent,
                **kwargs,
            )
            return (ensemble_result, all_runs)
        else:
            client = get_provider(provider, model_id)
            return get_response(
                client=client,
                prompt=prompt,
                data=data,
                row=row,
                script=script,
                db_markdown_map=db_markdown_map,
                extra_metadata=mapping_metadata,
                **kwargs,
            )

    # Parallelize across questions if threads > 1
    results = [None] * len(questions_df)
    num_workers = threads if threads and threads > 1 else 1
    if num_workers > 1:
        print(f"[INFO] Running per-question processing with {num_workers} threads")
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            future_to_idx = {}
            for idx, row in questions_df.iterrows():
                future = executor.submit(process_single_question, idx, row)
                future_to_idx[future] = idx
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    print(f"[ERROR] Failed processing question index {idx + 1}: {e}")
                    # Fallback placeholder on exception to keep alignment
                    if use_parallel:
                        results[idx] = (None, [])
                    else:
                        results[idx] = (None, 0.0, None, None, None)
    else:
        print(f"[INFO] Running per-question processing sequentially")
        for index, row in questions_df.iterrows():
            results[index] = process_single_question(index, row)

    if use_parallel:
        ensembles = [r[0] for r in results]
        all_model_runs_per_question = [r[1] for r in results]
        return ensembles, all_model_runs_per_question
    else:
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

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--description", type=str, default="MLFlow")
    parser.add_argument("--name", type=str, default="MLFlow project")
    parser.add_argument("--experiment_name", type=str)
    parser.add_argument('--db-base-path', type=str, required=True)
    parser.add_argument('--metadata-base-path', type=str, required=True)
    parser.add_argument("--pydough_file", type=str)
    parser.add_argument("--prompt_file", type=str)
    parser.add_argument("--questions", type=str)
    parser.add_argument("--provider", type=str)
    parser.add_argument("--model_id", type=str)
    parser.add_argument("--num_threads", type=int)
    parser.add_argument("--use-parallel", action="store_true")
    parser.add_argument("--use-extrametadata",  action="store_true", help="Use extra metadata from Gradio agent")
    parser.add_argument("--ensemble-selection-method", type=str, choices=["size", "favourite", "frequency"], default="size", help="Ensemble selection method: size, favourite, frequency")
    parser.add_argument("--use-gradio-agent", action="store_true", default=False, help="Use Gradio agent when no valid dataframes are available for ensemble")
    parser.add_argument("--tries", type=int, default=1, help="Number of tries for each model in parallel mode")
    parser.add_argument("--keys", nargs="*", type=int, help="Google API key indices to use (e.g., --keys 1 3)")
    parser.add_argument("--extra_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    kwargs = parse_extra_args(args.extra_args)
    print(f"[INFO] Parsed arguments: {vars(args)}")
    print(f"[INFO] Additional arguments: {kwargs}")
    return args, kwargs

# === Entry Point ===

@contextmanager
def mlflow_run_context(args, git_hash):
    MLFLOW_TRACKING_URI = "http://mlflow-alb-1071096006.us-east-2.elb.amazonaws.com"
    MLFLOW_TRACKING_TOKEN = os.environ["MLFLOW_TRACKING_TOKEN"]
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    experiment = mlflow.set_experiment(args.experiment_name)
    with mlflow.start_run(
        description=args.description,
        run_name=args.name,
        tags={"GIT_COMMIT": git_hash},
        experiment_id=experiment.experiment_id
    ):
        yield

def main(git_hash):
    print(f"[INFO] Starting prompt evaluation.")
    debug_log = "debug_log.txt"
    
    # Set up dual output: both terminal and file
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    debug_file = open("debug_log.txt", "w")
    
    try:
        # Create Tee objects for stdout and stderr
        sys.stdout = Tee(original_stdout, debug_file)
        sys.stderr = Tee(original_stderr, debug_file)
        args, kwargs = parse_arguments()

        # Load Google credentials based on --keys argument
        load_google_credentials(args.keys)

        with mlflow_run_context(args, git_hash):
            prompt, script, data, df, db_markdown_map = prepare_eval_data(args)

            # Retrieve the mlflow run ID
            mlflow_run_id = mlflow.active_run().info.run_id

            results, all_model_runs_per_question = process_questions(
                mlflow_run_id,
                data,
                provider=args.provider.lower(),
                model_id=args.model_id,
                prompt=prompt,
                questions_df=df,
                script=script,
                threads=args.num_threads,
                db_base_path=args.db_base_path,
                metadata_base_path=args.metadata_base_path,
                db_markdown_map=db_markdown_map,
                use_parallel=args.use_parallel,
                use_extrametadata=args.use_extrametadata,
                ensemble_selection_method=args.ensemble_selection_method,
                tries=args.tries,
                use_gradio_agent=args.use_gradio_agent,
                **kwargs
            )

            # Existing output (ensemble/winner per question)
            df = build_results_df(df, results)

            output_path = f"./results/{args.provider}/{args.model_id}"
            os.makedirs(output_path, exist_ok=True)
            output_file = f"{output_path}/responses_{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.csv"
            df.to_csv(output_file, index=False)

            # --- NEW: Output all model runs (for parallel mode) ---
            if args.use_parallel:
                # all_model_runs_per_question is a list of lists of dicts
                flat_runs = []
                for runs in all_model_runs_per_question:
                    if isinstance(runs, list):
                        flat_runs.extend(runs)
                # Build DataFrame
                all_runs_df = pd.DataFrame(flat_runs)
                all_runs_csv = f"{output_path}/all_model_runs_{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.csv"
                all_runs_df.to_csv(all_runs_csv, index=False)
                mlflow.log_artifact(all_runs_csv)

            test_path = f"{output_path}/test"
            os.makedirs(test_path, exist_ok=True)
            tested_file, tested_df = custom_eval(test_path, output_file, args.db_base_path, args.metadata_base_path)

            log_mlflow_metrics_and_artifacts(
                tested_df, output_path, args, kwargs, tested_file, debug_log
            )
    finally:
        # Restore original stdout/stderr and close debug file
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        debug_file.close()

def build_results_df(df, results):
    def get_field(result_entry, index):
        # Handle None entries gracefully
        if result_entry is None:
            return None
        # If dict-like, try common keys
        if isinstance(result_entry, dict):
            key_order = [
                "response",
                "execution_time",
                "usage",
                "model_name",
                "gen_df_json",
                "gen_sql",
            ]
            key = key_order[index] if index < len(key_order) else None
            return result_entry.get(key) if key else None
        # If sequence-like, index with bounds check
        try:
            return result_entry[index] if len(result_entry) > index else None
        except Exception:
            return None

    df["response"] = [get_field(r, 0) for r in results]
    df["execution_time"] = [get_field(r, 1) for r in results]
    df["extracted_python_code"] = df["response"].apply(extract_python_code)
    df["usage"] = [get_field(r, 2) for r in results]
    df["model_name"] = [get_field(r, 3) for r in results]
    df["gen_df_json"] = [get_field(r, 4) for r in results]
    df["gen_sql"] = [get_field(r, 5) for r in results]
    return df

if __name__ == "__main__":
    cwd = os.getcwd()
    #db_path = './test_data/TPCH.db'
    #download_database(db_path)
    #if untracked_files(cwd) or modified_files(cwd):
    #    autocommit(cwd)
    main(get_git_commit(cwd))