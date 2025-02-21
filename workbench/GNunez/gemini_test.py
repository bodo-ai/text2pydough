import aisuite as ai
client = ai.Client()

model="google:gemini-1.5-pro-001"

messages = [
    {"role": "system", "content": "Respond in Pirate English."},
    {"role": "user", "content": "Tell me a joke."},
]

response = client.chat.completions.create(
    model=model,
    messages=messages,
)

print(response.choices[0].message.content)