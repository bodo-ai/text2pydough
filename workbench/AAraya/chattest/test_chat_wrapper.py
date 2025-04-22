import os
from chat_wrapper import GeminiChatWrapper  # Asegurate de que apunta a tu clase nueva

# Función auxiliar para leer archivos
def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

# Función para formatear el prompt inicial
def format_prompt(prompt_template, script, database, definitions):
    return prompt_template.format(
        script_content=script,
        database_content=database,
        similar_queries="",
        definitions="\n".join(definitions),
        recomendation=""
    )

# Cargar componentes
script = read_file("./cheatsheet_v6.md")
database = read_file("./tcph_graph.md")
prompt_template = read_file("./prompt.md")
definitions = [
    "Total Order Value is defined as the sum of extended_price * (1 - discount)."
]

# Formatear prompt
system_instruction = format_prompt(
    prompt_template,
    script,
    database,
    definitions
)

# Instanciar wrapper
chat = GeminiChatWrapper(
    prompt=system_instruction,
    model_name="gemini-2.5-pro-preview-03-25",
    temperature=0.2
)

# Preguntas para probar persistencia
questions = [
    "¿Qué hace CALCULATE en PyDough?",
    "¿Y cómo se combina con PARTITION?",
    "Dame un ejemplo que use HASNOT"
]

# Ejecutar la conversación
for q in questions:
    print(f"\n🧠 Pregunta: {q}")
    respuesta = chat.ask(q)
    print("🤖 Respuesta:", respuesta)

# Ver historial
print("\n📚 Historial de conversación:")
for i, (user, bot) in enumerate(chat.get_chat_history()):
    print(f"\n🔹 Turno {i+1}")
    print("👤:", user)
    print("🤖:", bot)
