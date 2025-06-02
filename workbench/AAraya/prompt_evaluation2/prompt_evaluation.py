# prompt_evaluation.py

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
from data.test_data.eval import compare_output, execute_code_and_extract_result, compare_df
import aisuite as ai
from provider.ai_providers import *
from dynamic_prompt.generate_pydough_metadata import generate_metadata
from dynamic_prompt.mdgen import json_to_markdown
from sqlalchemy import create_engine, inspect, text
from gemini_wrapper import GeminiWrapper
from collections import defaultdict
import random

# === Helper Functions ===

models_to_test = [ 
    {
        "name": "claude",
        "provider": "google",
        "model_id": "claude-3-sonnet@20240229",
        "config": {
            "api_key": os.getenv("GOOGLE_API_KEY"),
            "project": os.getenv("GOOGLE_PROJECT_ID"),
            "region": "us-east5"
        }
    },
    {
        "name": "gemini",
        "provider": "google",
        "model_id": "gemini-2.5-pro-preview-05-06",
        "config": {
            "api_key": os.getenv("GOOGLE_API_KEY"),
            "project": os.getenv("GOOGLE_PROJECT_ID"),
            "region": "us-central1"
        }
    }
]


def get_provider(provider, model_id, config=None):
    if provider == "azure":
        return AzureAIProvider(model_id, config=config)
    elif provider == "aws-thinking":
        return ClaudeAIProvider(model_id, config=config)
    elif provider == "aws-deepseek":
        return DeepSeekAIProvider(model_id, config=config)
    elif provider == "google":
        return GeminiAIProvider(model_id, config=config)
    elif provider == "mistral":
        return MistralAIProvider(model_id, config=config)
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
        metadata_dir = os.path.join(metadata_base_path, dataset_name, "metadata")
        json_file = os.path.join(metadata_dir, f"{db_name}_graph.json")
        # Only generate if missing
        if not os.path.exists(json_file):
            print(f"[INFO] Generating JSON for: {db_name}")
            url = f"sqlite:///{os.path.join(db_base_path, 'databases', dataset_name, db_name)}"
            print("DB URL:", url)
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
    return "".join([f"{question}\nDatabase Schema:\n",str(db_content)]), prompt.format(
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
    print(f"[INFO] Asking question: {question}")
    response1 = client.ask(formatted_q,formatted_prompt, **kwargs)
    duration = time.time() - start
    if isinstance(response1, tuple):  # Gemini returns (text, usage)
        #response= correct(client, formatted_q, response1[0], formatted_prompt, db_name=db_name)
        return response1[0], duration, response1[1]
    #response= correct(client, formatted_q, response1, formatted_prompt, db_name=db_name)
    return response1, duration, None

def run_models_parallel(prompt, data, row, script, models_to_test, db_markdown_map=None, retries=3, **kwargs):
    question = row["question"]
    db_name = row.get("db_name", None)
    formatted_q, formatted_prompt = format_prompt(prompt, data, question, script, db_name, db_markdown_map)

    db_path = os.path.join("./test_data", "databases", row["dataset_name"], f"{db_name}.db")
    metadata_path = os.path.join("./test_data", "metadata", row["dataset_name"], f"{db_name}_graph.json")

    def run_model(model_info, attempt):
        provider_name = model_info["provider"]
        model_id = model_info["model_id"]
        config = model_info["config"]
        client = get_provider(provider_name, model_id, config=config)
        start = time.time()
        try:
            response = client.ask(formatted_q, formatted_prompt, **kwargs)
            duration = time.time() - start
            if isinstance(response, tuple):
                code, usage = response
            else:
                code, usage = response, None

            df = None
            if code:
                env = {"pydough": pydough, "datetime": datetime}
                df, _ = execute_code_and_extract_result(code, env, metadata_path, db_name, db_path)
        except Exception as e:
            code, duration, usage, df = None, time.time() - start, None, None
            print(f"[ERROR] Model {model_info['name']} failed on attempt {attempt}: {e}")

        return {
            "model_name": model_info["name"],
            "attempt": attempt,
            "code": code,
            "duration": duration,
            "usage": usage,
            "df": df,
        }

    all_runs = []
    with ThreadPoolExecutor(max_workers=len(models_to_test) * retries) as executor:
        futures = []
        for model in models_to_test:
            for attempt in range(retries):
                futures.append(executor.submit(run_model, model, attempt))
        all_runs = [f.result() for f in futures]

    # Group runs by model name
    grouped = {}
    for run in all_runs:
        grouped.setdefault(run["model_name"], []).append(run)

    # Detect early match between Gemini and Claude
    for i in range(retries):
        gemini_run = grouped.get("gemini", [])[i]
        claude_run = grouped.get("claude", [])[i]
        if gemini_run["df"] is not None and claude_run["df"] is not None:
            if compare_df(gemini_run["df"], claude_run["df"], query_category="a", question=question):
                print(f"[INFO] Early match found on attempt {i}. Returning Gemini result.")
                return gemini_run["code"], gemini_run["duration"], gemini_run["usage"]

    # Fallback: use ensemble result
    print("[INFO] No early match found. Running ensemble fallback...")
    return ensemble_result(all_runs, question)

def ensemble_result(all_runs, question):
    """
    Uses dataframe comparison to select the most consistent output.
    """
    valid_runs = [r for r in all_runs if r["df"] is not None]
    if not valid_runs:
        print("[WARNING] No valid dataframes to ensemble.")
        return None, 0.0, None

    consensus = defaultdict(int)

    for i in range(len(valid_runs)):
        for j in range(i + 1, len(valid_runs)):
            if compare_df(valid_runs[i]["df"], valid_runs[j]["df"], query_category="a", question=question):
                consensus[i] += 1
                consensus[j] += 1

    if consensus:
        best_index = max(consensus, key=lambda i: consensus[i])
        best = valid_runs[best_index]
        print(f"[INFO] Ensemble selected: {best['model_name']} with {consensus[best_index]} matches.")
        return best["code"], best["duration"], best["usage"]

    gemini_runs = [r for r in valid_runs if r["model_name"] == "gemini"]
    if gemini_runs:
        fallback = random.choice(gemini_runs)
        print("[INFO] No consensus found. Falling back to Gemini run.")
        return fallback["code"], fallback["duration"], fallback["usage"]
    else:
        print("[WARNING] No Gemini runs available. Falling back to random valid run.")
        fallback = random.choice(valid_runs)
        return fallback["code"], fallback["duration"], fallback["usage"]

def process_questions(data, provider, model_id, prompt, questions_df, script, threads, db_markdown_map=None, use_parallel=False, **kwargs):
    def thread_wrapper(row):
        if use_parallel:
            return run_models_parallel(
                prompt=prompt,
                data=data,
                row=row,
                script=script,
                models_to_test=models_to_test,
                db_markdown_map=db_markdown_map,
                **kwargs
            )
        else:
            client = get_provider(provider, model_id)
            return get_response(
                client=client,
                prompt=prompt,
                data=data,
                row=row,
                script=script,
                db_markdown_map=db_markdown_map,
                **kwargs
            )

    # If using parallel, we expect models_to_test to be defined globally or passed via kwargs
    if use_parallel:
        if "models_to_test" not in kwargs:
            raise ValueError("models_to_test must be provided when use_parallel=True")

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
    parser.add_argument('--db-base-path', type=str, required=True)
    parser.add_argument('--metadata-base-path', type=str, required=True)
    parser.add_argument("--pydough_file", type=str)
    parser.add_argument("--prompt_file", type=str)
    parser.add_argument("--questions", type=str)
    parser.add_argument("--provider", type=str)
    parser.add_argument("--model_id", type=str)
    parser.add_argument("--num_threads", type=int)
    parser.add_argument("--use-parallel", action="store_true")
    parser.add_argument("--extra_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    kwargs = parse_extra_args(args.extra_args)

    MLFLOW_TRACKING_URI = "http://mlflow-alb-1071096006.us-east-2.elb.amazonaws.com"
    MLFLOW_TRACKING_TOKEN = os.environ["MLFLOW_TRACKING_TOKEN"]
    #mlflow.gemini.autolog()
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    experiment = mlflow.set_experiment(args.experiment_name)

    with mlflow.start_run(description=args.description, run_name=args.name, tags={"GIT_COMMIT": git_hash}, experiment_id=experiment.experiment_id):

        prompt = read_file(args.prompt_file)
        script = read_file(args.pydough_file)

        with open("./queries_context.json") as f:
            data = json.load(f)

        df = pd.read_csv(args.questions)
        db_markdown_map = prepare_db_markdown_map(df, args.metadata_base_path, args.db_base_path)

        results = process_questions(
        data,
        provider=args.provider.lower(),
        model_id=args.model_id,
        prompt=prompt,
        questions_df=df,
        script=script,
        threads=args.num_threads,
        db_markdown_map=db_markdown_map,
        use_parallel=args.use_parallel,
        models_to_test=models_to_test,
        **kwargs
        )

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
        filtered_args = {key: value for key, value in vars(args).items() if key not in ['name', 'description', 'extra_args']}

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

            for diff, pct in match_pct_difficulty.items():
                mlflow.log_metric(f"match_pct_difficulty_{diff}", pct)

            for comp, pct in match_pct_complexity.items():
                mlflow.log_metric(f"match_pct_complexity_{comp}", pct)

            for (diff, comp), pct in match_pct_combo.items():
                mlflow.log_metric(f"match_pct_{diff}_{comp}", pct)

            non_matches_per_difficulty = non_match_df["difficulty"].value_counts()
            non_matches_per_complexity = non_match_df["complexity"].value_counts()
            non_matches_per_combo = non_match_df.groupby(["difficulty", "complexity"]).size()

            no_match_pct_difficulty = non_matches_per_difficulty / total_per_difficulty
            no_match_pct_complexity = non_matches_per_complexity / total_per_complexity
            no_match_pct_combo = non_matches_per_combo / total_per_combo

            for diff, pct in no_match_pct_difficulty.items():
                mlflow.log_metric(f"no_match_pct_difficulty_{diff}", pct)

            for comp, pct in no_match_pct_complexity.items():
                mlflow.log_metric(f"no_match_pct_complexity_{comp}", pct)

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
            mlflow.log_artifact(match_pct_combo_csv)

            # Difficulty + db
            match_pct_difficulty_df = (matches_per_difficulty_db / total_per_difficulty_db).reset_index()
            match_pct_difficulty_df.columns = ["difficulty", "db_name", "match_percentage"]
            match_pct_difficulty_csv = f"{output_path}/match_percentage_per_difficulty_db.csv"
            match_pct_difficulty_df.to_csv(match_pct_difficulty_csv, index=False)
            mlflow.log_artifact(match_pct_difficulty_csv)

            # Complexity + db
            match_pct_complexity_df = (matches_per_complexity_db / total_per_complexity_db).reset_index()
            match_pct_complexity_df.columns = ["complexity", "db_name", "match_percentage"]
            match_pct_complexity_csv = f"{output_path}/match_percentage_per_complexity_db.csv"
            match_pct_complexity_df.to_csv(match_pct_complexity_csv, index=False)
            mlflow.log_artifact(match_pct_complexity_csv)
            # Save raw counts as CSV artifacts if needed
            matches_per_difficulty.to_csv(f"{output_path}/match_count_per_difficulty.csv")
            matches_per_complexity.to_csv(f"{output_path}/match_count_per_complexity.csv")
            matches_per_combo.to_csv(f"{output_path}/match_count_per_difficulty_complexity.csv")

            mlflow.log_artifact(f"{output_path}/match_count_per_difficulty.csv")
            mlflow.log_artifact(f"{output_path}/match_count_per_complexity.csv")
            mlflow.log_artifact(f"{output_path}/match_count_per_difficulty_complexity.csv")
            # Group by db_name, difficulty, and complexity
            count_combo = df.groupby(['db_name', 'difficulty', 'complexity']).size().reset_index(name='count')
            total_combo = count_combo['count'].sum()
            count_combo['percentage'] = (count_combo['count'] / total_combo) * 100

            # Group by db_name and complexity
            count_complexity_db = df.groupby(['db_name', 'complexity']).size().reset_index(name='count')
            total_complexity = count_complexity_db['count'].sum()
            count_complexity_db['percentage'] = (count_complexity_db['count'] / total_complexity) * 100

            # Group by db_name and difficulty (optional)
            count_difficulty_db = df.groupby(['db_name', 'difficulty']).size().reset_index(name='count')
            total_difficulty = count_difficulty_db['count'].sum()
            count_difficulty_db['percentage'] = (count_difficulty_db['count'] / total_difficulty) * 100

            # === Group and Calculate Percentage by difficulty
            count_difficulty = df.groupby('difficulty').size().reset_index(name='count')
            total_difficulty = count_difficulty['count'].sum()
            count_difficulty['percentage'] = (count_difficulty['count'] / total_difficulty) * 100

            # === Group and Calculate Percentage by complexity
            count_complexity = df.groupby('complexity').size().reset_index(name='count')
            total_complexity = count_complexity['count'].sum()
            count_complexity['percentage'] = (count_complexity['count'] / total_complexity) * 100

            output_dir = f"{output_path}/distribution_reports"
            os.makedirs(output_dir, exist_ok=True)

            combo_path = f"{output_dir}/distribution_difficulty_complexity.csv"
            complexity_path = f"{output_dir}/distribution_complexity_db.csv"
            difficulty_path = f"{output_dir}/distribution_difficulty_db.csv"
            count_complexity_db.to_csv(complexity_path, index=False)
            count_difficulty_db.to_csv(difficulty_path, index=False)

            mlflow.log_artifact(difficulty_path)
            mlflow.log_artifact(complexity_path)
            count_combo.to_csv(combo_path, index=False)
            count_complexity.to_csv(complexity_path, index=False)
            count_difficulty.to_csv(difficulty_path, index=False)
            difficulty_path = f"{output_dir}/overall_distribution_difficulty.csv"
            complexity_path = f"{output_dir}/overall_distribution_complexity.csv"

            count_difficulty.to_csv(difficulty_path, index=False)
            count_complexity.to_csv(complexity_path, index=False)

            mlflow.log_artifact(difficulty_path)
            mlflow.log_artifact(complexity_path)

            mlflow.log_artifact(combo_path)
            mlflow.log_artifact(complexity_path)
            mlflow.log_artifact(difficulty_path)
        mlflow.log_params(filtered_args)
        mlflow.log_params(kwargs)
        mlflow.log_metrics(percentages)
        mlflow.log_metric("total_queries", total_rows)
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
