import google.generativeai as genai
import os

# 1. CONFIGURACIÓN DE SEGURIDAD Y API
# Reemplaza con tu llave de Google AI Studio
API_KEY = "AIzaSyDpw9KoIgc3_O_7KnijsjLBegV0xs5rTcI"
genai.configure(api_key=API_KEY)

def ejecutar_asistente_riopaila():
    print("--- Iniciando Asistente Riopaila Castilla (Versión Nativa) ---")
    
    # 2. CARGA DEL CONTEXTO
    # Leemos el archivo consolidado que preparaste
    archivo_path = "tu_archivo_riopaila.txt"
    
    if not os.path.exists(archivo_path):
        print(f"Error: No se encuentra el archivo {archivo_path}")
        return

    with open(archivo_path, "r", encoding="utf-8") as f:
        contexto_empresa = f.read()

    # 3. CONFIGURACIÓN DEL MODELO
    # Usamos gemini-1.5-flash que es el más estable y rápido
    model = genai.GenerativeModel('gemini-2.0-flash-lite-001')

    # 4. PREGUNTA DEL USUARIO
    pregunta = "¿Qué productos y servicios ofrece Riopaila Castilla?"

    # 5. CONSTRUCCIÓN DEL PROMPT (Ingeniería de Prompts)
    # Aquí le damos las instrucciones directas al modelo
    prompt_final = f"""
    Eres un experto en la historia y operación de Riopaila Castilla. 
    Tu objetivo es responder de forma profesional basándote en el contexto proporcionado.

    REGLAS:
    - Si la respuesta no está en el texto, di que no tienes la información.
    - Usa puntos clave (bullets) para listar productos.
    - Mantén un tono corporativo.

    CONTEXTO DE LA EMPRESA:
    ---
    {contexto_empresa}
    ---

    PREGUNTA DEL USUARIO:
    {pregunta}

    RESPUESTA:
    """

    # 6. GENERACIÓN DE RESPUESTA
    try:
        print("Consultando a Gemini...")
        response = model.generate_content(prompt_final)
        
        print("\n" + "="*30)
        print("RESPUESTA DEL ASISTENTE:")
        print("="*30)
        print(response.text)
        print("="*30)
        
    except Exception as e:
        print(f"Error al generar contenido: {e}")

if __name__ == "__main__":
    ejecutar_asistente_riopaila()