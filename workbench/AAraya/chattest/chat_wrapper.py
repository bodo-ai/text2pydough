import os
from google import genai
from google.genai import types

class GeminiChatWrapper:
    def __init__(self, script, database, prompt, definitions=None, model_name="", temperature=0.2):
        # Make sure the API key is set
        self.api_key = os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise RuntimeError("Environment variable 'GOOGLE_API_KEY' is required but not set.")
        
        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(model_name)

        self.temperature = temperature
        self.script = script
        self.database = database
        self.prompt_template = prompt
        self.definitions = definitions or []

        self.history = []
        self.chat_session = self.client.start_chat(
            generation_config=types.GenerationConfig(
                temperature=self.temperature,
                top_p=1.0,
                top_k=1
            ),
            system_instruction=self.prompt_template
        )

    def ask(self, user_question):
        response = self.chat_session.send_message(user_question)
        self.history.append((user_question, response.text))
        return response.text

    def restart(self):
        self.chat_session = self.client.start_chat(
            generation_config=types.GenerationConfig(
                temperature=self.temperature,
                top_p=1.0,
                top_k=1
            ),
            system_instruction=self.prompt_template
        )
        self.history = []

    def get_chat_history(self):
        return self.history
