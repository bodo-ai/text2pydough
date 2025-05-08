import argparse
from numba.types import Tuple
import ast
import bodo
import json
import os
import re
import pandas as pd
import aisuite as ai
import time
import hashlib
from datetime import datetime
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import UserMessage, SystemMessage
from azure.core.credentials import AzureKeyCredential
from test_data.eval import compare_df, compare_output, execute_code_and_extract_result, execute_code_and_extract_result_hash_bodo
from utils import download_database
from claude import ClaudeModel, DeepseekModel
from collections import defaultdict
import pydough
from abc import ABC, abstractmethod

# === Abstract Class for AI Providers ===
class AIProvider(ABC):
    """Abstract class defining the interface for AI providers."""

    @abstractmethod
    def ask(self, question):
        """Returns a response for a given question."""
        pass


# === Azure AI Provider ===
class AzureAIProvider(AIProvider):
    """Handles responses from Azure AI."""

    def __init__(self, model_id):
        self.client = self.setup_azure_client()
        self.model_id = model_id

    def setup_azure_client(self):
        """Initializes and returns the Azure ChatCompletionsClient."""
        endpoint = os.getenv("AZURE_BASE_URL")
        key = os.getenv("AZURE_API_KEY")

        if not endpoint or not key:
            raise ValueError("Azure environment variables are not set correctly.")

        return ChatCompletionsClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    def ask(self, question, prompt):
        """Generates a response using Azure AI."""
        formatted_prompt = prompt
        messages = [SystemMessage(formatted_prompt), UserMessage(question)]

        try:
            completion = self.client.complete(messages=messages, max_tokens=20000, model=self.model_id, stream=True)
            response = [chunk.choices[0]["delta"]["content"] for chunk in completion if chunk.choices]
            return "".join(response)
        except Exception as e:
            #print(f"Azure AI error: {e}")
            return None

class DeepSeekAIProvider(AIProvider):
    """Handles responses from Claude AI."""

    def __init__(self, provider, model_id, temperature):
        self.client = DeepseekModel(temperature)
        self.provider = provider
        self.model_id = model_id

    def ask(self, question, prompt):
        """Generates a response using Claude AI."""
        return self.client.ask_claude_with_stream(question, prompt, self.model_id, self.provider)


# === Claude AI Provider ===
class ClaudeAIProvider(AIProvider):
    """Handles responses from Claude AI."""

    def __init__(self, provider, model_id):
        self.client = ClaudeModel()
        self.provider = provider
        self.model_id = model_id

    def ask(self, question, prompt):
        """Generates a response using Claude AI."""
        return self.client.ask_claude_with_stream(question, prompt, self.model_id, self.provider)


# === Other AI Providers (e.g., AI Suite) ===
class OtherAIProvider(AIProvider):
    """Handles responses from other AI providers like AI Suite."""

    def __init__(self, provider, model_id, temperature, config= None):
        self.client = ai.Client(config) if config else ai.Client()
        self.provider = provider
        self.model_id = model_id
        self.temperature= temperature


    def ask(self, question, prompt):
        """Generates a response using AI Suite."""
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"{question}"},
        ]

        try:
            time.sleep(0.5)  # Simulate slight delay
            response = self.client.chat.completions.create(
                model=f"{self.provider}:{self.model_id}",
                messages=messages,
                temperature=self.temperature
            
            )
            return response.choices[0].message.content
        except Exception as e:
            #print(f"AI Suite error: {e}")
            return None, None 

def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

@bodo.jit(cache=True)
def extract_python_code(text):
    """Extracts Python code from triple backticks in text."""
    if not isinstance(text, str):  # Ensure text is a string
        return ""

    matches = re.findall(r"```(?:\w+\n)?(.*?)```", text, re.DOTALL)
    return matches[-1].strip() if matches else ""

def format_prompt(prompt, data, question, database_content, script_content):
    if question in data:
        recomendation = data[question].get("context_id", "")
        similar_code= data[question].get("similar_queries", "similar code not found")
        question = data[question].get("redefined_question", question)
 
    else:
        recomendation=""
        similar_code= "similar pydough code not found"
    
    return question, prompt.format(script_content=script_content, database_content=database_content, similar_queries=similar_code, recomendation=recomendation)

