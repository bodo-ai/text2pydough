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
questions_df = pd.read_csv(args.questions_csv, encoding="utf-8")
similar_code = questions_df["similar_queries"].tolist()

def ask_claude(prompt, question):
    body = json.dumps({
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

    modelId = 'anthropic.claude-3-7-sonnet-20250219-v1:0'
    accept = 'application/json'
    contentType = 'application/json'

    response = brt.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)

    response_body = json.loads(response.get('body').read())

# text
print(response_body.get('completion'))