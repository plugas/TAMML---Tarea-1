from google import genai
import os

# 1. CONFIGURACIÓN DEL CLIENTE (Librería nueva google-genai)
client = genai.Client(api_key="AIzaSyC5Ix1ZizvvZ6AUYaPpNiN3sXH49A338_U")

def asistente_riopaila_2026():
    # 2. CARGA DEL CONTEXTO
    archivo_path = "tu_archivo_riopaila.txt"
    with open(archivo_path, "r", encoding="utf-8") as f:
        contexto_empresa = f.read()

    # 3. PREGUNTA
    pregunta = "¿Qué productos y servicios ofrece Riopaila Castilla?"

    # 4. LLAMADA AL MODELO USANDO EL ALIAS CONFIRMADO
    # Usamos 'gemini-flash-latest' de tu lista para evitar el 404
    try:
        print("Consultando a la infraestructura estable de Gemini...")
        response = client.models.generate_content(
            model='gemini-flash-latest', 
            contents=f"Contexto: {contexto_empresa}\n\nPregunta: {pregunta}"
        )
        
        print("\n" + "="*30)
        print("RESPUESTA:")
        print(response.text)
        print("="*30)

    except Exception as e:
        print(f"Error de cuota o conexión: {e}")
        # Si 'flash-latest' da 429 por cuota, el 'flash-lite-latest' es tu salvavidas
        print("\nIntentando con versión Lite para ahorrar cuota...")
        response_lite = client.models.generate_content(
            model='gemini-flash-lite-latest',
            contents=f"Contexto: {contexto_empresa}\n\nPregunta: {pregunta}"
        )
        print(response_lite.text)

if __name__ == "__main__":
    asistente_riopaila_2026()