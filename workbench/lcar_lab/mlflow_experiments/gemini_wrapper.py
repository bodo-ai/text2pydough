# gemini_wrapper.py
import os
from typing import List
import mlflow.pyfunc
from provider.ai_providers import *

class GeminiWrapper(mlflow.pyfunc.PythonModel):
    def __init__(self, model_id):
        self.model_id = model_id

    def load_context(self, context):
        self.client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    def predict(self, context, model_input: List[str]) -> List[str]:
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=model_input
        )
        return [response.text]
