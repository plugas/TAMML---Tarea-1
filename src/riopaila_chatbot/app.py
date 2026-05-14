import os
import re
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

KNOWLEDGE_FILE = Path(__file__).parent.parent.parent / "data" / "knowledge" / "riopaila_castilla_clean.md"


def obtener_contexto():
    if not KNOWLEDGE_FILE.exists():
        return "Error: No se encontró el archivo de conocimiento."
    texto = KNOWLEDGE_FILE.read_text(encoding="utf-8")
    texto_limpio = re.sub(r'\s+', ' ', texto)
    return texto_limpio[:18000]


def responder(pregunta, historial):
    try:
        llm = ChatGroq(model="qwen/qwen3-32b", temperature=0)
        contexto = obtener_contexto()

        template = """
        Eres el Asistente experto de Riopaila Castilla.
        Responde basándote exclusivamente en este contexto de forma profesional:
        {contexto_empresa}

        Pregunta del usuario: {pregunta}
        """

        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | llm

        resultado = chain.invoke({
            "contexto_empresa": contexto,
            "pregunta": pregunta
        })

        respuesta = re.sub(r'<think>.*?</think>', '', resultado.content, flags=re.DOTALL).strip()
        return respuesta

    except Exception as e:
        return f"Error: {str(e)}"


with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Asistente Virtual Riopaila Castilla")

    gr.ChatInterface(
        fn=responder,
        title="Chat de Conocimiento Corporativo",
        description="Pregunta lo que desees sobre Riopaila Castilla.",
        examples=[
            "¿Qué productos venden?",
            "¿Cuándo es la asamblea?",
            "¿Quién es el fundador?"
        ]
    )

if __name__ == "__main__":
    demo.launch(share=False)
