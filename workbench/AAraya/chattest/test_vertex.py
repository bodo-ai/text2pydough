from vertexai import init
from vertexai.language_models import ChatModel

# Inicializa el entorno Vertex AI
init(project="solid-drive-448717-p8", location="us-central1")

# Usa un modelo que sabemos que está disponible y soportado por ChatModel
model = ChatModel.from_pretrained("gemini-1.5-pro")

# Inicia sesión de chat
chat = model.start_chat(
    context="You are a helpful assistant that answers clearly.",
    examples=[],
    temperature=0.2
)

# Prueba un mensaje
response = chat.send_message("What is the capital of France?")
print("Respuesta del modelo:", response.text)
