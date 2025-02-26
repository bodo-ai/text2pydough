import os
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.inference.models import SystemMessage, UserMessage

client = ChatCompletionsClient(
    endpoint=os.getenv("AZURE_BASE_URL"),
    credential=AzureKeyCredential(os.getenv("AZURE_API_KEY")),
)

response = client.complete(
    messages=[
        SystemMessage(content="You are a helpful assistant."),
        UserMessage(content="Give me a nutritional plan for grow muscles"),
    ],
    model="DeepSeek-R1"
)

print(response.choices[0].message.content)