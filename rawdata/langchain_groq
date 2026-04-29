import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import re

# 1. CONFIGURACIÓN DE API
os.environ["GROQ_API_KEY"] = "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"

def preparar_contexto_compacto(archivo_path):
    """
    Cumple con la regla 'No RAG'. 
    Limpia el texto y realiza un corte lineal para maximizar la densidad de tokens.
    """
    if not os.path.exists(archivo_path):
        return "Error: Archivo de contexto no encontrado."

    with open(archivo_path, "r", encoding="utf-8") as f:
        texto = f.read()
    
    # --- PROCESO DE COMPRESIÓN LINEAL ---
    # 1. Reemplaza múltiples saltos de línea y espacios por uno solo para ahorrar tokens
    texto_compacto = re.sub(r'\s+', ' ', texto)
    
    # 2. Corte a 18,000 caracteres (aprox. 4,500 tokens) 
    # Esto deja margen para el sistema y la respuesta dentro del límite de 6,000 TPM
    contexto_truncado = texto_compacto[:18000]
    
    print(f"--- Contexto procesado: {len(contexto_truncado)} caracteres enviados ---")
    return contexto_truncado

def configurar_asistente_groq():
    # Usamos el modelo 70B que suele tener mejor manejo de prompts densos
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0
    )

    template = """
    Eres el Asistente Virtual experto de Riopaila Castilla. 
    Tu misión es responder preguntas basándote exclusivamente en el contexto proporcionado de manera secuencial.

    CONTEXTO DE LA EMPRESA:
    {contexto_empresa}

    INSTRUCCIONES:
    - Responde de forma profesional y corporativa.
    - Si la información no está en el texto proporcionado, indícalo.

    Pregunta: {pregunta}
    Respuesta:
    """

    prompt = ChatPromptTemplate.from_template(template)
    return prompt | llm

# --- EJECUCIÓN ---
if __name__ == "__main__":
    # Ruta de tu archivo consolidado de Riopaila
    path_txt = "tu_archivo_riopaila.txt"
    
    # Preparación del contexto (Sin RAG, solo truncamiento lineal)
    contexto = preparar_contexto_compacto(path_txt)
    
    asistente = configurar_asistente_groq()
    
    # Pregunta de prueba
    pregunta_usuario = "¿Que hace actualmente Riopaila Castilla?"
    
    try:
        print("Consultando a Groq...")
        respuesta = asistente.invoke({
            "contexto_empresa": contexto, 
            "pregunta": pregunta_usuario
        })
        
        print("\n" + "="*40)
        print("Pregunta enviada: {pregunta_usuario}")
        print("\n" + "="*40)
        print("RESPUESTA DEL ASISTENTE:")
        print("="*40)
        print(respuesta.content)
        print("="*40)
        
    except Exception as e:
        print(f"Error en la comunicación: {e}")