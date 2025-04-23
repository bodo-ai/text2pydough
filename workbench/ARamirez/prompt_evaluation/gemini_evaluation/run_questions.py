# simplified_main.py

from abc import ABC, abstractmethod
import argparse
import os
import json
import re
import textwrap
import time
from datetime import datetime

import pandas as pd
import pydough
from test_data.eval import compare_output, execute_code_and_extract_result
from google import genai
from google.genai import types

# === Abstract Class for AI Providers ===
class AIProvider(ABC):
    @abstractmethod
    def ask(self, question, prompt, **kwargs):
        pass

class GeminiAIProvider(AIProvider):

    def __init__(self, model_id):
        try:
            self.api_key = os.environ["GOOGLE_API_KEY"]  
            self.project = os.environ["GOOGLE_PROJECT_ID"]
            self.location = os.environ["GOOGLE_REGION"]
            self.model_id = model_id
        except KeyError:
            raise RuntimeError("Environment variable 'GOOGLE_API_KEY' is required but not set.")
        self.client = genai.Client(vertexai=True, project=self.project, location=self.location)
    
    def ask(self, question, prompt, **kwargs):
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=question,
            config=types.GenerateContentConfig(
                system_instruction=prompt,
                temperature= 0,
                top_p= 1.0,
                seed= 42,
            ),
        )
        return response.text, response.usage_metadata
   
   
# ============ Utility Functions ============

def read_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def extract_python_code(text):
    if not isinstance(text, str):
        return ""
    matches = re.findall(r"```(?:\w+\n)?(.*?)```", text, re.DOTALL)
    return textwrap.dedent(matches[-1]).strip() if matches else ""

def format_prompt(prompt_template, data, question, script, db_name=None):
    db_content = ""
    if db_name:
        db_path = f"{db_name}_graph.md"
        db_content = read_file(db_path)

    q_data = data.get(question, {})
    formatted_q = q_data.get("redefined_question", question)
    formatted_prompt = prompt_template.format(
        script_content=script,
        database_content=db_content,
        similar_queries="No similar queries found",
        recomendation=""
    )
    return formatted_q, formatted_prompt

def process_questions(data, prompt_template, df, script):
    client = GeminiAIProvider("gemini-2.0-flash-001")
    responses = []
    for _, row in df.iterrows():
        try:
            question = row["question"]
            db_name = row.get("db_name", None)
            formatted_q, formatted_prompt = format_prompt(prompt_template, data, question, script, db_name)

            start = time.time()
            response = client.ask(formatted_q, formatted_prompt)
            duration = time.time() - start

            if isinstance(response, tuple):
                response = response[0]

            responses.append((response, duration))
        except Exception as e:
            responses.append((f"# Error processing question: {e}", 0.0))
    return responses

# ============ Entry Point ============

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pydough_file", required=True, help="Path to the pydough script file")
    parser.add_argument("--prompt_file", required=True, help="Path to the prompt template file")
    parser.add_argument("--questions", required=True, help="CSV with questions")
    args = parser.parse_args()

    try:
        prompt_template = read_file(args.prompt_file)
        script = read_file(args.pydough_file)

        with open("./queries_context.json", "r") as f:
            data = json.load(f)

        df = pd.read_csv(args.questions)
        results = process_questions(data, prompt_template, df, script)

        df["response"] = [r[0] for r in results]
        df["execution_time"] = [r[1] for r in results]
        df["extracted_python_code"] = df["response"].apply(extract_python_code)

        output_path = f"./results"
        os.makedirs(output_path, exist_ok=True)
        output_file = f"{output_path}/responses_{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.csv"
        df.to_csv(output_file, index=False)

        test_path = f"{output_path}/test"
        os.makedirs(test_path, exist_ok=True)
        tested_file, tested_df = compare_output(test_path, output_file)
        total_rows = len(tested_df)
        print(f"✅ Responses saved to {output_file}")

    except Exception as e:
        print(f"❌ Failed to complete process: {e}")

if __name__ == "__main__":
    main()
