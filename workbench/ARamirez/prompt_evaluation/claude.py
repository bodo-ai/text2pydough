# claude.py
import os
import boto3
import json
import pandas as pd
from botocore.config import Config

class ClaudeModel:
    def __init__(self):
        # Initialize AWS SDK and load necessary files
        config = Config(read_timeout=800)
        self.brt = boto3.client(service_name='bedrock-runtime', config=config)

    def ask_claude_with_stream(self, question, prompt, model, provider, **kwargs):
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": kwargs.get("max_tokens", 20000),
            "thinking": {
                "type": "enabled",
                "budget_tokens": kwargs.get("budget_tokens", 5000)
            },
            "system": prompt,
            "messages": [
                {
                    "role": "user",
                    "content": question
                }
            ],
            "temperature": kwargs.get("temperature", 1),
        })

        modelId = model
        accept = 'application/json'
        contentType = 'application/json'

        response = self.brt.invoke_model_with_response_stream(
            body=body, 
            modelId=modelId, 
            accept=accept, 
            contentType=contentType
        )
        
        text_delta = []
        thinking_delta = []
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
        return ''.join(text_delta)

    def extract_thinking_and_text(self, response_body):
        thinking_content = response_body['content'][0].get('thinking', '')
        text_content = response_body['content'][1].get('text', '')
        return thinking_content, text_content

    def extract_usage(self, response_body):
        return response_body.get('usage', {})

# gemini.py
from google import genai
from google.genai import types

class GeminiModel:
    def __init__(self):
        try:
            self.api_key = os.environ["GOOGLE_API_KEY"]  
            self.project = os.environ["GOOGLE_PROJECT_ID"]
            self.location = os.environ["GOOGLE_REGION"]
        except KeyError:
            raise RuntimeError("Environment variable 'GOOGLE_API_KEY' is required but not set.")
        self.brt = genai.Client(vertexai=True, project=self.project, location=self.location)

    def generate_content(self, question, prompt, model, provider, **kwargs):
        print(kwargs)
        response = self.brt.models.generate_content(
            model=model,
            contents=question,
            config=types.GenerateContentConfig(
                system_instruction=prompt,
                **kwargs
            ),
        )
        return response

    def chat(self, question, prompt, model, provider, chat=None, **kwargs):
        if not chat:
            chat = self.brt.chats.create(model=model)
        response = chat.send_message(
            question,        
            config=types.GenerateContentConfig(
                system_instruction=prompt,
                **kwargs
            )
        )
        return response, chat
    
    def extract_usage(self, response_body):
        return response_body.get('usage', {})

# deepseek.py
import boto3
import json
from botocore.config import Config

class DeepseekModel:
    def __init__(self):
        
        config = Config(read_timeout=500)
        self.brt = boto3.client(service_name='bedrock-runtime', config=config)

    def ask_claude_with_stream(self, question, prompt, model, provider, **kwargs):
        system_messages = [{"text": prompt}]
        messages = [
            {
                "role": "user",  
                "content": [{"text": question}]
            }
        ]

        modelId = model

        response = self.brt.converse(
            modelId=modelId,
            inferenceConfig={
                "maxTokens": kwargs.get("max_tokens", 30000),
                **kwargs
            },
            system=system_messages,
            messages=messages
        )
        response_text = response["output"]["message"]["content"][0]["text"]
        print(response.get('usage', {}))
        return response_text

    def extract_thinking_and_text(self, response_body):
        thinking_content = response_body['content'][0].get('thinking', '')
        text_content = response_body['content'][1].get('text', '')
        return thinking_content, text_content

    def extract_usage(self, response_body):
        return response_body.get('usage', {})
