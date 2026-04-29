# Construcción del Aplicativo Q&A – Riopaila Castilla

## Descripción
Esta carpeta contiene la implementación del sistema de preguntas y respuestas (Q&A) basado en modelos de lenguaje, construido sobre la base de conocimiento previamente generada.

El sistema fue diseñado bajo un enfoque **NO-RAG**, utilizando exclusivamente Prompt Engineering con contexto completo embebido.

---

## Arquitectura del sistema

El sistema está compuesto por:

- Modelo LLM: Qwen/Qwen3-32B (ChatGroq)
- Framework: LangChain
- Estrategia: Prompt Engineering (context stuffing)
- Interfaz: Gradio

---

## Flujo del sistema

1. El usuario ingresa una pregunta
2. Se carga el contexto completo (`tu_archivo_riopaila.txt`)
3. Se construye el prompt del sistema
4. El modelo genera una respuesta basada únicamente en el contexto
5. Se retorna la respuesta en la interfaz

---

## Implementación

Archivo principal:

- `langchain_groq_aplicativo.py`

Este archivo contiene:

- Integración con ChatGroq
- Carga del contexto
- Definición del prompt template
- Pipeline LangChain (prompt + LLM)
- Manejo de respuestas

---

## Inconvenientes técnicos

### 🔹 Ollama (modelo local)
- Alta latencia de inferencia
- Consumo elevado de CPU/RAM
- Ineficiente para pruebas múltiples (20+ preguntas)

---

### 🔹 n8n (no-code automation)
- Generación automática de estructuras tipo RAG
- Pérdida de control sobre el prompt engineering
- Incompatibilidad con la restricción NO-RAG del proyecto

---

### 🔹 Gemini / Vertex AI
- Problemas de autenticación con Vertex
- Inestabilidad en la conexión API
- Limitación de cuota (4–5 preguntas en versión free)

---

## Resultado

Se implementó un sistema funcional, estable y reproducible, capaz de responder consultas corporativas en tiempo real sin degradación de rendimiento.
