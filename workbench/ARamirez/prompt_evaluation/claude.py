# %%
import boto3
import json
import pandas as pd

class ClaudeModel:
    def __init__(self):
        # Initialize AWS SDK and load necessary files
        self.brt = boto3.client(service_name='bedrock-runtime')

    def ask_claude_with_stream(self, question, prompt, model, provider):
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 20000,
            "thinking": {
                "type": "enabled",
                "budget_tokens": 6500
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

        modelId = model
        accept = 'application/json'
        contentType = 'application/json'

        response = self.brt.invoke_model_with_response_stream(body=body, modelId=modelId, accept=accept, contentType=contentType)
        text_delta = []
        stream = response.get('body')
        if stream:
            for event in stream:
                chunk = event.get('chunk')
                if chunk:
                    bytes_data = json.loads(chunk.get('bytes').decode())
                    if 'delta' in bytes_data:
                        delta = bytes_data['delta']
                        text_delta.append(delta.get('text', ''))

        return ''.join(text_delta)

    def extract_thinking_and_text(self, response_body):
        thinking_content = response_body['content'][0].get('thinking', '')
        text_content = response_body['content'][1].get('text', '')
        return thinking_content, text_content

    def extract_usage(self, response_body):
        return response_body.get('usage', {})
# %%
