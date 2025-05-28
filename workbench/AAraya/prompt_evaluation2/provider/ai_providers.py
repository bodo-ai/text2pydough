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
        self.model_id = model_id
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.project = project or os.getenv("GOOGLE_PROJECT_ID")
        self.region = region or os.getenv("GOOGLE_REGION")

        if not self.api_key or not self.project:
            raise RuntimeError("Missing Gemini/Claude credentials.")

        if "claude" in self.model_id:
            self.region = self.region or "us-east5"
            self.client = AnthropicVertex(project_id=self.project, region=self.region)
            self.is_claude = True
        else:
            self.region = self.region or "us-central1"
            self.client = genai.Client(project=self.project, location=self.region)
            self.is_claude = False

    @mlflow.trace
    def ask(self, question, prompt, **kwargs):
        if self.is_claude:
            # Claude acepta max_tokens directamente
            response = self.client.messages.create(
                messages=[{"role": "user", "content": question}],
                model=self.model_id,
                system=prompt,
                **kwargs
            )
            return response.content[0].text, response.usage
        else:
            # Gemini requiere mapping a generation_config y NO acepta max_tokens
            generation_config = types.GenerationConfig(
                temperature=kwargs.get("temperature", 1.0),
                top_p=kwargs.get("top_p", 1.0),
                top_k=kwargs.get("top_k", 1),
                max_output_tokens=kwargs.get("max_tokens", 2048),  # mapping correcto
            )

            response = self.client.models.generate_content(
                model=self.model_id,
                contents=question,
                generation_config=generation_config,
                system_instruction=prompt
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

