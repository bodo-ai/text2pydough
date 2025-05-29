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
from test_data.eval import execute_code_and_extract_result, compare_df, query_sqlite_db
import aisuite as ai
from provider.ai_providers import *
from dynamic_prompt.generate_pydough_metadata import generate_metadata
from dynamic_prompt.mdgen import json_to_markdown
from sqlalchemy import create_engine, inspect, text
from gemini_wrapper import GeminiWrapper

# === Helper Functions ===

models_to_evaluate = [
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
        return AzureAIProvider(model_id)
    elif provider == "aws-deepseek":
        return DeepSeekAIProvider(model_id)
    elif provider == "google":
        return GeminiAIProvider(model_id, **(config or {}))
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
    if not isinstance(text, str):
        return ""

    # Buscar bloques de código markdown (```python ... ```)
    matches = re.findall(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    if matches:
        return textwrap.dedent(matches[-1]).strip()

    # Fallback: intentar detectar un bloque al final del texto si no está bien cerrado
    approx_code_start = text.rfind("```python")
    if approx_code_start != -1:
        return textwrap.dedent(text[approx_code_start + 9:]).strip()  # Skip '```python\n'

    # Último fallback: devolver todo (no recomendado si hay explicaciones largas)
    return textwrap.dedent(text).strip()

def prepare_db_markdown_map(df, metadata_base_path, db_base_path):
    db_names = df["db_name"]
    dataset_names = df["dataset_name"]
    db_markdown_map = {}
    for db_name, dataset_name in zip(db_names, dataset_names):
        metadata_dir = os.path.join(metadata_base_path, "metadata", dataset_name)
        json_file = os.path.join(metadata_dir, f"{db_name}_graph.json")
        # Only generate if missing
        if not os.path.exists(json_file):
            print(f"[INFO] Generating JSON for: {db_name}")
            url = f"sqlite:///{os.path.join(db_base_path, "databases", dataset_name, f"{db_name}.db")}"
            print(f"[INFO] Connecting to: {url}")
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
    return "".join([f"\n\n\nQuestion: {question}\n"]), prompt.format(
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

def process_questions(data, prompt, questions_df, script, threads, models_to_evaluate, db_base_path, metadata_base_path, db_markdown_map=None, **kwargs):
    print("[DEBUG] Entrando a process_questions con", len(questions_df), "preguntas")
    def thread_wrapper(row):
        print(f"[DEBUG] Procesando pregunta: {row['question']}")
        # 1. Ejecutar modelos en paralelo
        responses = run_models_parallel(
            row,
            models_to_evaluate,
            prompt_template=prompt,
            data=data,
            script=script,
            db_markdown_map=db_markdown_map,
            **kwargs
        )
        
        print(f"[DEBUG] Respuestas recibidas para: {row['question']}")

        # 2. Evaluar resultados
        evaluation = evaluate_models(
            row=row,
            responses=responses,
            db_base_path=db_base_path,
            metadata_base_path=metadata_base_path
        )
        
        print(f"[DEBUG] Evaluación completada para: {row['question']}, Ganador: {evaluation['winner']}")


        # 3. Consolidar información por fila
        return {
            "question": row["question"],
            "db_name": row.get("db_name"),
            "dataset_name": row.get("dataset_name"),
            "responses": responses,  # raw output por modelo
            "winner_model": evaluation["winner"],
            "comparison_result": evaluation["result"],
            "code": evaluation["code"],
            "exception": evaluation["exception"],
            "all_model_results": evaluation["all_results"]
        }

    with ThreadPoolExecutor(max_workers=threads) as executor:
        results = list(executor.map(thread_wrapper, [row for _, row in questions_df.iterrows()]))

    return results


def run_models_parallel(row, models_to_evaluate, prompt_template, data, script, db_markdown_map=None, **kwargs):
    question = row["question"]
    db_name = row.get("db_name", None)

    # Formatear el prompt
    formatted_q, formatted_prompt = format_prompt(prompt_template, data, question, script, db_name, db_markdown_map)

    # Función interna para pedir a un modelo
    def ask_model(model_entry):
        name = model_entry["name"]
        provider = model_entry["provider"]
        model_id = model_entry["model_id"]
        config = model_entry.get("config", {})

        try:
            client = get_provider(provider, model_id, config)
            response = client.ask(formatted_q, formatted_prompt, **kwargs)
            if isinstance(response, tuple):
                code, usage = response
            else:
                code, usage = response, None
            return name, {
                "code": code,
                "usage": usage,
                "exception": None
            }
        except Exception as e:
            return name, {
                "code": None,
                "usage": None,
                "exception": str(e)
            }

    # Ejecutar todos los modelos en paralelo
    with ThreadPoolExecutor(max_workers=len(models_to_evaluate)) as executor:
        futures = [executor.submit(ask_model, model) for model in models_to_evaluate]
        results = dict(f.result() for f in futures)

    return results

def evaluate_models(row, responses, db_base_path, metadata_base_path):
    question = row["question"]
    db_name = row["db_name"]
    dataset_name = row["dataset_name"]
    sql_gold = row["sql"]
    
    print(f"[DEBUG] Entrando a evaluate_models para: {question}")

    db_path = os.path.join(db_base_path, "databases", dataset_name, f"{db_name}.db")
    metadata_path = os.path.join(metadata_base_path, "metadata", dataset_name, f"{db_name}_graph.json")

    model_results = {}

    for model_name, response in responses.items():
        code = response.get("code")
        code = extract_python_code(code)
        local_env = {"pydough": pydough, "datetime": datetime}

        if code is None:
            model_results[model_name] = {
                "result": "Query Error",
                "exception": response.get("exception"),
                "code": None
            }
            continue

        result_df, exception = execute_code_and_extract_result(code, local_env, metadata_path, db_name, db_path)

        if result_df is None:
            model_results[model_name] = {
                "result": "Query Error",
                "exception": str(exception),
                "code": code
            }
            continue

        sql_df, sql_error = query_sqlite_db(sql_gold, db_path)
        if sql_df is None:
            model_results[model_name] = {
                "result": "SQL Error",
                "exception": sql_error,
                "code": code
            }
            continue

        match = compare_df(result_df, sql_df, query_category="a", question=question, query_gold=sql_gold, query_gen=code)
        model_results[model_name] = {
            "result": "Match" if match else "No Match",
            "exception": None,
            "code": code
        }

    # decidir cuál usar
    if len(model_results) == 1:
        # Solo hay un modelo, devolver directamente
        only_model = list(model_results.keys())[0]
        return {
            "winner": only_model,
            **model_results[only_model],
            "all_results": model_results
        }

    # Si hay múltiples, escoger el mejor resultado
    priority = ["Match", "No Match", "SQL Error", "Query Error"]
    for label in priority:
        for model, result in model_results.items():
            if result["result"] == label:
                return {
                    "winner": model,
                    **result,
                    "all_results": model_results
                }

    # fallback
    return {
        "winner": None,
        "result": "Unknown",
        "code": None,
        "exception": "No valid response",
        "all_results": model_results
    }


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
    print("[DEBUG] Entrando al main()")
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
    #mlflow.gemini.autolog()
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    experiment = mlflow.set_experiment(args.experiment_name)
    print("[DEBUG] Iniciando run en MLFlow...")
    with mlflow.start_run(description=args.description, run_name=args.name, tags={"GIT_COMMIT": git_hash}, experiment_id=experiment.experiment_id):

        prompt = read_file(args.prompt_file)
        script = read_file(args.pydough_file)

        with open("./queries_context.json") as f:
            data = json.load(f)

        df = pd.read_csv(args.questions)
        db_markdown_map = prepare_db_markdown_map(df, args.metadata_base_path, args.db_base_path)
        
        print("[DEBUG] Ejecutando process_questions()...")
        results = process_questions(
            data=data,
            prompt=prompt,
            questions_df=df,
            script=script,
            threads=args.num_threads,
            models_to_evaluate=models_to_evaluate,
            db_base_path=args.db_base_path,
            metadata_base_path=args.metadata_base_path,
            db_markdown_map=db_markdown_map,
            **kwargs
        )

        # === OUTPUT DIR ===
        output_path = f"./results/ensemble_eval"
        os.makedirs(output_path, exist_ok=True)

        # === CSV 1: RAW RESPONSES ===
        raw_rows = []
        for r in results:
            for model_name, data in r["responses"].items():
                raw_rows.append({
                    "question": r["question"],
                    "db_name": r["db_name"],
                    "dataset_name": r["dataset_name"],
                    "model": model_name,
                    "code": data.get("code"),
                    "exception": data.get("exception"),
                    "usage": data.get("usage")
                })
        raw_df = pd.DataFrame(raw_rows)
        raw_output_file = f"{output_path}/raw_responses_{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.csv"
        raw_df.to_csv(raw_output_file, index=False)
        mlflow.log_artifact(raw_output_file)

        # === CSV 2: EVALUATED RESPONSES ===
        final_df = pd.DataFrame(results)

        # Extraer modelos dinámicamente
        all_models = set()
        for r in results:
            all_models.update(r.get("all_model_results", {}).keys())

        for model in sorted(all_models):
            final_df[f"{model}_code"] = final_df["all_model_results"].apply(lambda d: d.get(model, {}).get("code"))
            final_df[f"{model}_result"] = final_df["all_model_results"].apply(lambda d: d.get(model, {}).get("result"))
            final_df[f"{model}_exception"] = final_df["all_model_results"].apply(lambda d: d.get(model, {}).get("exception"))

        evaluated_output_file = f"{output_path}/evaluated_responses_{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.csv"
        final_df.to_csv(evaluated_output_file, index=False)
        mlflow.log_artifact(evaluated_output_file)
        
        print(f"[DEBUG] Guardado CSV: {raw_output_file}")
        print(f"[DEBUG] Guardado CSV: {evaluated_output_file}")


        # === MÉTRICAS Y LOGGING ===
        total_rows = len(final_df)
        counts = final_df["comparison_result"].value_counts()
        percentages = counts / total_rows

        for label, frac in percentages.items():
            mlflow.log_metric(f"comparison_{label.replace(' ', '_')}", float(frac))

        mlflow.log_metric("total_queries", total_rows)
        mlflow.log_param("models_used", list(sorted(all_models)))

        metrics_dict = {f"comparison_{label.replace(' ', '_')}": float(frac) for label, frac in percentages.items()}
        metrics_dict["total_queries"] = total_rows
        metrics_path = "./metrics.json"
        with open(metrics_path, "w") as f:
            json.dump(metrics_dict, f, indent=4)
        mlflow.log_artifact(metrics_path)

        # === REGISTRO DEL MODELO USADO (si se quiere)
        mlflow.pyfunc.log_model(
            artifact_path="model",
            python_model=GeminiWrapper(model_id=args.model_id),
            artifacts={
                "prompt_file": args.prompt_file,
                "pydough_file": args.pydough_file,
                "metrics": metrics_path
            }
        )
        
        print("[DEBUG] Terminando run de MLFlow")

if __name__ == "__main__":
    cwd = os.getcwd()
    db_path = './test_data/TPCH.db'
    download_database(db_path)
    if untracked_files(cwd) or modified_files(cwd):
        autocommit(cwd)
    main(get_git_commit(cwd))