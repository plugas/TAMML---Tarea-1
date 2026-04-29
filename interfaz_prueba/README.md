# Interfaz de Prueba – Sistema Q&A Riopaila Castilla

## 1. Descripción general

Esta carpeta contiene la implementación de la interfaz de usuario desarrollada para la validación del sistema de Preguntas y Respuestas (Q&A) de Riopaila Castilla.

El objetivo de esta interfaz es permitir la interacción directa con el modelo de lenguaje en un entorno tipo chatbot, facilitando la evaluación del sistema en tiempo real bajo la arquitectura **NO-RAG basada en Prompt Engineering**.

---

## 2. Arquitectura de la interfaz

La interfaz está construida sobre los siguientes componentes:

- **Framework UI:** Gradio  
- **Modelo LLM:** Qwen/Qwen3-32B (vía ChatGroq API)  
- **Orquestación:** LangChain  
- **Fuente de conocimiento:** `tu_archivo_riopaila.txt`  

Desde el punto de vista arquitectónico, la interfaz actúa como una **capa de interacción ligera (frontend mínimo)** sobre el pipeline de inferencia del modelo.

---

## 3. Flujo de funcionamiento

El sistema opera bajo el siguiente flujo secuencial:

1. El usuario ingresa una pregunta en la interfaz tipo chat.  
2. La aplicación carga el contexto empresarial previamente consolidado.  
3. LangChain construye el prompt con contexto + pregunta del usuario.  
4. El prompt es enviado al modelo Qwen3-32B vía API de Groq.  
5. El modelo genera una respuesta basada exclusivamente en el contexto (NO-RAG).  
6. La respuesta es renderizada en la interfaz en tiempo real.

---

## 4. Implementación técnica

El archivo principal de la interfaz es:

- `app.gradio.py`

### 🔹 Componentes implementados:

- Carga del modelo mediante ChatGroq API  
- Integración del archivo de conocimiento como contexto estático  
- Definición del pipeline LangChain (prompt → LLM → respuesta)  
- Interfaz chat con `ChatInterface` de Gradio  
- Manejo de historial de conversación (opcional según configuración)

---

## 5. Características técnicas de la interfaz

### ✔ Interacción en tiempo real
Permite consultas dinámicas con respuesta inmediata del modelo.

### ✔ Arquitectura ligera
Implementación minimalista sin backend complejo ni frameworks frontend pesados.

### ✔ Integración directa con LLM
La interfaz ejecuta directamente la función de inferencia sin capas intermedias adicionales.

### ✔ Compatibilidad con pipeline LangChain
Permite mantener la lógica de orquestación desacoplada del frontend.

---

## 6. Rol dentro del sistema global

La interfaz cumple el rol de:

- 🔹 Punto de validación del sistema Q&A  
- 🔹 Herramienta de prueba de Prompt Engineering  
- 🔹 Entorno de evaluación de respuestas del modelo  
- 🔹 Visualización del comportamiento del sistema NO-RAG  

---

## 7. Resultado obtenido

La implementación permitió:

- Validar el comportamiento del modelo en condiciones reales de uso  
- Evaluar la calidad de las respuestas generadas  
- Verificar consistencia del sistema en múltiples interacciones  
- Demostrar funcionalidad completa del pipeline (usuario → prompt → LLM → respuesta)  

---

## 8. Limitaciones observadas

- Dependencia del modelo LLM externo (Groq API)  
- No existe almacenamiento persistente de conversación a nivel de base de datos  
- Rendimiento condicionado por la longitud del contexto embebido  
- No se implementa memoria semántica ni recuperación dinámica (NO-RAG por diseño)  

---

## 9. Conclusión

La interfaz desarrollada cumple su objetivo como capa de interacción mínima y eficiente, permitiendo la validación del sistema Q&A sin sobrecarga de infraestructura, y manteniendo coherencia con la arquitectura definida en el proyecto.
