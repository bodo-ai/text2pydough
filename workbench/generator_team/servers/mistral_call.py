import os
import aisuite as ai
from dotenv import load_dotenv
load_dotenv()

api_key = os.environ["MISTRAL_API_KEY"]
model = "codestral-2501"

client = ai.Client()

chat_response = client.chat.completions.create(
    model=f"mistral:{model}",
    messages=[
        {
            "role": "user",
            "content": "What is the best French cheese?",
        },
    ],
    temperature=0.7,
)
print(chat_response.choices[0].message.content)