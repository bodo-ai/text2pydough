import argparse
import os
import time
import pandas as pd
import aisuite as ai
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import UserMessage, SystemMessage
from azure.core.credentials import AzureKeyCredential

def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

def setup_azure_client():
    """Initializes and returns the Azure ChatCompletionsClient."""
    endpoint = os.getenv("AZURE_OPENAI_BASE_URL")
    token = os.getenv("GITHUB_TOKEN")

    if not endpoint or not token:
        raise ValueError("Azure environment variables are not set correctly.")

    return ChatCompletionsClient(endpoint=endpoint, credential=AzureKeyCredential(token))

def get_azure_response(client, prompt, question, model_id):
    """Generates a response using Azure AI."""
    messages = [SystemMessage(prompt), UserMessage(question)]
    
    try:
        response = client.complete(messages=messages, max_tokens=1000, model=model_id)
        return response.choices[0].message.content
    except Exception as e:
        print(f"Azure AI error: {e}")
        return None

def get_other_provider_response(client, provider, model_id, prompt, question):
    """Generates a response using aisuite."""
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": question},
    ]
    
    try:
        response = client.chat.completions.create(
            model=f"{provider}:{model_id}",
            messages=messages,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"AI Suite error: {e}")
        return None

def process_questions(provider, model_id, formatted_prompt, questions):
    responses = []
    
    if provider == "azure":
        client = setup_azure_client()
        get_response = lambda q: get_azure_response(client, formatted_prompt, q, model_id)
    else:
        client = ai.Client()
        get_response = lambda q: get_other_provider_response(client, provider, model_id, formatted_prompt, q)
    
    with ThreadPoolExecutor() as executor:
        responses = list(executor.map(get_response, questions))

    return responses

def main():
    # Argument Parser
    parser = argparse.ArgumentParser(description="Process a script file and questions CSV.")
    parser.add_argument("script_file", type=str, help="Path to the script file.")
    parser.add_argument("database_structure", type=str, help="Path to the database file.")
    parser.add_argument("prompt_file", type=str, help="Path to the prompt file.")
    parser.add_argument("questions_csv", type=str, help="Path to the questions CSV file.")
    parser.add_argument("provider", type=str, help="Model provider (either 'azure' or another provider).")
    parser.add_argument("model_id", type=str, help="Model ID.")

    args = parser.parse_args()

    # Create result directory if not exists
    folder_path = f"./results/{args.provider}/{args.model_id}"
    os.makedirs(folder_path, exist_ok=True)

    # Read Files Efficiently
    with open(args.prompt_file, "r", encoding="utf-8") as f:
        prompt = f.read()

    with open(args.script_file, "r", encoding="utf-8") as f:
        script_content = f.read()

    with open(args.database_structure, "r", encoding="utf-8") as f:
        database_content = f.read()

    # Read Questions
    questions_df = pd.read_csv(args.questions_csv, encoding="utf-8")
    questions = questions_df["question"].tolist()

    # Format prompt once
    formatted_prompt = prompt.format(script_content=script_content, database_content=database_content)


    # Process questions
    responses = process_questions(args.provider.lower(), args.model_id, formatted_prompt, questions_df["question"].tolist())

    # Save responses
    questions_df["response"] = responses
    output_file = f"{folder_path}/responses_{datetime.now().strftime('%Y_%m_%d-%I_%M_%S_%p')}.csv"
    questions_df.to_csv(output_file, index=False, encoding="utf-8")

    print(f"Responses saved to {output_file}")

if __name__ == "__main__":
    main()