def correct(client, question,  code, prompt):
    extracted_code= extract_python_code(code)
    local_env = {"pydough": pydough, "datetime": datetime}
    response= code    
    result, exception= execute_code_and_extract_result(extracted_code, local_env)
    
    if result is None:

        q= (f"""
        Review and correct the provided Pydough code based on the given exception and original question.
        - Analyze the provided Pydough code for syntax errors, logical errors, and exceptions.
        - Identify the specific line or section where the exception occurs. 
        - Consider the context of the original question to ensure that the code aligns with the intended functionality.
        - Do not assume if a method exists.
        - Follow the rules provided in pydough.    
        - Return the same output but with the corrected code.
        An error occurred while processing this code: {code}. 
        The error is: '{exception}'. 
        The original question was: '{question}'. 
        Can you help me fix the issue? Please make sure to use the right syntax and rules for creating pydough code.""")

        response=client.ask(q, prompt)
        return "".join([code, response])
    return response

def get_azure_response(client, prompt, data, question, database_content, script_content):
    """Generates a response using Azure AI."""
    formatted_prompt = format_prompt(prompt,data,question,database_content, script_content)
    
    try:
        response= client.ask(question, formatted_prompt)
        corrected_response= correct(client,question,response, formatted_prompt)
        return corrected_response, None
    except Exception as e:
        #print(f"Azure AI error: {e}")
        return None

def get_response(client, updated_question, formatted_prompt):
    """Generates a response using aisuite."""
    try:
        response = client.ask(updated_question, formatted_prompt)
        return response
    except Exception as e:
        #print(f"AI Suite error: {e}")
        return None

def get_other_provider_response(client, prompt, data, question, database_content,script_content):
    """Generates a response using aisuite."""
    updated_question, formatted_prompt = format_prompt(prompt,data,question,database_content,script_content)
   
    try:
        #print("Get response")
        start_time = time.time()
        response = get_response(client, updated_question,formatted_prompt)
        end_time = time.time()
        response_time = end_time - start_time
        return response, response_time
    except Exception as e:
        #print(f"AI Suite error: {e}")
        #return None
        return "N/A", -1

def ensembling_process(client, updated_question, formatted_prompt, iterations):
    """
    Performs an ensembling process to generate multiple responses from an AI client.
    Uses a direct comparison approach to identify matching results.
    """
    dfs_and_responses = []
    counts = defaultdict(list)

    try:
        for i in range(iterations):
            response = client.ask(updated_question, formatted_prompt)
            extracted_code = extract_python_code(response)
            local_env = {"pydough": pydough, "datetime": datetime}
            result, exception = execute_code_and_extract_result(extracted_code, local_env)

            if result is not None:
                dfs_and_responses.append((result, response))
            #else:
            #    print(f"The PyDough code has the exception: {exception}")
        
        if dfs_and_responses == []:
            return response
        else: 
            for i in range(len(dfs_and_responses)):
                for j in range(i + 1, len(dfs_and_responses)):
                    df_gold = dfs_and_responses[i][0]
                    df_gen = dfs_and_responses[j][0]

                    if compare_df(
                        df_gold=df_gold,
                        df_gen=df_gen,
                        query_category="",
                        question=""
                    ):
                        counts[i].append(j)

            most_common_index = max(counts, key=lambda k: len(counts[k]), default=None)

            if most_common_index is not None:
                return dfs_and_responses[most_common_index][1]
            else:
            #    print("No common result found, returning the first response as fallback.")
                return dfs_and_responses[0][1] if dfs_and_responses else None

    except Exception as e:
        #print(f"AI Suite error: {e}")
        return None

def get_claude_response(client, prompt, data, question, database_content, script_content, num_iterations):
    """Generates a response using aisuite."""
    updated_question, formatted_prompt = format_prompt(prompt,data,question,database_content,script_content)
    start_time = time.time()
    response=ensembling_process(client, updated_question,formatted_prompt, num_iterations)
    end_time = time.time()
    execution_time = end_time - start_time
    return response, execution_time

output_type = bodo.typeof(("hello", 1.2))

@bodo.wrap_python(output_type)
def process_question_wrapper(provider, model_id, formatted_prompt, q, temperature, database_content, script_content, num_iterations):
    """ Wrapper function to handle API calls. """
    with open("data/queries_context.json", "r") as json_data:
        data = json.load(json_data)

    if provider == "azure":
        client = AzureAIProvider(model_id)
        return get_azure_response(client, formatted_prompt, data, q, database_content, script_content)[0]
    elif provider == "aws-thinking":
        client = ClaudeAIProvider(provider, model_id)
        return get_claude_response(client, formatted_prompt, data, q, database_content, script_content, num_iterations)[0]
    elif provider == "aws-deepseek":
        client = DeepSeekAIProvider(provider, model_id, temperature)
        return get_claude_response(client, formatted_prompt, data, q, database_content, script_content,num_iterations)[0]
    else:
        client = OtherAIProvider(provider, model_id, temperature)
        return get_other_provider_response(client, formatted_prompt, data, q, database_content, script_content)

 
