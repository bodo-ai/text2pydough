import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import UserMessage, SystemMessage
from azure.core.credentials import AzureKeyCredential
from abc import ABC, abstractmethod
import os
import boto3
import json
import pandas as pd
from botocore.config import Config
import google.genai as genai
from google.genai import types
import aisuite as ai
from mistralai import Mistral

# === Abstract Class for AI Providers ===
class AIProvider(ABC):
    @abstractmethod
    def ask(self, question, prompt, **kwargs):
        pass

# === Azure Provider ===
class AzureAIProvider(AIProvider):
    def __init__(self, model_id):
        self.client = self.setup_azure_client()
        self.model_id = model_id

    def setup_azure_client(self):
        endpoint = os.getenv("AZURE_BASE_URL")
        key = os.getenv("AZURE_API_KEY")
        if not endpoint or not key:
            raise ValueError("Azure environment variables are not set.")
        return ChatCompletionsClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    def ask(self, question, prompt, **kwargs):
        messages = [SystemMessage(prompt), UserMessage(question)]
        try:
            completion = self.client.complete(messages=messages, max_tokens=kwargs.get("max_tokens", 20000),
                                              model=self.model_id, stream=True)
            return "".join([chunk.choices[0]["delta"]["content"] for chunk in completion if chunk.choices])
        except Exception as e:
            print(f"Azure error: {e}")
            return None

# === Claude, Deepseek, Gemini, AI Suite Providers ===
class ClaudeAIProvider(AIProvider):
    def __init__(self, model_id):
        config = Config(read_timeout=800)
        self.brt = boto3.client(service_name='bedrock-runtime', config=config)
        self.model_id = model_id

    def ask(self, question, prompt, **kwargs):
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

        modelId = self.model_id
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

class DeepSeekAIProvider(AIProvider):
    def __init__(self, model_id):
        config = Config(read_timeout=500)
        self.brt = boto3.client(service_name='bedrock-runtime', config=config)
        self.model_id = model_id

    def ask(self, question, prompt, **kwargs):
        system_messages = [{"text": prompt}]
        messages = [
            {
                "role": "user",  
                "content": [{"text": question}]
            }
        ]

        modelId = self.model_id

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
        return response_text

class GeminiAIProvider(AIProvider):

    def __init__(self, model_id):
        try:
            self.api_key = os.environ["GOOGLE_API_KEY"]  
            self.project = os.environ["GOOGLE_PROJECT_ID"]
            self.location = os.environ["GOOGLE_REGION"]
            self.model_id = model_id
        except KeyError:
            raise RuntimeError("Environment variable 'GOOGLE_API_KEY' is required but not set.")
        self.client = genai.Client(vertexai= True,  project=self.project, location=self.location)
    
    def ask(self, question, prompt, **kwargs):
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=question,
            config=types.GenerateContentConfig(
                system_instruction=prompt,
                **kwargs
            ),
        
        )
        return response.text, response.usage_metadata
    
    def chat(self, question, prompt, chat=None, **kwargs):
        if not chat:
            chat = self.client.chats.create(model=self.model_id)
        response = chat.send_message(
            question,        
            config=types.GenerateContentConfig(
                system_instruction=prompt,
                **kwargs
            )
        )
        return response, chat

class OtherAIProvider(AIProvider):
    def __init__(self, provider, model_id, config=None):
        self.client = ai.Client(config) if config else ai.Client()
        self.provider = provider
        self.model_id = model_id
    
    def ask(self, question, prompt, **kwargs):
        messages = [{"role": "system", "content": prompt}, {"role": "user", "content": question}]
        try:
            response = self.client.chat.completions.create(
                model=f"{self.provider}:{self.model_id}",
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"AI Suite error: {e}")
            return None

class MistralAIProvider(AIProvider):
    def __init__(self, model_id):
        self.api_key = os.environ["MISTRAL_API_KEY"]  
        self.model_id = model_id
        self.client= Mistral(api_key=self.api_key)
    
    def ask(self, question, prompt, **kwargs):
        messages = [{"role": "system", "content": prompt}, {"role": "user", "content": question}]
        try:
            response = self.client.chat.complete(
                model=f"{self.model_id}",
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"AI Suite error: {e}")
            return None
