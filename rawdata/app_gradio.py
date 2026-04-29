import gradio as gr
import os
import re
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# 1. CONFIGURACIÓN
os.environ["GROQ_API_KEY"] = "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"

def obtener_contexto():
    archivo_path = "tu_archivo_riopaila.txt"
    if not os.path.exists(archivo_path):
        return "Error: No se encontró el archivo de conocimiento."
    with open(archivo_path, "r", encoding="utf-8") as f:
        texto = f.read()
    # Limpieza de espacios para optimizar tokens
    texto_limpio = re.sub(r'\s+', ' ', texto)
    return texto_limpio[:18000] 

def responder(pregunta, historial):
    try:
        # Configuración del modelo qwen/qwen3-32b - llama-3.3-70b-versatile
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
        
        # Ejecución
        resultado = chain.invoke({
            "contexto_empresa": contexto, 
            "pregunta": pregunta
        })
        
        return resultado.content

    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# 3. INTERFAZ GRADIO (Versión ultra-compatible)
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🏢 Asistente Virtual Riopaila Castilla")
    
    # Hemos quitado 'type' y los nombres de los botones para evitar el TypeError
    chatbot = gr.ChatInterface(
        fn=responder,
        title="Chat de Conocimiento Corporativo",
        description="Pregunta lo que desees sobre Riopaila Castilla.",
        examples=["¿Qué productos venden?", "¿Cuándo es la asamblea?", "¿Quién es el fundador?"]
    )

if __name__ == "__main__":
    # share=False para evitar problemas de firewall en la universidad
    demo.launch(share=False)
    
    