# %%
import os
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
        thinking_delta= []
        stream = response.get('body')
        if stream:
            for event in stream:
                chunk = event.get('chunk')
                if chunk:
                    bytes_data = json.loads(chunk.get('bytes').decode())
                    if 'delta' in bytes_data:
                        delta = bytes_data['delta']
                        text_delta.append(delta.get('text', ''))
                        thinking_delta.append(delta.get('thinking', ''))
        #print(f"New sentence {''.join(thinking_delta)}")
        return ''.join(text_delta)

    def extract_thinking_and_text(self, response_body):
        thinking_content = response_body['content'][0].get('thinking', '')
        text_content = response_body['content'][1].get('text', '')
        return thinking_content, text_content

    def extract_usage(self, response_body):
        return response_body.get('usage', {})
# %%
from google import genai
from google.genai import types

class GeminiModel:
    def __init__(self, temperature):
        try:
            self.api_key = os.environ["GOOGLE_API_KEY"]  
        except KeyError:
            raise RuntimeError("Environment variable 'GOOGLE_API_KEY' is required but not set.")
        self.brt =  genai.Client(api_key="AIzaSyCIJ8R71urQshcnFNFUXOAuD0bs14yGIe0")
        self.temperature= temperature

    def generate_content(self, question, prompt, model, provider):
        response = self.brt.models.generate_content(
        model=model,
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction=prompt,
            temperature=self.temperature,
        ),
    )
        return response

    def chat(self, question, prompt, model, provider, chat= None):
        if not chat:
            chat = self.brt.chats.create(model=model)
        response = chat.send_message(
            question,        
            config=types.GenerateContentConfig(
            system_instruction=prompt,
            temperature=self.temperature,
        ))
        return response, chat
    
    def extract_usage(self, response_body):
        return response_body.get('usage', {})
    
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
       # reasoning_text= response["output"]["message"]["content"][1]["reasoningContent"]["reasoningText"]["text"]
        print(response.get('usage', {}))
        return response_text

    def extract_thinking_and_text(self, response_body):
        thinking_content = response_body['content'][0].get('thinking', '')
        text_content = response_body['content'][1].get('text', '')
        return thinking_content, text_content

    def extract_usage(self, response_body):
        return response_body.get('usage', {})

