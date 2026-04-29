# Construcción del Aplicativo Q&A – Riopaila Castilla

## 1. Descripción general del módulo

Esta carpeta contiene la implementación del sistema de Preguntas y Respuestas (Q&A) desarrollado para la empresa **Riopaila Castilla**, como parte del Módulo 1 del proyecto.

El objetivo principal es construir un asistente virtual funcional capaz de responder preguntas corporativas utilizando únicamente información previamente extraída y consolidada en un archivo de conocimiento (`tu_archivo_riopaila.txt`).

El sistema se implementa bajo una arquitectura **NO-RAG (No Retrieval-Augmented Generation)**, basada exclusivamente en **Prompt Engineering con contexto completo embebido (context stuffing)**.

---

## 2. Arquitectura del sistema

La arquitectura final del sistema está compuesta por los siguientes componentes:

- **Modelo LLM:** Qwen/Qwen3-32B vía ChatGroq  
- **Framework de orquestación:** LangChain  
- **Interfaz de usuario:** Gradio  
- **Estrategia de conocimiento:** Prompt Engineering (sin RAG)  
- **Fuente de contexto:** archivo consolidado `tu_archivo_riopaila.txt`

Desde el punto de vista arquitectónico, el sistema sigue un enfoque **centralizado de inferencia**, donde todo el conocimiento es inyectado directamente en el prompt del modelo.

---

## 3. Flujo de funcionamiento del sistema

El pipeline de inferencia se define de la siguiente forma:

1. El usuario ingresa una pregunta desde la interfaz Gradio.  
2. Se carga el corpus completo de conocimiento empresarial (`tu_archivo_riopaila.txt`).  
3. Se construye un **prompt de sistema estructurado** con el contexto completo.  
4. LangChain orquesta la entrada (contexto + pregunta) hacia el modelo LLM.  
5. El modelo genera una respuesta basada exclusivamente en el contexto proporcionado.  
6. La respuesta es retornada al usuario en tiempo real.

Este flujo elimina cualquier mecanismo de recuperación externa, garantizando cumplimiento del enfoque **NO-RAG exigido por el enunciado del módulo**.

---

## 4. Implementación técnica

El núcleo del sistema se encuentra en el archivo:

- `langchain_groq_aplicativo.py`

Este script implementa:

### 🔹 Carga del conocimiento
- Lectura del archivo consolidado de scraping
- Limpieza de caracteres y normalización de texto
- Reducción de tamaño a ~18.000 caracteres para optimización de tokens

### 🔹 Construcción del prompt
Se utiliza un `ChatPromptTemplate` con la siguiente estructura conceptual:

- Rol del sistema: asistente corporativo de Riopaila Castilla  
- Contexto completo de la empresa (prompt injection)  
- Pregunta del usuario  

### 🔹 Orquestación con LangChain
LangChain actúa como capa intermedia que permite:

- Encapsular prompt + modelo en un pipeline reproducible  
- Mantener trazabilidad del input/output  
- Facilitar cambios de modelo sin modificar la lógica base  

### 🔹 Ejecución del modelo
El modelo Qwen/Qwen3-32B es invocado vía API de Groq, aprovechando infraestructura optimizada de inferencia de baja latencia.

---

## 5. Limitaciones técnicas y problemas encontrados

Durante la fase de implementación se evaluaron múltiples alternativas tecnológicas, las cuales presentaron limitaciones significativas:

### 🔹 5.1 Ollama (modelos locales)
Se realizaron pruebas con modelos open-source locales.

**Problemas identificados:**
- Alta latencia en inferencia debido a ejecución en CPU local  
- Consumo elevado de recursos (RAM y CPU)  
- Degradación del rendimiento al procesar contexto largo (~18K caracteres)  
- Imposibilidad de escalar pruebas (≥20 preguntas)

➡️ Conclusión: no viable para evaluación iterativa del sistema.

---

### 🔹 5.2 n8n (automatización no-code)
Se evaluó n8n como alternativa de orquestación visual.

**Problemas identificados:**
- Abstracción excesiva del pipeline de LLM  
- Generación automática de estructuras tipo RAG (no permitidas en el módulo)  
- Pérdida de control sobre prompt engineering granular  
- Limitación para implementar arquitectura NO-RAG estricta  

➡️ Conclusión: incompatible con los requerimientos académicos del proyecto.

---

### 🔹 5.3 Gemini / Vertex AI (Google Cloud)
Se implementó integración con modelos Gemini en Vertex AI.

**Problemas identificados:**
- Errores de autenticación y configuración de credenciales  
- Inestabilidad en la conexión API  
- Restricción de cuota en versión gratuita (4–5 consultas máximas)  
- Imposibilidad de ejecutar pruebas extensivas (≥20 preguntas)

➡️ Conclusión: no apto para evaluación continua del sistema.

---

## 6. Decisión de arquitectura final

Dado el análisis comparativo, se seleccionó la siguiente configuración final:

- **Modelo LLM:** ChatGroq (Qwen/Qwen3-32B)  
- **Framework:** LangChain  
- **Interfaz:** Gradio  
- **Estrategia:** Prompt Engineering (NO-RAG con contexto completo)

### 🔹 Justificación técnica

Esta arquitectura fue seleccionada porque:

- Reduce significativamente la latencia de inferencia (infraestructura LPU de Groq)  
- Permite procesar contextos extensos sin degradación crítica  
- Garantiza estabilidad en pruebas múltiples (20+ interacciones)  
- Mantiene control total sobre el prompt system (sin abstracciones externas)  
- Cumple estrictamente la restricción de NO-RAG del enunciado  

---

## 7. Resultado del módulo

El resultado final es un sistema Q&A funcional que:

- Responde preguntas corporativas en tiempo real  
- Utiliza exclusivamente conocimiento preprocesado  
- Mantiene consistencia en respuestas  
- Evita alucinaciones mediante restricción de contexto  
- Opera de forma estable en pruebas extensivas  

---

## 8. Relación con el proyecto global

Este módulo representa la **fase de construcción del “cerebro del chatbot”**, el cual será posteriormente evolucionado hacia arquitecturas más avanzadas (RAG, embeddings y bases vectoriales) en módulos futuros.
