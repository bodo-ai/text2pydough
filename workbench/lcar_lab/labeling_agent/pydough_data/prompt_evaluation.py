import argparse
import ast
import json
import multiprocessing
import os
import re
import pandas as pd
import aisuite as ai
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import UserMessage, SystemMessage
from azure.core.credentials import AzureKeyCredential
import mlflow
from test_data.eval import compare_output, execute_code_and_extract_result
from utils import autocommit, get_git_commit, modified_files, untracked_files, download_database
from claude import ClaudeModel, DeepseekModel
import pydough
from abc import ABC, abstractmethod
from google import genai
from google.genai.types import GenerateContentConfig, HttpOptions

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
            print(f"Azure AI error: {e}")
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
                temperature=self.temperature,
                topP=0,
                topK=0
            
            )
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"AI Suite error: {e}")
            return None, None 

# === Other AI Providers (e.g., AI Suite) ===
class GeminiAIProvider(AIProvider):
    """Handles responses from other AI providers like AI Suite."""

    def __init__(self, provider, model_id, temperature, config= None):
        #self.client = ai.Client(config) if config else ai.Client()
        #self.client = genai.Client(
            #vertexai=True,
            #project="solid-drive-448717-p8",
            #location="us-central1",
            #http_options=types.HttpOptions(api_version='v1')
        #)
        self.client = genai.Client(api_key="AIzaSyCIJ8R71urQshcnFNFUXOAuD0bs14yGIe0")#"AIzaSyB9i0FbDZzqy2Q3y4aolDP0EBXZOoTR7LY")
        self.provider = provider
        self.model_id = model_id
        self.temperature= temperature
        # uplad file
        print("Uploading repo file...")
        self.pydough_repo_file = self.client.files.upload(file="/home/dfinolbe/bodo/data/repomix-output-tree-main_xml.txt")
        print("Done with repo upload to Gemini..")


    def ask(self, question, prompt):
        """Generates a response using AI Suite."""
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"{question}"},
        ]

        try:
            time.sleep(0.5)  # Simulate slight delay
            #print(prompt)
            #with open("sample_prompt.txt", 'a', encoding='utf-8') as file:
                #file.write(prompt)
            #print(question)
            #with open("sample_question.txt", 'a', encoding='utf-8') as file:
                #file.write(question)
            #quit()
            # Define system instructions 
            system_instructions = [prompt]
            
            # Create a reusable configuration
            config = GenerateContentConfig(system_instruction=system_instructions)

            response= self.client.models.generate_content(
                model=self.model_id,#"gemini-2.0-flash",
                contents=[self.pydough_repo_file, "\n\n", question],
                config = config,
            )
            
            print("\nRSPONSE:\n")
            print(self.model_id)
            print(response.candidates[0].content.parts[0].text)#.content.parts[0].text)
            return response.candidates[0].content.parts[0].text#.choices[0].message.content
            
        except Exception as e:
            #quit()
            print(f"AI Suite error: {e}")
            return None, None 

def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

def extract_python_code(text):
    """Extracts Python code from triple backticks in text."""
    if not isinstance(text, str):  # Ensure text is a string
        return ""

    matches = re.findall(r"```(?:\w*\n)?(.*?)\n```", text, re.DOTALL)
    return matches[-1].strip() if matches else ""

import os

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
        print(f"Azure AI error: {e}")
        return None

def get_other_provider_response(client, prompt, data, question, database_content,script_content):
    """Generates a response using aisuite."""
    updated_question, formatted_prompt = format_prompt(prompt,data,question,database_content,script_content)
   
    try:
        start_time = time.time()
        response=client.ask(updated_question,formatted_prompt)
        end_time = time.time()
        execution_time = end_time - start_time
        corrected_response= correct(client, updated_question, response,formatted_prompt)
        return corrected_response, execution_time
    except Exception as e:
        print(f"AI Suite error: {e}")
        return None

def get_claude_response(client, prompt, data, question, database_content, script_content):
    """Generates a response using aisuite."""
    updated_question, formatted_prompt = format_prompt(prompt,data,question,database_content,script_content)
    start_time = time.time()
    response=client.ask(updated_question,formatted_prompt)
    end_time = time.time()
    execution_time = end_time - start_time
    corrected_response = correct(client, updated_question, response,formatted_prompt)
    return corrected_response, execution_time

def process_question_wrapper(args):
    """ Wrapper function to handle multiprocessing calls. """
    provider, model_id, formatted_prompt, data, q, temperature, database_content, script_content, client = args
    #provider, model_id, formatted_prompt, data, q, temperature, database_content, script_content = args

    if provider == "azure":
        client = AzureAIProvider(model_id)
        return get_azure_response(client, formatted_prompt, data, q, database_content, script_content)
    elif provider == "aws-thinking":
        client = ClaudeAIProvider(provider, model_id)
        return get_claude_response(client, formatted_prompt, data, q, database_content, script_content)
    elif provider == "aws-deepseek":
        client = DeepSeekAIProvider(provider, model_id, temperature)
        return get_claude_response(client, formatted_prompt, data, q, database_content, script_content)
    elif provider=="google":
        #client = GeminiAIProvider(provider, model_id, temperature)
        return get_other_provider_response(client, formatted_prompt, data, q, database_content, script_content)
    else:
        provider= "google"
        client = OtherAIProvider(provider, model_id, temperature)
        return get_other_provider_response(client, formatted_prompt, data, q, database_content, script_content)

