from langchain_ollama import OllamaLLM
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate



# 1. CARGA Y PROCESAMIENTO DEL TEXTO (Punto 2 de la tarea)
def preparar_conocimiento(archivo_path):
    with open(archivo_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Segmentación (Chunking) para asegurar coherencia semántica
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000, 
        chunk_overlap=300,
        separators=["\n\n", "\n", ".", " "]
    )
    
    chunks = text_splitter.split_text(raw_text)
    # Consolidamos el texto limpio para el Prompt de Sistema (Punto 3)
    return "\n".join(chunks)

# 2. CONFIGURACIÓN DEL MODELO Y PROMPT (Punto 3 de la tarea)
def configurar_sistema_qa(contexto):
    # Inicializamos Llama 3 vía Ollama
    # llm = OllamaLLM(model="llama3", temperature=0) # temperature=0 para evitar alucinaciones
    
    #llm = OllamaLLM(model="gemma2:2b", temperature=0, num_thread=6) # Usa los 6 núcleos de tu i5-9400
    
    llm = OllamaLLM(model="phi3", temperature=0, num_ctx=4096, num_thread=8) # Aumentamos un poco el contexto ya que tienes 16GB RAM, Usamos 8 hilos de tu i7 para ir más rápido
    # Diseño del Prompt Robusto (Prompt Engineering)
    template = """
    Eres el Asistente Virtual experto de Riopaila Castilla. Tu función es responder preguntas 
    basándote exclusivamente en la información proporcionada.

    REGLAS DE ORO:
    1. Usa solo el CONTEXTO proporcionado para responder.
    2. Si la respuesta no está en el CONTEXTO, di: "Lo siento, no tengo información oficial sobre esa consulta en mi base de datos de Riopaila Castilla."
    3. Mantén un tono profesional, servicial y corporativo.
    4. NO menciones que eres un modelo de lenguaje; actúa como un representante de la empresa.

    CONTEXTO:
    {contexto_empresa}

    PREGUNTA DEL USUARIO: {pregunta}
    
    RESPUESTA:
    """

    prompt = ChatPromptTemplate.from_template(template)
    
    # Creamos la cadena (Chain)
    chain = prompt | llm
    return chain

# --- EJECUCIÓN INICIAL ---
# archivo_plano = "tu_archivo_riopaila.txt" # Cambia por el nombre de tu archivo
archivo_plano = "contexto_optimizado.txt" # Cambia por el nombre de tu archivo
conocimiento_base = preparar_conocimiento(archivo_plano)
sistema_qa = configurar_sistema_qa(conocimiento_base)

# Ejemplo de prueba técnica
respuesta = sistema_qa.invoke({"contexto_empresa": conocimiento_base, "pregunta": "¿Que ha hecho Riopaila en los ultimos 10 años?"})
print(respuesta)