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
from test_data.eval import compare_output, execute_code_and_extract_result, compare_df, symetric_compare_df
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
from ensemble_logic import ensemble_result, ensemble_from_all_runs_file
# === Global RNG (seeded) ===
RNG_SEED = 12345
rng = random.Random(RNG_SEED)

# Tie-break helper used by selection methods
def selection_random_tie_break(candidate_indices, question_idx="?"):
    """
    Deterministically break ties among candidate indices using a seeded RNG.
    Returns the chosen index from candidate_indices.
    """
    if not candidate_indices:
        return None
    chosen = rng.choice(candidate_indices)
    print(f"[INFO] [Q{question_idx}] Tie-break among {len(candidate_indices)} candidates -> picked index {chosen}")
    return chosen


# === Credential for google cloud ===
def load_google_credentials(selected_keys=[1]):
    """
    Load Google API credentials based on selected key indices (1-based).
    If selected_keys is None, load just key number 1.
    Sets the global google_credentials variable.
    """
        # Find the .env file in your home directory
    env_path = Path.home() / ".env"
    load_dotenv(dotenv_path=env_path)
    print(f"[INFO] Loaded credentials from {env_path}")
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

    parts = [f"{question}\nDatabase Schema:\n", json_to_markdown(db_content['metadata'])]

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
    counts = tested_df['comparison_result'].value_counts()
    percentages = counts / total_rows
    filtered_args = {key: value for key, value in vars(args).items() if key not in ['name', 'description', 'extra_args']}
    can_log_mlflow = (not getattr(args, 'disable_mlflow', False)) and (mlflow.active_run() is not None)

    # === Conditional Custom Metrics ===
    if "difficulty" in tested_df.columns and "complexity" in tested_df.columns:
        total_per_difficulty = tested_df["difficulty"].value_counts()
        total_per_complexity = tested_df["complexity"].value_counts()
        total_per_combo = tested_df.groupby(["difficulty", "complexity"]).size()

        match_df = tested_df[tested_df["comparison_result"] == "Match"]
        non_match_df = tested_df[tested_df["comparison_result"] != "Match"]

        matches_per_difficulty = match_df["difficulty"].value_counts()
        matches_per_complexity = match_df["complexity"].value_counts()
        matches_per_combo = match_df.groupby(["difficulty", "complexity"]).size()

        match_pct_difficulty = matches_per_difficulty / total_per_difficulty
        match_pct_complexity = matches_per_complexity / total_per_complexity
        match_pct_combo = matches_per_combo / total_per_combo

        if can_log_mlflow:
            for diff, pct in match_pct_difficulty.items():
                mlflow.log_metric(f"match_pct_difficulty_{diff}", pct)

        if can_log_mlflow:
            for comp, pct in match_pct_complexity.items():
                mlflow.log_metric(f"match_pct_complexity_{comp}", pct)

        if can_log_mlflow:
            for (diff, comp), pct in match_pct_combo.items():
                mlflow.log_metric(f"match_pct_{diff}_{comp}", pct)

        non_matches_per_difficulty = non_match_df["difficulty"].value_counts()
        non_matches_per_complexity = non_match_df["complexity"].value_counts()
        non_matches_per_combo = non_match_df.groupby(["difficulty", "complexity"]).size()

        no_match_pct_difficulty = non_matches_per_difficulty / total_per_difficulty
        no_match_pct_complexity = non_matches_per_complexity / total_per_complexity
        no_match_pct_combo = non_matches_per_combo / total_per_combo

        if can_log_mlflow:
            for diff, pct in no_match_pct_difficulty.items():
                mlflow.log_metric(f"no_match_pct_difficulty_{diff}", pct)

        if can_log_mlflow:
            for comp, pct in no_match_pct_complexity.items():
                mlflow.log_metric(f"no_match_pct_complexity_{comp}", pct)

        if can_log_mlflow:
            for (diff, comp), pct in no_match_pct_combo.items():
                mlflow.log_metric(f"no_match_pct_{diff}_{comp}", pct) 
        total_per_combo_db = tested_df.groupby(["difficulty", "complexity", "db_name"]).size()
        total_per_difficulty_db = tested_df.groupby(["difficulty", "db_name"]).size()
        total_per_complexity_db = tested_df.groupby(["complexity", "db_name"]).size()
        non_matches_per_combo_per_database = non_match_df.groupby(["difficulty","complexity", "db_name"]).size()
        matches_per_combo_db  = match_df.groupby(["difficulty", "complexity","db_name"]).size()
        non_matches_difficulty_per_database = non_match_df.groupby(["difficulty", "db_name"]).size()
        matches_per_difficulty_db  = match_df.groupby(["difficulty", "db_name"]).size()
        non_matches_complexity_per_database = non_match_df.groupby(["complexity", "db_name"]).size()
        matches_per_complexity_db  = match_df.groupby(["complexity", "db_name"]).size()

        # Combo (difficulty + complexity + db)
        match_pct_combo_df = (matches_per_combo_db / total_per_combo_db).reset_index()
        match_pct_combo_df.columns = ["difficulty", "complexity", "db_name", "match_percentage"]
        match_pct_combo_csv = f"{output_path}/match_percentage_per_difficulty_complexity_db.csv"
        match_pct_combo_df.to_csv(match_pct_combo_csv, index=False)
        if can_log_mlflow:
            mlflow.log_artifact(match_pct_combo_csv)

        # Difficulty + db
        match_pct_difficulty_df = (matches_per_difficulty_db / total_per_difficulty_db).reset_index()
        match_pct_difficulty_df.columns = ["difficulty", "db_name", "match_percentage"]
        match_pct_difficulty_csv = f"{output_path}/match_percentage_per_difficulty_db.csv"
        match_pct_difficulty_df.to_csv(match_pct_difficulty_csv, index=False)
        if can_log_mlflow:
            mlflow.log_artifact(match_pct_difficulty_csv)

        # Complexity + db
        match_pct_complexity_df = (matches_per_complexity_db / total_per_complexity_db).reset_index()
        match_pct_complexity_df.columns = ["complexity", "db_name", "match_percentage"]
        match_pct_complexity_csv = f"{output_path}/match_percentage_per_complexity_db.csv"
        match_pct_complexity_df.to_csv(match_pct_complexity_csv, index=False)
        if can_log_mlflow:
            mlflow.log_artifact(match_pct_complexity_csv)
        # Save raw counts as CSV artifacts if needed
        matches_per_difficulty.to_csv(f"{output_path}/match_count_per_difficulty.csv")
        matches_per_complexity.to_csv(f"{output_path}/match_count_per_complexity.csv")
        matches_per_combo.to_csv(f"{output_path}/match_count_per_difficulty_complexity.csv")

        if can_log_mlflow:
            mlflow.log_artifact(f"{output_path}/match_count_per_difficulty.csv")
            mlflow.log_artifact(f"{output_path}/match_count_per_complexity.csv")
            mlflow.log_artifact(f"{output_path}/match_count_per_difficulty_complexity.csv")
        # Group by db_name, difficulty, and complexity
        count_combo = tested_df.groupby(['db_name', 'difficulty', 'complexity']).size().reset_index(name='count')
        total_combo = count_combo['count'].sum()
        count_combo['percentage'] = (count_combo['count'] / total_combo) * 100

        # Group by db_name and complexity
        count_complexity_db = tested_df.groupby(['db_name', 'complexity']).size().reset_index(name='count')
        total_complexity = count_complexity_db['count'].sum()
        count_complexity_db['percentage'] = (count_complexity_db['count'] / total_complexity) * 100

        # Group by db_name and difficulty (optional)
        count_difficulty_db = tested_df.groupby(['db_name', 'difficulty']).size().reset_index(name='count')
        total_difficulty = count_difficulty_db['count'].sum()
        count_difficulty_db['percentage'] = (count_difficulty_db['count'] / total_difficulty) * 100

        # === Group and Calculate Percentage by difficulty
        count_difficulty = tested_df.groupby('difficulty').size().reset_index(name='count')
        total_difficulty = count_difficulty['count'].sum()
        count_difficulty['percentage'] = (count_difficulty['count'] / total_difficulty) * 100

        # === Group and Calculate Percentage by complexity
        count_complexity = tested_df.groupby('complexity').size().reset_index(name='count')
        total_complexity = count_complexity['count'].sum()
        count_complexity['percentage'] = (count_complexity['count'] / total_complexity) * 100

        output_dir = f"{output_path}/distribution_reports"
        os.makedirs(output_dir, exist_ok=True)

        combo_path = f"{output_dir}/distribution_difficulty_complexity.csv"
        complexity_path = f"{output_dir}/distribution_complexity_db.csv"
        difficulty_path = f"{output_dir}/distribution_difficulty_db.csv"
        count_complexity_db.to_csv(complexity_path, index=False)
        count_difficulty_db.to_csv(difficulty_path, index=False)

        if can_log_mlflow:
            mlflow.log_artifact(difficulty_path)
            mlflow.log_artifact(complexity_path)
        count_combo.to_csv(combo_path, index=False)
        count_complexity.to_csv(complexity_path, index=False)
        count_difficulty.to_csv(difficulty_path, index=False)
        difficulty_path = f"{output_dir}/overall_distribution_difficulty.csv"
        complexity_path = f"{output_dir}/overall_distribution_complexity.csv"

        count_difficulty.to_csv(difficulty_path, index=False)
        count_complexity.to_csv(complexity_path, index=False)

        if can_log_mlflow:
            mlflow.log_artifact(difficulty_path)
            mlflow.log_artifact(complexity_path)

        if can_log_mlflow:
            mlflow.log_artifact(combo_path)
            mlflow.log_artifact(complexity_path)
            mlflow.log_artifact(difficulty_path)
    if can_log_mlflow:
        mlflow.log_params(filtered_args)
        mlflow.log_params(kwargs)
        mlflow.log_metrics(percentages)
        mlflow.log_metric("total_queries", total_rows)
        mlflow.log_artifact(tested_file)
    debug_log = f"debug_log.txt"
    if can_log_mlflow:
        mlflow.log_artifact(debug_log)

    percentages_dict = percentages.to_dict()
    metrics_json = json.dumps(percentages_dict, indent=4)
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

