# %%
import boto3
import json
import pandas as pd
from botocore.config import Config

class ClaudeModel:
    def __init__(self):
        # Initialize AWS SDK and load necessary files
        config = Config(read_timeout=800)
        self.brt = boto3.client(service_name='bedrock-runtime', config= config)

    def ask_claude_with_stream(self, question, prompt, model, provider):
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 20000,
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

# %%
import boto3
import json
import pandas as pd
from botocore.config import Config

class DeepseekModel:
    def __init__(self, temperature ):
        # Initialize AWS SDK and load necessary files
        self.temperature= temperature
        config = Config(read_timeout=500)
        self.brt = boto3.client(service_name='bedrock-runtime', config= config)

    def ask_claude_with_stream(self, question, prompt, model, provider):
        system_messages= [{"text": prompt}]
        messages= [
                {
                    "role": "user",  # Wrap "string" in quotes to make it a valid string
                    "content":[{"text": question}]
                }
            ]
        

        modelId = model
        

        response = self.brt.converse(modelId= modelId,inferenceConfig= {"maxTokens": 30000,"temperature":self.temperature}, system=system_messages, messages= messages)
        response_text = response["output"]["message"]["content"][0]["text"]
        reasoning_text= response["output"]["message"]["content"][1]["reasoningContent"]["reasoningText"]["text"]
        print(response.get('usage', {}))
        return response_text, reasoning_text

    def extract_thinking_and_text(self, response_body):
        thinking_content = response_body['content'][0].get('thinking', '')
        text_content = response_body['content'][1].get('text', '')
        return thinking_content, text_content

    def extract_usage(self, response_body):
        return response_body.get('usage', {})
# %%

import boto3
with open("/home/ara/tekdatum/ara-text2pydough/text2pydough/workbench/ARamirez/prompt_evaluation/data/prompts/prompt3.md", "r", encoding="utf-8") as f:
            prompt = f.read()

# Set values here
TARGET_MODEL_ID = "deepseek.r1-v1:0" # Model to optimize for. For model IDs, see https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html
PROMPT = prompt # Prompt to optimize

def get_input(prompt):
    return {
        "textPrompt": {
            "text": prompt
        }
    }
 
def handle_response_stream(response):
    try:
        event_stream = response['optimizedPrompt']
        for event in event_stream:
            if 'optimizedPromptEvent' in event:
                print("========================== OPTIMIZED PROMPT ======================\n")
                optimized_prompt = event['optimizedPromptEvent']
                print(optimized_prompt)
            else:
                print("========================= ANALYZE PROMPT =======================\n")
                analyze_prompt = event['analyzePromptEvent']
                print(analyze_prompt)
    except Exception as e:
        raise e
 
 
if __name__ == '__main__':
    client = boto3.client('bedrock-agent-runtime')
    try:
        response = client.optimize_prompt(
            input=get_input(PROMPT),
            targetModelId=TARGET_MODEL_ID
        )
        print("Request ID:", response.get("ResponseMetadata").get("RequestId"))
        print("========================== INPUT PROMPT ======================\n")
        print(PROMPT)
        handle_response_stream(response)
    except Exception as e:
        raise e
# %%
