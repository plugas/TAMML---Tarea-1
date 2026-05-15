# `src/riopaila_rag/` — Núcleo del agente RAG

Este paquete contiene **todo** el código del Módulo 2: agente, tools, memoria, ingestión y la interfaz Streamlit. También conserva el motor legado del Módulo 1 (`kb.py`).

## Archivos del paquete

### `__init__.py`
Marcador del paquete. Vacío por convención: las funciones públicas se importan explícitamente desde cada módulo.

### `paths.py`
Rutas centralizadas del proyecto (calculadas desde la ubicación del archivo, `ROOT = parent.parent.parent`).
Expone `ASSETS_DIR`, `PATH_CONSOLIDADO` (`data/knowledge/riopaila_castilla_clean.md`), `DATA_DIR`.

### `config.py`
Lee todas las variables de entorno con `python-dotenv` y las expone como constantes tipadas.

**Variables principales:**
| Variable | Default | Para qué se usa |
|---|---|---|
| `OPENAI_API_KEY` | — | LLM y embeddings |
| `LLM_MODEL` | `gpt-4o-mini` | Modelo conversacional |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embeddings (1536 dims) |
| `SUPABASE_URL` | — | URL del proyecto |
| `SUPABASE_KEY` | — | Anon key |
| `CHUNK_SIZE` | `1200` | Tamaño máximo del chunk en chars (overlap = 20%) |
| `RAG_TOP_K` | `5` | N fragmentos a retornar en cada búsqueda |
| `LANGSMITH_API_KEY` | — | Tracing (opcional) |
| `GROQ_API_KEY` | — | Legacy módulo 1 |

Incluye funciones `check_openai()` y `check_supabase()` que lanzan `EnvironmentError` con mensaje claro si faltan credenciales.

### `chunking.py`
**Chunking manual jerárquico** (no usa `langchain-text-splitters`). Estrategia:

1. Divide el texto por encabezados Markdown (`#`, `##`, `###`).
2. Si una sección excede `chunk_size`, la divide por párrafos (doble salto de línea).
3. Si un párrafo aún excede, divide por oraciones con **overlap del 20%** del `chunk_size`.

**Funciones públicas:**
- `chunk_text(text, source, chunk_size) -> list[Chunk]`
- `chunk_file(path, chunk_size) -> list[Chunk]`

**Metadata por chunk:** `{seccion, fuente, posicion, total_chunks, chunk_size_config, overlap_config}`.

Con `CHUNK_SIZE=1200`: ~430 chars promedio, overlap 240 chars (~20%).

### `ingest.py`
**Pipeline ETL completo** del Módulo 2 (`make ingest`):

1. Recopila archivos `.md` (`riopaila_castilla_clean.md` + `data/knowledge/pdfs/*.md`).
2. Pide confirmación (o `--force` para saltarla).
3. Limpia la tabla `documents` de Supabase.
4. Chunkea con `chunk_file()` (chunk_size=1200, overlap=240).
5. Genera embeddings en batches de **100 chunks** con OpenAI `text-embedding-3-small`.
6. Sube cada batch a Supabase con `client.table("documents").insert(rows).execute()`.

Resultado típico: ~2.515 chunks indexados desde 26 archivos.

### `memory.py`
**Memoria conversacional persistente** en Supabase.

Clase `SupabaseChatHistory(BaseChatMessageHistory)` que:
- Lee/escribe en la tabla `chat_messages` filtrando por `session_id`.
- Convierte cada fila JSONB `{type: 'human'|'ai', content: ...}` a `HumanMessage` / `AIMessage` de LangChain.
- Métodos: `.messages` (property), `.add_message(msg)`, `.clear()`.

Compatible con cualquier integración LangChain que espere `BaseChatMessageHistory`.

### `agent.py`
**Agente conversacional ReAct** construido con `langgraph.prebuilt.create_react_agent`.

**Configuración del LLM:**
```python
ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1,      # respuestas deterministas
    top_p=0.9,            # solo tokens muy probables
    streaming=True,
)
```

**Tools registradas:** `rag_search` + `company_info_search` (importadas de `tools/`).

**System prompt:** ~6 KB con 7 secciones (identidad, jerarquía anti-injection, alcance, política de tools, manejo de incertidumbre, formato de salida, comportamiento institucional). Diseñado para resistir prompt injection y mantener formalidad corporativa.

**Funciones públicas:**
- `ask(question, session_id) -> str` — modo bloqueante.
- `ask_streaming(question, session_id) -> Iterator[AgentEvent]` — emite eventos `tool_call` / `tool_result` / `token` / `final` en tiempo real (consumido por `app.py` con `st.write_stream`).
- `clear_session(session_id)` — borra el historial de Supabase.

El agente es **singleton lazy**: se construye en la primera llamada y se reusa.

### `app.py`
**Interfaz Streamlit** completa con 5 pestañas:

- **Inicio, Resumen, FAQ, Q&A** → Módulo 1 (Groq Llama).
- **Agente** → Módulo 2 (calco visual de Q&A con motor RAG ReAct).

Detalles del Agente:
- Hero carrusel + header verde institucional (reusa estilos de Q&A).
- Columna izquierda: 5 ejemplos de preguntas + panel `Ver fuentes consultadas` (altura fija 240 px, scroll interno).
- Columna derecha: transcript del chat + sugerencias + input + Enter o botón **Enviar**.
- Streaming: spinner durante la generación; respuesta completa al terminar dentro de la burbuja del bot.
- Persistencia: cada sesión tiene un `session_id` único guardado en Supabase.

### `kb.py` (legado Módulo 1)
Base de conocimiento por **recuperación léxica** (sin embeddings). Lee `riopaila_castilla_clean.md` y selecciona fragmentos por coincidencia de palabras clave. Usa Groq + LangChain. Consumido por las pestañas Resumen, FAQ y Q&A.

### `assets/`
Recursos estáticos: logo, logotipo, hero principal y 7 imágenes del carrusel (`hero_carousel/`).

### `tools/`
Subpaquete con las dos herramientas del agente. Ver [`tools/README.md`](tools/README.md).

## Hallazgos importantes

- **Python 3.14**: requiere `supabase==2.3.8`, `gotrue>=2.4,<2.5`, `httpx>=0.24,<0.26`. Versiones más nuevas dependen de `onnxruntime==1.20.1` sin wheels para `cp314`.
- **Encoding en Windows**: PowerShell con `cp1252` rompe con `→`, `✓` y similares. Los scripts evitan esos caracteres.
- **RLS de Supabase**: en dev debe estar **desactivado** en las 3 tablas para que la `anon key` lea/escriba.
- **Costo de embeddings**: ingestar los 2.515 chunks cuesta ~USD 0.10 con `text-embedding-3-small`.
- **`RunnableWithMessageHistory` deprecado**: por eso `agent.py` maneja la memoria manualmente (carga historial → invoca → guarda) en vez de envolverlo.
