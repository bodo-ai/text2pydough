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

import pydough
from utils import autocommit, get_git_commit, modified_files, untracked_files, download_database
from test_data.eval import compare_output, execute_code_and_extract_result
from claude import ClaudeModel, DeepseekModel, GeminiModel
import aisuite as ai

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import UserMessage, SystemMessage
from azure.core.credentials import AzureKeyCredential
from abc import ABC, abstractmethod

# === Abstract Class for AI Providers ===
class AIProvider(ABC):
    @abstractmethod
    def ask(self, question, prompt, **kwargs):
        pass

# === Azure Provider ===
class AzureAIProvider(AIProvider):
    def __init__(self, model_id):
        self.client = self.setup_azure_client()
        self.model_id = model_id

    def setup_azure_client(self):
        endpoint = os.getenv("AZURE_BASE_URL")
        key = os.getenv("AZURE_API_KEY")
        if not endpoint or not key:
            raise ValueError("Azure environment variables are not set.")
        return ChatCompletionsClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    def ask(self, question, prompt, **kwargs):
        messages = [SystemMessage(prompt), UserMessage(question)]
        try:
            completion = self.client.complete(messages=messages, max_tokens=kwargs.get("max_tokens", 20000),
                                              model=self.model_id, stream=True)
            return "".join([chunk.choices[0]["delta"]["content"] for chunk in completion if chunk.choices])
        except Exception as e:
            print(f"Azure error: {e}")
            return None

# === Claude, Deepseek, Gemini, AI Suite Providers ===
class ClaudeAIProvider(AIProvider):
    def __init__(self, provider, model_id):
        self.client = ClaudeModel()
        self.provider = provider
        self.model_id = model_id

    def ask(self, question, prompt, **kwargs):
        return self.client.ask_claude_with_stream(question, prompt, self.model_id, self.provider, **kwargs)

class DeepSeekAIProvider(AIProvider):
    def __init__(self, provider, model_id, temperature):
        self.client = DeepseekModel(temperature)
        self.provider = provider
        self.model_id = model_id

    def ask(self, question, prompt, **kwargs):
        return self.client.ask_claude_with_stream(question, prompt, self.model_id, self.provider, **kwargs)

class GeminiAIProvider(AIProvider):
    def __init__(self, provider, model_id, temperature):
        self.client = GeminiModel(temperature)
        self.provider = provider
        self.model_id = model_id

    def ask(self, question, prompt, **kwargs):
        response = self.client.generate_content(question, prompt, self.model_id, self.provider, **kwargs)
        return response.text, response.usage_metadata

class OtherAIProvider(AIProvider):
    def __init__(self, provider, model_id, temperature, config=None):
        self.client = ai.Client(config) if config else ai.Client()
        self.provider = provider
        self.model_id = model_id
        self.temperature = temperature

    def ask(self, question, prompt, **kwargs):
        messages = [{"role": "system", "content": prompt}, {"role": "user", "content": question}]
        try:
            response = self.client.chat.completions.create(
                model=f"{self.provider}:{self.model_id}",
                messages=messages,
                temperature=self.temperature,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"AI Suite error: {e}")
            return None

# === Helper Functions ===
def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def extract_python_code(text):
    if not isinstance(text, str): return ""
    matches = re.findall(r"```(?:\w+\n)?(.*?)```", text, re.DOTALL)
    return textwrap.dedent(matches[-1]).strip() if matches else ""

def format_prompt(prompt, data, question, db_content, script, db_name=None):
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

# === Model Response Helpers ===
def get_azure_response(client, prompt, data, question, db, script, **kwargs):
    formatted_q, formatted_prompt = format_prompt(prompt, data, question, db, script)
    response = client.ask(formatted_q, formatted_prompt, **kwargs)
    return correct(client, formatted_q, response, formatted_prompt), None

def get_claude_response(client, prompt, data, question, db, script, **kwargs):
    formatted_q, formatted_prompt = format_prompt(prompt, data, question, db, script)
    start = time.time()
    response = client.ask(formatted_q, formatted_prompt, **kwargs)
    return correct(client, formatted_q, response, formatted_prompt), time.time() - start

def get_gemini_response(client, prompt, data, df, db, script, **kwargs):
    question = df["question"]
    db_name = df["db_name"]
    formatted_q, formatted_prompt = format_prompt(prompt, data, question, db, script, db_name)
    start = time.time()
    response, usage = client.ask(formatted_q, formatted_prompt, **kwargs)
    return response, time.time() - start, usage

def get_other_provider_response(client, prompt, data, question, db, script, **kwargs):
    formatted_q, formatted_prompt = format_prompt(prompt, data, question, db, script)
    start = time.time()
    response = client.ask(formatted_q, formatted_prompt, **kwargs)
    return correct(client, formatted_q, response, formatted_prompt), time.time() - start

# === Processor Wrapper ===
def process_question_wrapper(args):
    provider, model_id, prompt, data, q, temperature, db, script, kwargs = args
    client = {
        "azure": AzureAIProvider(model_id),
        "aws-thinking": ClaudeAIProvider(provider, model_id),
        "aws-deepseek": DeepSeekAIProvider(provider, model_id, temperature),
        "google": GeminiAIProvider(provider, model_id, temperature)
    }.get(provider, OtherAIProvider(provider, model_id, temperature))

    func_map = {
        "azure": get_azure_response,
        "aws-thinking": get_claude_response,
        "aws-deepseek": get_claude_response,
        "google": get_gemini_response
    }

    handler = func_map.get(provider, get_other_provider_response)
    return handler(client, prompt, data, q, db, script, **kwargs)

def process_questions(data, provider, model_id, prompt, questions_df, temperature, db, script, threads, **kwargs):
    with multiprocessing.Pool(threads) as pool:
        return pool.map(process_question_wrapper, [
            (provider, model_id, prompt, data, row, temperature, db, script, kwargs)
            for _, row in questions_df.iterrows()
        ])

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
    parser.add_argument("--database_structure", type=str)
    parser.add_argument("--prompt_file", type=str)
    parser.add_argument("--questions", type=str)
    parser.add_argument("--provider", type=str)
    parser.add_argument("--model_id", type=str)
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--num_threads", type=int)
    parser.add_argument("--extra_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    kwargs = parse_extra_args(args.extra_args)

    mlflow.set_tracking_uri("http://127.0.0.1:5000")
    experiment = mlflow.set_experiment("text2pydough")
    with mlflow.start_run(description=args.description, run_name=args.name, tags={"GIT_COMMIT": git_hash}, experiment_id=experiment.experiment_id):
        prompt = read_file(args.prompt_file)
        script = read_file(args.pydough_file)
        db_content = read_file(args.database_structure)
        with open("./queries_context.json") as f: data = json.load(f)
        df = pd.read_csv(args.questions)
        results = process_questions(data, args.provider.lower(), args.model_id, prompt, df, args.temperature, db_content, script, args.num_threads, **kwargs)

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

        mlflow.log_params(vars(args))
        mlflow.log_params(kwargs)
        mlflow.log_metric("total_queries", len(tested_df))
        mlflow.log_artifact(tested_file)

if __name__ == "__main__":
    cwd = os.getcwd()
    db_path = './test_data/TPCH.db'
    download_database(db_path)
    if untracked_files(cwd) or modified_files(cwd):
        autocommit(cwd)
    main(get_git_commit(cwd))
