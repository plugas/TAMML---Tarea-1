# TAMML --- Tarea 1  
## Creación de la Base de Conocimiento Semántico y Sistema Q&A (Preguntas y Respuestas)

---

## Descripción del proyecto

Este proyecto corresponde al **Módulo 1** de la asignatura, cuyo objetivo es construir la base de conocimiento de un sistema de preguntas y respuestas (Q&A) para la empresa **Riopaila Castilla**.

El sistema simula un **asistente virtual corporativo**, capaz de responder preguntas de usuarios sobre información pública de la empresa, utilizando técnicas de **Prompt Engineering con modelos de lenguaje (LLMs)**, sin implementar RAG en esta etapa.

---

## Objetivo

Diseñar y construir el núcleo de conocimiento de un chatbot empresarial, capaz de responder preguntas como:

- Productos y servicios
- Historia de la empresa
- Sostenibilidad y medio ambiente
- Estructura organizacional
- Información institucional general

---

## Arquitectura del sistema

El sistema fue desarrollado bajo una arquitectura basada en **context stuffing (sin RAG)**:

- **Modelo LLM:** Qwen/Qwen3-32B  
- **Proveedor:** ChatGroq API  
- **Framework de orquestación:** LangChain  
- **Interfaz de usuario:** Gradio  
- **Estrategia de conocimiento:** Prompt Engineering con contexto completo  

El conocimiento de la empresa fue previamente extraído mediante web scraping, limpiado y consolidado en un único archivo de texto que actúa como **memoria del sistema**.

---

## Funcionalidades

El sistema permite:

- Responder preguntas en lenguaje natural  
- Consultar información institucional de la empresa  
- Generar respuestas basadas únicamente en el contexto suministrado  
- Interacción en tiempo real mediante interfaz web  
- Validación de coherencia en más de 20 preguntas de prueba  

---

## Interfaz de usuario

Se implementó una interfaz web utilizando **Gradio**, que permite:

- Ingresar preguntas desde un campo de texto  
- Obtener respuestas generadas por el modelo en tiempo real  
- Realizar pruebas iterativas del sistema Q&A  

---

## Base de conocimiento

El sistema se alimenta de un corpus construido a partir de:

- Web scraping del sitio oficial de Riopaila Castilla  
- Extracción de secciones relevantes (productos, empresa, sostenibilidad, etc.)  
- Limpieza y normalización del texto  
- Consolidación en un único archivo de contexto (`.txt`)

---

## Evaluación del sistema

Se realizaron pruebas con **más de 20 preguntas**, evaluando:

- Precisión de respuestas  
- Coherencia con el contexto  
- Cobertura de temas empresariales  
- Comportamiento frente a preguntas fuera del dominio  

---

## Limitaciones

- No implementa arquitectura RAG (limitación del diseño del módulo)  
- Dependencia del tamaño de ventana de contexto del LLM  
- Escalabilidad limitada por uso de context stuffing  
- Posibles omisiones si la información no está en el texto base  
- Dependencia de servicios externos (Groq API)

---

## Tecnologías utilizadas

- Python   
- LangChain  
- Gradio  
- ChatGroq API   
- Qwen3-32B   
- BeautifulSoup & Requests (Web Scraping)

---

## Trabajo futuro

Evolución del sistema hacia una arquitectura más escalable:

- Implementación de embeddings semánticos  
- Uso de bases vectoriales (FAISS / ChromaDB)  
- Migración a arquitectura RAG  
- Optimización del chunking semántico  
- Reducción del tamaño del prompt y mejora de eficiencia  

---

## Autores

- Nelcy Lucia Zapata Gil– 22502267
- Valentina Isaza Ospina - 22502266
- Oscar Fernando Pulgarin – 22500224
Proyecto académico desarrollado en el marco de técnicas avanzadas de IA aplicadas a modelos de lenguaje.

---
