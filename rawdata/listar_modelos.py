import google.generativeai as genai
import os

# Configura tu API KEY
os.environ["GOOGLE_API_KEY"] = "AIzaSyC5Ix1ZizvvZ6AUYaPpNiN3sXH49A338_U"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

print("--- Modelos disponibles para generar contenido ---")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"Nombre técnico: {m.name}")
        print(f"Nombre para LangChain: {m.name.replace('models/', '')}")
        print("-" * 30)