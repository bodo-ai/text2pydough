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

# === Claude, Deepseek, Gemini, AI Suite Providers ===


class ClaudeAIProviderAWS(AIProvider):
    def __init__(self, model_id, config=None):
        region = config.get("region", "us-east-1")
        profile = config.get("profile", "default")
        session = session(profile_name=profile)
        self.brt = session.client("bedrock-runtime", region_name=region)
        self.model_id = model_id

    def ask(self, question, prompt, **kwargs):
        max_tokens = kwargs.get("max_tokens", 20000)
        temperature = kwargs.get("temperature", 0.0)

        
        inference_config = {
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        body = {
            "modelId": self.model_id,
            "system": [{"type": "text", "text": prompt}],
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": question}]
                }
            ],
            "inferenceConfig": inference_config
        }

        
        response = self.brt.converse_stream(**body)

        
        full_output = ""
        for event in response["stream"]:
            chunk = event.get("chunk")
            if chunk:
                bytes_data = json.loads(chunk["bytes"].decode())
                if "delta" in bytes_data and "text" in bytes_data["delta"]:
                    full_output += bytes_data["delta"]["text"]

        return full_output, None


class ClaudeAIProvider(AIProvider):
    def __init__(self, model_id, config=None):
        try:
            self.api_key = os.environ["GOOGLE_API_KEY"]
            self.project = os.environ["GOOGLE_PROJECT_ID"]
            self.location = "us-east5"
            self.model_id = model_id
            self.client = AnthropicVertex(project_id=self.project, region=self.location)
        except KeyError as e:
            raise RuntimeError(f"Missing environment variable: {e}")

    @mlflow.trace
    def ask(self, prompt, system_instruction, **kwargs):
        try:
            kwargs.setdefault("max_tokens", 20000)
            use_streaming = kwargs.pop("use_stream", True)

            if use_streaming:
                # Streaming mode
                response_stream = self.client.messages.create(
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    model=self.model_id,
                    system=system_instruction,
                    stream=True,
                    **kwargs
                )

                full_output = ""
                for chunk in response_stream:
                    data = chunk.to_dict() if hasattr(chunk, "to_dict") else chunk

                    if data.get("type") == "content_block_delta":
                        delta = data.get("delta", {})
                        if delta.get("type") == "text_delta":
                            full_output += delta.get("text", "")
                            
                return full_output, None  # usage not available in streaming mode

            else:
                # Regular mode
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
                return response.content[0].text, response.usage

        except Exception as e:
            raise RuntimeError(f"[ClaudeAIProvider] Request failed: {e}")



class GeminiAIProvider(AIProvider):

    def __init__(self, model_id, config=None):
        try:
            self.api_key = os.environ["GOOGLE_API_KEY"]  
            self.project = os.environ["GOOGLE_PROJECT_ID"]
            self.location = os.environ["GOOGLE_REGION"]
            self.model_id = model_id
            self.client = genai.Client(project=self.project, location=self.location)    
        except KeyError:
            raise RuntimeError("Environment variable 'GOOGLE_API_KEY' is required but not set.")

    @mlflow.trace
    def ask(self, prompt, system_instruction, **kwargs):
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
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