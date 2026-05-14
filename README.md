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

El conocimiento de la empresa fue previamente extraído mediante web scraping, limpiado y consolidado en un único archivo Markdown que actúa como **memoria del sistema**.

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
- Extracción de posts de LinkedIn e Instagram  
- Descarga y lectura de documentos PDF del portal SIMEV (Superfinanciera)  
- Limpieza y normalización del texto  
- Consolidación en un único archivo de contexto en formato **Markdown** (`.md`)

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
- uv (gestión de entorno y dependencias)  
- LangChain  
- Gradio  
- ChatGroq API  
- Qwen3-32B  
- Selenium & BeautifulSoup (Web Scraping)  
- pdfplumber (lectura de PDFs)  
- Makefile (automatización de tareas)

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

- Nelcy Lucia Zapata Gil – 22502267
- Valentina Isaza Ospina - 22502266
- Oscar Fernando Pulgarin – 22500224
- Juan Andres Lopez - 2226490

---

## Apartado técnico

### Gestión del entorno con uv

El proyecto utiliza [uv](https://github.com/astral-sh/uv) como gestor de entorno virtual y dependencias, reemplazando el flujo tradicional de `pip` + `venv`. Todas las dependencias están declaradas en `pyproject.toml` y el entorno se reproduce de forma exacta mediante `uv.lock`.

Para instalar el entorno desde cero:

```bash
uv sync
```

### Automatización con Makefile

Las tareas del proyecto se ejecutan mediante `make`, evitando tener que recordar comandos largos. Los comandos disponibles son:

| Comando | Descripción |
|---------|-------------|
| `make app` | Lanza la interfaz Gradio del chatbot |
| `make scrape-web` | Extrae contenido del sitio web de Riopaila |
| `make scrape-linkedin` | Extrae posts de LinkedIn |
| `make scrape-instagram` | Extrae posts de Instagram y otras redes |
| `make scrape-simev` | Extrae hechos relevantes de SIMEV y descarga PDFs |
| `make scrape-all` | Ejecuta todos los scrapers en secuencia |
| `make merge` | Consolida los reportes en un único archivo Markdown |
| `make clean-ctx` | Limpia el archivo de conocimiento para el LLM |
| `make build-knowledge` | Pipeline completo: merge + limpieza |
| `make help` | Lista todos los comandos disponibles |

El flujo completo de uso es:

```bash
make scrape-all       # 1. Recolectar información
make build-knowledge  # 2. Consolidar y limpiar el contexto
make app              # 3. Lanzar el chatbot
```

### Contexto en formato Markdown

El archivo de conocimiento que se pasa al modelo está en formato **Markdown** (`.md`) en lugar de texto plano. Esto permite al LLM aprovechar la estructura semántica del documento: los encabezados `##` y `###` indican secciones, las tablas organizan datos clave, y los bloques `>` destacan publicaciones de redes sociales. El resultado es una mejor comprensión del contexto y respuestas más precisas.

El pipeline de construcción genera tres archivos en `data/knowledge/`:

1. `riopaila_castilla.md` — consolidación directa de todos los reportes
2. `riopaila_castilla_clean.md` — versión limpia que consume el modelo ✅

### Estructura del proyecto

```
TAMML---Tarea-1/
├── .gitignore
├── pyproject.toml                # Dependencias y configuración del paquete
├── uv.lock                       # Lock file reproducible
├── Makefile                      # Comandos de automatización
├── README.md
│
├── src/
│   └── riopaila_chatbot/
│       ├── app.py                # Interfaz Gradio + cadena LangChain
│       └── scrapers/
│           ├── web.py            # Scraper del sitio web oficial
│           ├── linkedin.py       # Scraper de LinkedIn
│           ├── instagram.py      # Scraper de Instagram y otras redes
│           └── simev.py          # Scraper de SIMEV + descarga de PDFs
│
├── scripts/
│   ├── merge_reports.py          # Consolida reportes en un único .md
│   └── clean_context.py          # Limpia el contexto para el LLM
│
├── data/
│   ├── knowledge/
│   │   ├── riopaila_castilla.md       # Contexto consolidado
│   │   └── riopaila_castilla_clean.md # Contexto limpio (usado por el modelo)
│   └── pdfs/                          # PDFs descargados de SIMEV
│
└── reports/                      # Reportes individuales por fuente (.md)
    ├── reporte_web_riopaila.md
    ├── reporte_linkedin_posts_riopaila.md
    ├── reporte_instagram_posts_riopaila.md
    └── reporte_simev_riopaila.md
```