def process_questions(data, provider, model_id, formatted_prompt, questions, temperature, database_content, script_content, num_threads):
    """ Processes questions in parallel using multiprocessing. """
    
    if provider=="google_multiprocessing":
        #multi-processing consider using batching function for google method. 
        with multiprocessing.Pool(processes=num_threads) as pool:  # Adjust process count as needed
            original_responses = pool.map(
                process_question_wrapper, 
                [(provider, model_id, formatted_prompt, data, q, temperature, database_content, script_content) for q in questions]
            )

    # single threaded processing 
    else:
        client = GeminiAIProvider(provider, model_id, temperature)
        original_responses = [process_question_wrapper([provider, model_id, formatted_prompt, data, q, temperature, database_content, script_content, client]) for q in questions]
    
    return original_responses

def main(git_hash):
    # Argument Parser
    parser = argparse.ArgumentParser(description="Process a script file and questions CSV.")
    parser.add_argument("--description", type=str, default="MLFlow")
    parser.add_argument("--name", type=str, default="MLFlow project")
    parser.add_argument("--pydough_file", type=str, help="Path to the script file.")
    parser.add_argument("--database_structure", type=str, help="Path to the database file.")
    parser.add_argument("--prompt_file", type=str, help="Path to the prompt file.")
    parser.add_argument("--questions", type=str, help="Path to the questions CSV file.")
    parser.add_argument("--provider", type=str, help="Model provider (either 'azure' or another provider).")
    parser.add_argument("--model_id", type=str, help="Model ID.")
    parser.add_argument("--temperature", type=float, help="Set the temperature to the model")
    parser.add_argument("--num_threads", type=int, help="Set the numbers of threads to the model")

    parser.set_defaults(eval_results=False)
    args = parser.parse_args()
    
    # Create result directory if not exists
    folder_path = f"./results/{args.provider}/{args.model_id}"
    os.makedirs(folder_path, exist_ok=True)
    
    mlflow.set_tracking_uri("http://127.0.0.1:5001") # 5000 for remote
    expr_name = "text2pydough"  # create a new experiment (do not replace)
    experiment= mlflow.set_experiment(expr_name)
    with mlflow.start_run(description=args.description, run_name=args.name, tags={"GIT_COMMIT": git_hash},experiment_id=experiment.experiment_id):
        # Read Files Efficiently
        with open(args.prompt_file, "r", encoding="utf-8") as f:
            prompt = f.read()

        with open(args.pydough_file, "r", encoding="utf-8") as f:
            script_content = f.read()

        with open(args.database_structure, "r", encoding="utf-8") as f:
            database_content = f.read()

        with open("./queries_context.json","r") as json_data:
            data = json.load(json_data)

        # Read Questions
        questions_df = pd.read_csv(args.questions, encoding="utf-8")

        combined_list = questions_df['question'].tolist()

        responses = process_questions(data,args.provider.lower(), args.model_id, prompt, combined_list, args.temperature,database_content,script_content, args.num_threads)

        response_column = [response[0] for response in responses]  # Extract corrected responses
        execution_time_column = [response[1] for response in responses]  # Extract execution times

        # Save responses and execution times into the DataFrame
        questions_df["response"] = response_column
        questions_df["execution_time"] = execution_time_column

        output_file = f"{folder_path}/responses_{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.csv"
        questions_df["extracted_python_code"] = questions_df["response"].apply(extract_python_code)

        questions_df.to_csv(output_file, index=False, encoding="utf-8")

        folder_path = f"./results/{args.provider}/{args.model_id}/test"
        os.makedirs(folder_path, exist_ok=True)

        output_file, responses= compare_output(folder_path,output_file, "./test_data/tpch.db")
        total_rows = len(responses)

        counts = responses['comparison_result'].dropna().value_counts()
        percentages = counts / total_rows

        mlflow.log_metrics(
            percentages,
        )
        mlflow.log_metric("total_script_queries", total_rows)
        mlflow.log_artifact(output_file)

        mlflow.log_params(
            {
                "pydough_file": args.pydough_file,
                "database_structure": args.database_structure,
                "prompt_file": args.prompt_file,
                "prompt": prompt,
                "questions_file": args.questions,
                "provider": args.provider,
                "model_id": args.model_id,
                "temperature": args.temperature
            }
        )
       
        mlflow.set_tag("llm_output", output_file)
        mlflow.set_tag("csv" ,responses) 
        mlflow.log_artifact(output_file)
    

if __name__ == "__main__":

    cwd = os.getcwd()
     # Define the database path
    db_path = './test_data/tpch.db'

    # Download the database if it's not already present
    download_database(db_path)
    untracked= untracked_files(cwd)
    modified= modified_files(cwd)
    
    if untracked or modified:
        autocommit(cwd)

    git_hash= get_git_commit(cwd)
    
    main(git_hash)