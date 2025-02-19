import os
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.inference.models import SystemMessage, UserMessage

client = ChatCompletionsClient(
    endpoint="https://ai-arnoldo2137ai929428123129.services.ai.azure.com/models",
    credential=AzureKeyCredential("CLQAXkuwkcBxwpVB0fuL9KmIMGP3GLhTBZcAGezHh6CRZhfqq9fPJQQJ99BBACHYHv6XJ3w3AAAAACOGSJD4"),
)

response = client.complete(
    messages=[
        SystemMessage(content="You are a helpful assistant."),
        UserMessage(content="Give me a nutritional plan for grow muscles"),
    ],
    model="DeepSeek-R1"
)

print(response.choices[0].message.content)