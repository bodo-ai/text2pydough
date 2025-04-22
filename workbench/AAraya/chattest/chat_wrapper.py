from vertexai.language_models import ChatModel, InputOutputTextPair

class GeminiChatWrapper:
    def __init__(self, script, database, prompt, definitions=None, model_name="gemini-2.0-flash-001"):
        self.model = ChatModel.from_pretrained(model_name)
        self.script = script
        self.database = database
        self.prompt_template = prompt
        self.definitions = definitions or []
        self.history = []

        self.chat = self.model.start_chat(
            context=self.format_prompt(),  
            examples=[],
            temperature=0.0
        )

    def format_prompt(self):
        return self.prompt_template.format(
            script_content=self.script,
            database_content=self.database,
            similar_queries="",
            definitions="\n".join(self.definitions),
            recomendation=""
        )

    def ask(self, user_question):
        response = self.chat.send_message(user_question)
        self.history.append((user_question, response.text))
        return response.text

    def restart(self):
        self.chat = self.model.start_chat(
            context=self.format_prompt(),
            examples=[],
            temperature=0.0
        )
        self.history = []