def run_models_parallel(mlflow_run_id, prompt, data, row, script, models_to_test, db_base_path, metadata_base_path, db_markdown_map=None, tries=1, ensemble_selection_method="size", extra_metadata=None, use_gradio_agent=True, **kwargs):
    question = row["question"]
    question_idx = row.get("question_index", "?")
    db_name = row.get("db_name", None)
    dataset_name = row.get("dataset_name", None)
    formatted_q, formatted_prompt = format_prompt(prompt, data, question, script, db_name, db_markdown_map, extra_metadata)

    db_path = os.path.join(db_base_path, dataset_name, 'databases', db_name, f"{db_name}.sqlite")
    metadata_path = os.path.join(metadata_base_path, dataset_name, "metadata", f"{db_name}_graph.json")
    
    print(f"[DEBUG] [Q{question_idx}] Running models for: {question}")

    def run_model(model_info, attempt):
        attempt = attempt+1
        provider_name = model_info["provider"]
        model_id = model_info["model_id"]
        config = model_info["config"]
        print(f"[DEBUG] [Q{question_idx}] Running model {model_info['name']} (attempt {(attempt+1)})")
        client = get_provider(provider_name, model_id, config=config)
        start = time.time()
        model_specific_kwargs = dict(kwargs)
        gen_df_json = "No valid genrated df"
        gen_sql = "No valid SQL"
        if model_info["name"] == "gemini":
            model_specific_kwargs.pop("use_stream", None)
        try:
            raw_response = None
            usage = None
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
                gen_df, _, gen_sql = execute_code_and_extract_result(code, env, metadata_path, db_name, db_path, start_of_week="Monday")
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
            #print(f"[DEBUG] [Q{question_idx}] Generated DataFrame: {gen_df}")
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
        with ThreadPoolExecutor(max_workers=len(models_to_test)) as executor:
            futures = [executor.submit(run_model, model, attempt) for model in models_to_test]
            all_runs.extend(f.result() for f in futures)

    print(f"[DEBUG] [Q{question_idx}] Completed all runs. Total: {len(all_runs)}")
    for run in all_runs:
        print(f"[DEBUG] [Q{question_idx}] {run['model_name']} | Attempt: {(run['attempt'])} | DF: {'✅' if run['df'] is not None else '❌'}")

    # Group runs by model name
    grouped = {}
    for run in all_runs:
        grouped.setdefault(run["model_name"], []).append(run)
    # Fallback: use ensemble result
    print(f"[INFO] [Q{question_idx}] No early match found. Running ensemble fallback...")
    ensemble = ensemble_result(mlflow_run_id, all_runs, question, dataset_name, db_name, question_idx, ensemble_selection_method=ensemble_selection_method, use_gradio_agent=use_gradio_agent)
    return ensemble, all_runs