@bodo.jit(cache=True)
def run(question, provider, model_id, formatted_prompt, temperature, database_content, script_content, num_iterations, output_file):
    """ Main function to process questions and get responses.
    Overall process:
    1. Run the question n times in parallel.
    2. Get response from the AI provider.
    3. Extract Python code from the response.
    4. Execute the code and get the dataframe result hash.
    4. Find the most common hash result.
    6. Get the corresponding response.
    """

    df_response = pd.DataFrame(columns=["hash", "response", 'extracted_code', "call_time", "exec_time"], index=range(num_iterations))
    t0 = time.time()
    for i in bodo.prange(num_iterations):
        # 1. Get response
        # columns: response #and call_time
        #print("process_question_wrapper")
        df_response.iloc[i, 1] = process_question_wrapper(
                provider, model_id, formatted_prompt, question, temperature, database_content, script_content, num_iterations)[0]
        # 2. Extract Python code, execute it, and get the dataframe result hash
        # column: extracted_code
        df_response.iloc[i, 2] = extract_python_code(df_response['response'].iloc[i])
        # column: hash
        df_response.iloc[i, 0] = execute_code_and_extract_result_hash_bodo(df_response.extracted_code.iloc[i])
    # 3. Find most common hash result
    most_common_ans = df_response["hash"].value_counts().idxmax()
    # 4. Get the corresponding response
    response = df_response[df_response["hash"] == most_common_ans]["response"].iloc[0]
    t1 = time.time()
    #df_response.to_csv(output_file, index=False)
    return df_response


def main():
    # Argument Parser
    parser = argparse.ArgumentParser(description="Process a script file and questions CSV.")
    parser.add_argument("--pydough_file", type=str, help="Path to the script file.")
    parser.add_argument("--database_structure", type=str, help="Path to the database file.")
    parser.add_argument("--prompt_file", type=str, help="Path to the prompt file.")
    parser.add_argument("--questions", type=str, help="Path to the questions CSV file.")
    parser.add_argument("--provider", type=str, help="Model provider (e.g., 'azure', 'claude').")
    parser.add_argument("--model_id", type=str, help="Model ID.")
    parser.add_argument("--temperature", type=float, help="Set the temperature for the model.")
    parser.add_argument("--num_threads", type=int, help="Number of threads for parallel processing.")
    parser.add_argument("--num_iterations", type=int, help="Number of iterations for ensembling.")

    args = parser.parse_args()

    # Create result directory if not exists
    folder_path = f"./results/bodo_eval/{args.provider}/{args.model_id}"
    os.makedirs(folder_path, exist_ok=True)
    output_file = f"{folder_path}/responses_{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.csv"

    # Read Files Efficiently
    with open(args.prompt_file, "r", encoding="utf-8") as f:
        prompt = f.read()

    with open(args.pydough_file, "r", encoding="utf-8") as f:
        script_content = f.read()

    with open(args.database_structure, "r", encoding="utf-8") as f:
        database_content = f.read()

    # FIXME: data type is not accepted by Bodo
    with open("data/queries_context.json", "r") as json_data:
        data = json.load(json_data)

    # Read Questions
    print("File: ", args.questions, "num_threads: ", args.num_threads, "num_iterations: ", args.num_iterations)
    with open(args.questions, "r", encoding="utf-8") as f:
        question = f.read()

    t0 = time.time()
    questions_df = run(question, args.provider.lower(), args.model_id, prompt, args.temperature, database_content, script_content, args.num_iterations, output_file)
    t1 = time.time()
    total_time = t1-t0
    print(f"[RESULT] mode=bodo threads={args.num_threads} iterations={args.num_iterations} time={total_time:.3f} output_file={output_file}")



    # FIXME: Why Bodo complained here? It's out of JIT function
    #questions_df.to_csv(output_file, index=False)#, encoding="utf-8")

if __name__ == "__main__":
    # import pdb; pdb.set_trace()

    db_path = './test_data/tpch.db'
    
    download_database(db_path)
    
    main()

