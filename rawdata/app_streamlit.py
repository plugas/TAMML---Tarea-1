import streamlit as st
import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import re

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Asistente Riopaila Castilla", page_icon="🏢")

# Título visual
st.title("🏢 Asistente Virtual Riopaila Castilla")
st.markdown("---")

# 1. ENTORNO Y LLAVE API
os.environ["GROQ_API_KEY"] = "TU_API_KEY_DE_GROQ"

# 2. FUNCIÓN DE PROCESAMIENTO (Sin RAG, truncamiento lineal)
def obtener_contexto():
    archivo_path = "tu_archivo_riopaila.txt"
    if not os.path.exists(archivo_path):
        return "Error: No se encontró el archivo de conocimiento."
    
    with open(archivo_path, "r", encoding="utf-8") as f:
        texto = f.read()
    
    # Compresión semántica básica (limpieza de espacios)
    texto_limpio = re.sub(r'\s+', ' ', texto)
    # Corte a 18,000 para cumplir con la cuota de Groq
    return texto_limpio[:18000]

# 3. INTERFAZ DE USUARIO EN STREAMLIT
with st.sidebar:
    st.header("Configuración")
    st.info("Modelo: Llama 3.3 70B\nProveedor: Groq")
    if st.button("Recargar Conocimiento"):
        st.cache_data.clear()
        st.success("Conocimiento actualizado")

# Cuadro de entrada de pregunta
pregunta_usuario = st.text_input("Haz una pregunta sobre la empresa:", placeholder="Ej: ¿Qué productos venden?")

if pregunta_usuario:
    with st.spinner("Consultando al experto..."):
        try:
            # Preparar el motor de inferencia
            llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
            contexto = obtener_contexto()
            
            template = """
            Eres el Asistente experto de Riopaila Castilla. 
            Responde basándote en este contexto de forma profesional:
            {contexto_empresa}

            Pregunta: {pregunta}
            """
            
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | llm
            
            # Ejecución
            respuesta = chain.invoke({
                "contexto_empresa": contexto, 
                "pregunta": pregunta_usuario
            })
            
            # Mostrar respuesta en Streamlit
            st.markdown("### Respuesta:")
            st.write(respuesta.content)
            
        except Exception as e:
            st.error(f"Hubo un error en la comunicación: {e}")

# Pie de página académico
st.markdown("---")
st.caption("Proyecto Maestría en IA - Técnicas Avanzadas de IA")