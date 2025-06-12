# gemini_wrapper.py
import os
from typing import List
import mlflow.pyfunc
from mlflow.models import set_model
from provider.ai_providers import *

class GeminiWrapper(mlflow.pyfunc.PythonModel):
    def predict(self, context, model_input):
        return model_input
    
set_model(GeminiWrapper())
