# %%
import boto3
import json

import pandas as pd
brt = boto3.client(service_name='bedrock-runtime')
with open("./prompt3.md", "r", encoding="utf-8") as f:
            prompt = f.read()

with open("./cheatsheet_v4_examples.md", "r", encoding="utf-8") as f:
            script_content = f.read()

with open("./tcph_graph.md", "r", encoding="utf-8") as f:
            database_content = f.read()

        # Read Questions
questions_df = pd.read_csv("./questions.csv", encoding="utf-8")
similar_code = questions_df["question"].tolist()

def ask_claude(prompt, question):
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens":10000 ,   
        "thinking": {
        "type": "enabled",
        "budget_tokens": 4000
    },
        "system": prompt,  # Wrap "string" in quotes to make it a valid string
        "messages": [
            {
                "role": "user",  # Wrap "string" in quotes to make it a valid string
                "content": question
            }
        ],
        "temperature": 0.0,
    })

    modelId = 'us.anthropic.claude-3-7-sonnet-20250219-v1:0'
    accept = 'application/json'
    contentType = 'application/json'

    response = brt.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)

    response_body = json.loads(response.get('body').read())
    return response_body

# Loop through all questions in the 'similar_queries' column
for question in similar_code[:3]:
    # Ask the model for each question
    response_body = ask_claude(prompt, question)
    
    # Print the model's response
    print(f"Question: {question}")
    print(f"Response: {response_body.get('completion')}")
    print("-" * 50)
