import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import UserMessage, SystemMessage
from azure.core.credentials import AzureKeyCredential
from abc import ABC, abstractmethod
import boto3
import json
import pandas as pd
from botocore.config import Config
import google.genai as genai
from google.genai import types
import aisuite as ai
from mistralai import Mistral
import mlflow
from anthropic import AnthropicVertex

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

# === DeepSeek Provider ===
class DeepSeekAIProvider(AIProvider):
    def __init__(self, model_id):
        config = Config(read_timeout=500)
        self.brt = boto3.client(service_name='bedrock-runtime', config=config)
        self.model_id = model_id

    def ask(self, question, prompt, **kwargs):
        system_messages = [{"text": prompt}]
        messages = [{"role": "user", "content": [{"text": question}]}]
        response = self.brt.converse(
            modelId=self.model_id,
            inferenceConfig={"maxTokens": kwargs.get("max_tokens", 30000), **kwargs},
            system=system_messages,
            messages=messages
        )
        return response["output"]["message"]["content"][0]["text"]

# === Gemini & Claude Provider ===
class GeminiAIProvider(AIProvider):
    def __init__(self, model_id, api_key=None, project=None, region=None):
        try:
            self.model_id = model_id
            self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
            self.project = project or os.getenv("GOOGLE_PROJECT_ID")
            self.location = region or os.getenv("GOOGLE_REGION")
            if "claude" in model_id:
                self.location = "us-east5"
                self.client = AnthropicVertex(project_id=self.project, region=self.location)
                self.is_claude = True
            else:
                self.client = genai.Client(project=self.project, location=self.location)
                self.is_claude = False
        except KeyError:
            raise RuntimeError("Missing Google Gemini credentials (GOOGLE_API_KEY, etc).")

    @mlflow.trace
    def ask(self, prompt, system_instruction, **kwargs):
        if "claude" in self.model_id:
            max_tokens = kwargs.pop("max_tokens", 20000)
            response = self.client.messages.create(
                messages=[
           
                {
                    "role": "user",
                    "content": prompt,
                }
                ],
                model=self.model_id,
                system=system_instruction,
                **kwargs
            )
            
            text_message = response.content[0].text
            usage = response.usage 
            return text_message, usage
        else:    
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    **kwargs
                ),
            
            )
            return response.text, response.usage_metadata

# === AI Suite Provider ===
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

# === Mistral Provider ===
class MistralAIProvider(AIProvider):
    def __init__(self, model_id):
        self.api_key = os.environ["MISTRAL_API_KEY"]
        self.model_id = model_id
        self.client = Mistral(api_key=self.api_key)

    def ask(self, question, prompt, **kwargs):
        messages = [{"role": "system", "content": prompt}, {"role": "user", "content": question}]
        try:
            response = self.client.chat.complete(
                model=self.model_id,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Mistral error: {e}")
            return None

