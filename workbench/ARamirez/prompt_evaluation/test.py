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
formatted_prompt = prompt.format(script_content=script_content, database_content=database_content, similar_queries=similar_code)

def ask_claude(prompt, question):
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens":18000 ,   
        "thinking": {
        "type": "enabled",
        "budget_tokens": 6000
    },
        "system": prompt,  # Wrap "string" in quotes to make it a valid string
        "messages": [
            {
                "role": "user",  # Wrap "string" in quotes to make it a valid string
                "content": question
            }
        ],
        "temperature": 1,
    })

    modelId = 'us.anthropic.claude-3-7-sonnet-20250219-v1:0'
    accept = 'application/json'
    contentType = 'application/json'

    response = brt.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)

    response_body = json.loads(response.get('body').read())
    return response_body
# %%
# Loop through all questions in the 'similar_queries' column
for question in similar_code[2]:
    # Ask the model for each question
    response_body = ask_claude(formatted_prompt, question)
    
    # Print the model's response
    print(f"Question: {question}")
    print(f"Response: {response_body}")
    print("-" * 50)

# %%
question="Retrieves the top 3 suppliers with the highest total sales for each region"
response_body = ask_claude(formatted_prompt, question)

# %%    
    # Print the model's response
print(f"Question: {question}")
print(f"Response: {response_body}")
# %%
# Extracting the response content
thinking_content = response_body['content'][0].get('thinking', '')
text_content = response_body['content'][1].get('text', '')

# %%
print(thinking_content)
# %%
usage = response_body.get('usage', {})

# %%
def ask_claude(prompt, question):
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens":18000 ,   
        "thinking": {
        "type": "enabled",
        "budget_tokens": 5000
    },
        "system": prompt,  # Wrap "string" in quotes to make it a valid string
        "messages": [
            {
                "role": "user",  # Wrap "string" in quotes to make it a valid string
                "content": question
            }
        ],
        "temperature": 1,
    })

    modelId = 'us.anthropic.claude-3-7-sonnet-20250219-v1:0'
    accept = 'application/json'
    contentType = 'application/json'

    response = brt.invoke_model_with_response_stream(body=body, modelId=modelId, accept=accept, contentType=contentType)

    stream = response.get('body')
    if stream:
        for event in stream:
            chunk = event.get('chunk')
            if chunk:
                print(json.loads(chunk.get('bytes').decode()))