# Interfaz de Prueba – Sistema Q&A Riopaila Castilla

## Descripción
Esta carpeta contiene la interfaz de usuario desarrollada para la validación del sistema Q&A.

La interfaz permite interactuar con el modelo mediante un entorno tipo chatbot.

---

## Tecnología utilizada

- Gradio (UI web)
- Python
- LangChain
- ChatGroq API

---

## Funcionalidad

La aplicación realiza el siguiente flujo:

1. Entrada de pregunta del usuario
2. Carga del contexto empresarial (`tu_archivo_riopaila.txt`)
3. Envío del prompt al modelo LLM
4. Generación de respuesta
5. Visualización en interfaz tipo chat

---

## Archivos

- `app.gradio.py`
- `tu_archivo_riopaila.txt`

---

## Características de la interfaz

- Interacción tipo chat en tiempo real
- Ejecución ligera (low-code UI)
- Integración directa con funciones Python
- Visualización inmediata de respuestas

---

## Resultado

Se logró una interfaz funcional, ligera y eficiente para la validación del sistema Q&A sin necesidad de frontend complejo.