def process_questions(mlflow_run_id, data, provider, model_id, prompt, questions_df, script, threads, db_base_path, metadata_base_path, db_markdown_map=None, use_parallel=False, use_extrametadata=False, ensemble_selection_method="size", tries=1, use_gradio_agent=True, **kwargs):
    print(f"[INFO] Processing {len(questions_df)} questions with {threads} threads using provider: {provider}, model_id: {model_id}")
    num_keys = len(google_credentials)
    def thread_wrapper(row_tuple):
        index, row = row_tuple
        row["question_index"] = index + 1
        question = row["question"]
        db_name = row.get("db_name", None)
        dataset_name = row.get("dataset_name", None)
        mapping_metadata = None
        if use_extrametadata:
            if db_name and db_markdown_map and db_name in db_markdown_map:
                db_content = db_markdown_map[db_name]
            if dataset_name == 'spider_data':
                dataset_name = 'Spider'
            result = gradio_process_question(question, dataset_name, db_name)
            if result:
                json_data = result.get("json_data", None)
                mapping_metadata = map_all_profiles_to_markdown(db_content['metadata'],json_data, db_name)
            
        # Select Google credentials in a round-robin manner
        api_key, project_id = google_credentials[index % num_keys]  # Round-robin selection

        # Configuations and selected models
        models_to_test = [ 
            {
                "name": "claude",
                "provider": "anthropic",
                "model_id": "claude-opus-4@20250514",
                "config": {
                    "api_key": api_key,
                    "project": project_id,
                    "region": "us-east5"
                }
            },
            {
                "name": "gemini",
                "provider": "google",
                "model_id": "gemini-2.5-pro",
                "config": {
                    "api_key": api_key,
                    "project": project_id,
                    "region": "us-central1"
                }
            }
        ]
        
        if use_parallel: 
            # Return both the ensemble result and all model runs
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
                **kwargs
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
                **kwargs
            )

    with ThreadPoolExecutor(max_workers=threads) as executor:
        results = list(executor.map(thread_wrapper, questions_df.iterrows()))

    if use_parallel:
        # results is a list of (ensemble, all_runs) tuples
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
    # These paths are only required when running LLM evaluation, not when --all-runs is provided
    parser.add_argument('--db-base-path', type=str)
    parser.add_argument('--metadata-base-path', type=str)
    parser.add_argument("--pydough_file", type=str)
    parser.add_argument("--prompt_file", type=str)
    parser.add_argument("--questions", type=str)
    parser.add_argument("--provider", type=str)
    parser.add_argument("--model_id", type=str)
    parser.add_argument("--num_threads", type=int)
    parser.add_argument("--use-parallel", action="store_true")
    parser.add_argument("--use-extrametadata",  action="store_true", help="Use extra metadata from Gradio agent")
    parser.add_argument("--ensemble-selection-method", type=str, choices=["size", "favourite", "frequency", "random", "density"], default="size", help="Ensemble selection method: size, favourite, frequency, random, density")
    parser.add_argument("--use-gradio-agent", action="store_true", default=False, help="Use Gradio agent when no valid dataframes are available for ensemble")
    parser.add_argument("--tries", type=int, default=1, help="Number of tries for each model in parallel mode")
    parser.add_argument("--keys", nargs="*", type=int, help="Google API key indices to use (e.g., --keys 1 3)")
    # New: run ensemble directly from an all_runs CSV
    parser.add_argument('--all-runs', type=str, help='Path to an all_runs-style CSV to ensemble without calling LLMs')
    parser.add_argument('--ensemble-output-dir', type=str, help='Directory to write ensemble results when using --all-runs')
    # MLflow configuration
    parser.add_argument('--mlflow-uri', type=str, help='Override MLflow tracking URI (e.g., file:./mlruns)')
    parser.add_argument('--disable-mlflow', action='store_true', help='Skip MLflow entirely')
    parser.add_argument("--extra_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    kwargs = parse_extra_args(args.extra_args)
    print(f"[INFO] Parsed arguments: {vars(args)}")
    print(f"[INFO] Additional arguments: {kwargs}")
    return args, kwargs

# === Entry Point ===

@contextmanager
def mlflow_run_context(args, git_hash):
    env_path = Path.home() / ".env"
    load_dotenv(dotenv_path=env_path)
    print(f"[INFO] Loaded credentials from {env_path}")
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
    sys.stdout = open("debug_log.txt", "w")
    sys.stderr = sys.stdout
    args, kwargs = parse_arguments()

    # Branch: If --all-runs is provided, run standalone ensemble mode
    if args.all_runs:
        with mlflow_run_context(args, git_hash):
            mlflow_run = mlflow.active_run()
            mlflow_run_id = mlflow_run.info.run_id if mlflow_run is not None else None

            winners_df, output_file = ensemble_from_all_runs_file(
                args.all_runs,
                ensemble_selection_method=args.ensemble_selection_method,
                use_gradio_agent=args.use_gradio_agent,
                output_dir=(args.ensemble_output_dir or './results/ensemble_from_all_runs'),
                mlflow_run_id=mlflow_run_id
            )

            # Ensure extracted code is available for comparison flow
            try:
                winners_df["extracted_python_code"] = winners_df["response"].apply(extract_python_code)
            except Exception:
                pass

            # Overwrite the winners CSV with the added column
            if output_file:
                winners_df.to_csv(output_file, index=False)

            # If DB paths are provided, run comparison to append comparison_result/exception
            if output_file and args.db_base_path and args.metadata_base_path:
                test_dir = os.path.join(os.path.dirname(output_file), "test")
                os.makedirs(test_dir, exist_ok=True)
                tested_file, tested_df = compare_output(test_dir, output_file, args.db_base_path, args.metadata_base_path)
                # Write enriched results back to the main output file for convenience
                tested_df.to_csv(output_file, index=False)
                # Log percentages and artifacts to MLflow consistent with LLM mode
                try:
                    output_dir = os.path.dirname(output_file)
                    log_mlflow_metrics_and_artifacts(
                        tested_df=tested_df,
                        output_path=output_dir,
                        args=args,
                        kwargs=kwargs,
                        tested_file=tested_file,
                        debug_log=debug_log
                    )
                except Exception as e:
                    print(f"[WARNING] Failed to log MLflow metrics for all-runs mode: {e}")
                if (not getattr(args, 'disable_mlflow', False)) and (mlflow.active_run() is not None):
                    mlflow.log_artifact(tested_file)

            if output_file and (not getattr(args, 'disable_mlflow', False)) and (mlflow.active_run() is not None):
                mlflow.log_artifact(output_file)
        return

    # Regular LLM evaluation mode
    # Load Google credentials based on --keys argument
    load_google_credentials(args.keys)

    # Validate required arguments for evaluation mode
    if not args.db_base_path or not args.metadata_base_path:
        raise ValueError("--db-base-path and --metadata-base-path are required unless --all-runs is provided")

    with mlflow_run_context(args, git_hash):
        prompt, script, data, df, db_markdown_map = prepare_eval_data(args)

        # Retrieve the mlflow run ID safely (may be None if MLflow is disabled or unavailable)
        mlflow_run = mlflow.active_run()
        mlflow_run_id = mlflow_run.info.run_id if mlflow_run is not None else None

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
                flat_runs.extend(runs)
            # Build DataFrame
            all_runs_df = pd.DataFrame(flat_runs)
            all_runs_csv = f"{output_path}/all_model_runs_{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.csv"
            all_runs_df.to_csv(all_runs_csv, index=False)
            if (not getattr(args, 'disable_mlflow', False)) and (mlflow.active_run() is not None):
                mlflow.log_artifact(all_runs_csv)

        test_path = f"{output_path}/test"
        os.makedirs(test_path, exist_ok=True)
        tested_file, tested_df = compare_output(test_path, output_file, args.db_base_path, args.metadata_base_path)

        log_mlflow_metrics_and_artifacts(
            tested_df, output_path, args, kwargs, tested_file, debug_log
        )

def build_results_df(df, results):
    df["response"] = [r[0] for r in results]
    df["execution_time"] = [r[1] for r in results if r[1] is not None]
    df["extracted_python_code"] = df["response"].apply(extract_python_code)
    df["usage"] = [r[2] if len(r) > 2 else None for r in results]
    df["model_name"] = [r[3] if len(r) > 3 else None for r in results]
    df["gen_df_json"] = [r[4] if len(r) > 4 else None for r in results]
    df["gen_sql"] = [r[5] if len(r) > 5 else None for r in results]
    return df

if __name__ == "__main__":
    cwd = os.getcwd()
    db_path = './test_data/TPCH.db'
    download_database(db_path)
    #if untracked_files(cwd) or modified_files(cwd):
    #    autocommit(cwd)
    main(get_git_commit(cwd))
