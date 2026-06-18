# Asistente Virtual Corporativo — Riopaila Castilla S.A.

> Proyecto **TAMML** (Taller de Aplicaciones con Modelos de Machine Learning).
> Asistente conversacional para la empresa agroindustrial **Riopaila Castilla S.A.** (Valle del Cauca, Colombia), construido de forma incremental en **tres módulos** que conviven en el mismo repositorio.

<!-- ─────────────────────────── Stack tecnológico ─────────────────────────── -->

#### Núcleo
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![uv](https://img.shields.io/badge/uv-package%20manager-DE5FE9?logo=astral&logoColor=white)
![Make](https://img.shields.io/badge/Makefile-automation-A42E2B?logo=gnu&logoColor=white)
![License](https://img.shields.io/badge/license-academic-blue)

#### Módulo 1 — Q&A (context stuffing)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-orchestration-1C3C3C?logo=langchain&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-Qwen3--32B-F55036?logo=groq&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-scraping-43B02A?logo=selenium&logoColor=white)
![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-parsing-4B8BBE)

#### Módulo 2 — Agente RAG
![OpenAI](https://img.shields.io/badge/OpenAI-gpt--4o--mini-412991?logo=openai&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-ReAct%20agent-1C3C3C?logo=langgraph&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-Postgres-3FCF8E?logo=supabase&logoColor=white)
![pgvector](https://img.shields.io/badge/pgvector-1536d-4169E1?logo=postgresql&logoColor=white)
![LangSmith](https://img.shields.io/badge/LangSmith-tracing-1C3C3C?logo=langchain&logoColor=white)

#### Módulo 3 — Agent OS (Ruta B)
![OpenFang](https://img.shields.io/badge/OpenFang-Agent%20OS%20v0.6.9-FF6B35)
![Rust](https://img.shields.io/badge/Rust-runtime-000000?logo=rust&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-local%20LLM-000000?logo=ollama&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-@RioPaila__Bot-26A5E4?logo=telegram&logoColor=white)

#### Ruta Transversal B — Análisis de datos
![scikit-learn](https://img.shields.io/badge/scikit--learn-t--SNE%20%2B%20KMeans-F7931E?logo=scikit-learn&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-vectores-013243?logo=numpy&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-plots-11557C?logo=python&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-notebook-F37626?logo=jupyter&logoColor=white)

---

## Integrantes

| Nombre | Código |
|---|---|
| Nelcy Lucia Zapata Gil | 22502267 |
| Valentina Isaza Ospina | 22502266 |
| Oscar Fernando Pulgarin | 22500224 |
| Juan Andres Lopez | 2226490 |

---

## Problema y solución

**Riopaila Castilla S.A.** es una empresa agroindustrial con más de un siglo de operación (azúcar, alcohol carburante, cogeneración de energía con bagazo, mieles, aceite de palma). Su información pública está dispersa en el sitio web, redes sociales, informes a la Superintendencia Financiera (SFC/SIMEV) y documentos de gobierno corporativo. Un usuario (empleado, proveedor, accionista o público general) no tiene un canal único para resolver dudas sobre la compañía.

**Solución:** un asistente virtual corporativo que centraliza ese conocimiento y responde en lenguaje natural, **sin alucinaciones**, citando siempre la fuente. El proyecto recorre tres arquitecturas, de la más simple a la más avanzada.

---

## Evolución en tres módulos

| Aspecto | **Módulo 1** — Q&A | **Módulo 2** — Agente RAG | **Módulo 3** — Agent OS (OpenFang) |
|---|---|---|---|
| Recuperación | Léxica (palabras clave) | Semántica (embeddings + pgvector) | Memoria de 6 capas (Vector + KV Store) del OS |
| Decisión de tool | Hardcoded | El agente decide (ReAct) | Router multi-agente (`agent_send`) |
| Memoria | Sesión navegador | Persistente (Supabase) | Sesiones canónicas multicanal del OS |
| Modelo | Groq `Qwen3-32B` | OpenAI `gpt-4o-mini` | `gpt-4o-mini` (+ ruta local Ollama 100% GPU) |
| Canal | Streamlit | Streamlit | **Telegram** (`@RioPaila_Bot`) |
| Autonomía | Reactivo | Reactivo | **Hand autónomo programado** |
| Observabilidad | — | LangSmith | Dashboard OpenFang `:4200` + JSONL |

Los tres módulos conviven: la app Streamlit expone los Módulos 1 y 2; el Módulo 3 corre como un sistema operativo agéntico independiente sobre OpenFang.

---

# Módulo 1 — Q&A con Prompt Engineering (context stuffing)

Punto de partida: un sistema de preguntas y respuestas **sin RAG**. Todo el conocimiento de la empresa se inyecta en el prompt del sistema en cada consulta (*context stuffing*).

- **Modelo:** `Qwen/Qwen3-32B` vía **Groq API** (baja latencia, aceleradores LPU).
- **Framework:** LangChain. **Interfaz:** Streamlit (pestañas *Resumen*, *FAQ*, *Q&A*).
- **Conocimiento:** `data/knowledge/riopaila_castilla_clean.md` (~180 KB), recuperación **léxica** por solape de palabras clave y bigramas (ver `kb.py`).

### Pipeline de datos (scraping)

1. Web scraping del sitio oficial (Selenium + BeautifulSoup).
2. Extracción de Instagram y LinkedIn.
3. Scraping de SIMEV (Superfinanciera) y descarga de PDFs regulatorios.
4. Consolidación (`merge_reports.py`) → limpieza (`clean_context.py`) → `riopaila_castilla_clean.md`.

> Implementación en `src/riopaila_chatbot/scrapers/` y `src/scripts/`. La lógica Q&A está en `src/riopaila_rag/kb.py`.

---

# Módulo 2 — Agente conversacional (RAG + Tools + Memoria)

Evoluciona el chatbot hacia un **agente ReAct** con búsqueda semántica real, tools deterministas y memoria persistente. La interfaz Streamlit conserva las páginas del Módulo 1 y añade la pestaña **Agente**.

## Arquitectura

```
                     ┌──────────────────────┐
                     │   Streamlit (UI)     │
                     │   pagina_agente()    │
                     └──────────┬───────────┘
                                ▼
                     ┌──────────────────────┐
                     │  LangGraph ReAct     │   ← agent.py
                     │  (gpt-4o-mini)       │
                     │  temp=0.1 top_p=0.9  │
                     └──┬──────────────┬────┘
            ┌───────────▼──┐    ┌──────▼────────────┐
            │ rag_search   │    │company_info_search│
            │ (RAG vector) │    │ (datos exactos)   │
            └──────┬───────┘    └──────────┬────────┘
                   ▼                       ▼
        ┌──────────────────────────────────────────┐
        │  Supabase (Postgres + pgvector)          │
        │  - documents      (2515 chunks, 1536d)   │
        │  - company_info   (datos verificados)    │
        │  - chat_messages  (memoria persistente)  │
        └──────────────────────────────────────────┘
```

## Stack

- **LLM:** OpenAI `gpt-4o-mini` (`temperature=0.1`, `top_p=0.9`, streaming).
- **Embeddings:** OpenAI `text-embedding-3-small` (1536 dims).
- **Vector store:** Supabase Postgres + `pgvector` (similitud coseno con `match_documents()`).
- **Agente:** LangGraph `create_react_agent` (loop ReAct con tool-calling nativo).
- **Memoria:** `SupabaseChatHistory` persiste cada turno (human/ai) en `chat_messages`.
- **Observabilidad:** LangSmith (proyecto `TAMLL`).
- **PDF → Markdown:** `pymupdf4llm` (preserva tablas y encabezados).
- **Export:** "Descargar PDF" de la conversación con diseño institucional (`fpdf2`).

## Las dos herramientas del agente

| Tool | Tipo | Uso |
|---|---|---|
| `rag_search(query)` | Semántica | Preguntas narrativas/históricas → embedde la query y llama a `match_documents()` (top-k=12). |
| `company_info_search(category)` | Determinista | Datos exactos (NIT, teléfonos, emails, cifras, sedes) → consulta `company_info` (9 categorías). |

## Pipeline ETL (desde cero)

```bash
# 1. Credenciales — crear .env (ver .env.example)
# 2. Supabase — correr supabase/migrations/001_init.sql + supabase/seeds/company_info.sql
make convert-pdfs    # 3. PDFs → Markdown (pymupdf4llm)  → data/knowledge/pdfs/
make ingest          # 4. chunks + embeddings + upload a Supabase  (~2515 chunks)
make app             # 5. lanzar Streamlit en http://localhost:8501
```

`ingest.py`: recopila el `.md` principal + 25 PDFs convertidos → chunking jerárquico (encabezados → párrafos → oraciones, overlap 20%) → embeddings en lotes de 100 → upload a `documents` con metadata `{fuente, seccion, posicion, total_chunks}`.

## Las 5 pestañas de la app

| Pestaña | Módulo | Modelo | Datos | Memoria |
|---|---|---|---|---|
| Inicio | — | — | — | — |
| Resumen | 1 | Groq Qwen3 | KB consolidado | No |
| FAQ | 1 | Groq Qwen3 | KB consolidado | No |
| Q&A | 1 | Groq Qwen3 | KB consolidado | Sesión navegador |
| **Agente** | **2** | **OpenAI gpt-4o-mini** | **Supabase (vector + structured)** | **Supabase persistente** |

---

# Módulo 3 — Agente corporativo sobre OpenFang Agent OS (Ruta B)

Evolución hacia un **Sistema Operativo Agéntico** usando **[OpenFang](https://github.com/RightNow-AI/openfang)** (Agent OS escrito en **Rust**, MIT/Apache-2.0), con arquitectura **multi-agente** y memoria nativa del OS. Cumple la **Ruta B** de la entrega.

## Arquitectura multi-agente

```
                    Telegram (@RioPaila_Bot)
                          │  telegram_bridge.py (long-polling)
                          ▼
         ┌─────────────────────────────────────────────┐
         │  OpenFang Kernel (daemon, API+dashboard :4200)│
         │  API compatible con OpenAI · modelo gpt-4o-mini│
         └───────────────┬─────────────────────────────┘
                         ▼
              ┌────────────────────────┐
              │ riopaila-coordinador   │  router: clasifica y delega (agent_send)
              └───────┬───────────┬────┘
                      ▼           ▼
        ┌──────────────────┐  ┌────────────────────────┐
        │ riopaila-faq     │  │ riopaila-institucional │
        │ (rápida, ≤3 frases)│ │ (detallada/histórica)  │
        └──────────────────┘  └────────────────────────┘

        Hand autónomo:  riopaila-inteligencia  (vigilancia sectorial programada)
        Memoria OpenFang:  KV Store (43 datos) + Vector Store (documentos)
```

**4 agentes corriendo en paralelo.** El coordinador recibe la consulta, la delega (`agent_send`) en el especialista FAQ o institucional, y devuelve la respuesta indicando quién respondió.

## Componentes

| Componente | Detalle |
|---|---|
| **Kernel** | OpenFang v0.6.9, daemon en `127.0.0.1:4200`, API OpenAI-compatible. |
| **Modelo** | `gpt-4o-mini` (fiable en el agent-loop). Ruta local Ollama (gemma3:4b / qwen2.5:3b a **100% GPU**) instalada y documentada. |
| **Agente institucional** | Datos verificados como **identidad base** en el system prompt (anti-alucinación: NIT, 1918, certificaciones). |
| **Agente FAQ** | Respuestas cortas (`temp 0`, `max_tokens 512`, `seed 7`). |
| **Coordinador (router)** | Delega vía `agent_send` (`tools = [agent_list, agent_send, memory_recall]`). |
| **KV Store** | 43 datos estructurados (de `company_info.sql`) cargados con `seed_openfang_kv.py`. |
| **Memoria semántica** | Documentos ingeridos con `ingest_openfang.py` (API OpenAI-compatible del OS). |
| **Hand autónomo** | `riopaila-inteligencia` — `HAND.toml` + `SKILL.md` (vigilancia sectorial programada). |
| **Canal** | Telegram `@RioPaila_Bot` vía `telegram_bridge.py` (sortea el bug 404 del canal nativo en v0.6.9). |

## Comandos del Módulo 3

```bash
make openfang-start     # arranca el daemon (API + dashboard :4200)
make openfang-spawn     # despliega institucional + faq + coordinador
make openfang-migrate   # carga KV Store + memoria semántica (= openfang-kv + openfang-ingest)
make openfang-hand      # instala y activa el Hand de inteligencia sectorial
make openfang-telegram  # arranca el puente Telegram ↔ agente (bot @RioPaila_Bot)
make openfang-status    # estado del daemon y agentes
```

> Configuración del OS en `openfang/config.toml.example` → copiar a `~/.openfang/config.toml`.
> Guía reproducible paso a paso: **[`docs/runbook-openfang.md`](docs/runbook-openfang.md)**.
> Documento de entrega: **[`docs/entrega-modulo3-openfang.md`](docs/entrega-modulo3-openfang.md)**.

---

# Ruta Transversal B (opcional) — Análisis de comportamiento con t-SNE

Sobre el historial de interacciones del agente OpenFang (sesiones JSONL), se proyectan las intenciones de los usuarios en 2D para descubrir clústeres.

```bash
make tsne-seed   # siembra interacciones representativas (8 intenciones × 6 formulaciones)
make tsne        # genera el análisis t-SNE (PNG + interpretación de clústeres)
```

- **Extracción:** lee `~/.openfang/workspaces/riopaila*/sessions/*.jsonl`.
- **Vectorización:** embeddings `text-embedding-3-small` (cacheados en `data/analysis/`).
- **Reducción:** `t-SNE` (scikit-learn, métrica coseno) + **KMeans** para descubrir agrupaciones.
- **Salida:** `data/analysis/tsne_intenciones.png` + pureza por clúster. Notebook en `notebooks/analisis_tsne.ipynb`.

> Requiere el extra de dependencias de análisis: `uv sync --extra analysis`.
> Interpretación detallada en **[`docs/analisis-tsne.md`](docs/analisis-tsne.md)**.

---

## Instalación y ejecución

El proyecto usa **[uv](https://github.com/astral-sh/uv)** como gestor de entorno y dependencias (reemplaza `pip` + `venv`). Todo está declarado en `pyproject.toml` y bloqueado en `uv.lock`.

```bash
# 1. Instalar uv (una vez)
#    Windows (PowerShell):  irm https://astral.sh/uv/install.ps1 | iex
#    Linux/macOS:           curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Reproducir el entorno
uv sync                      # dependencias base (Módulos 1 y 2)
uv sync --extra analysis     # + numpy/scikit-learn/matplotlib (Ruta B t-SNE)

# 3. Configurar credenciales
cp .env.example .env         # y rellenar las claves (ver más abajo)

# 4. Lanzar la app (Módulos 1 y 2)
make app                     # http://localhost:8501
```

### Variables de entorno (`.env`)

```dotenv
OPENAI_API_KEY=sk-...                 # Módulo 2 (agente + embeddings) y Módulo 3
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
SUPABASE_URL=https://<proyecto>.supabase.co
SUPABASE_KEY=eyJ...                   # clave anon (Legacy JWT)
GROQ_API_KEY=gsk_...                  # Módulo 1
LANGCHAIN_TRACING_V2=true             # LangSmith (Módulo 2)
LANGCHAIN_API_KEY=lsv2_pt_...
LANGCHAIN_PROJECT=TAMLL
TELEGRAM_BOT_TOKEN=123456789:AA...    # Módulo 3 (bot de Telegram)
```

Variables opcionales: `RAG_TOP_K` (def. 12), `CHUNK_SIZE` (def. 1200), `KB_MAX_CONTEXT_CHARS`.

---

## Estructura del repositorio

```
TAMML---Tarea-1/
├── pyproject.toml              # dependencias (uv) + extra [analysis]
├── uv.lock · Makefile · README.md · CONTEXT.md
├── .env.example
│
├── src/
│   ├── riopaila_chatbot/       # Módulo 1 — scrapers
│   │   └── scrapers/           # web.py · linkedin.py · instagram.py · simev.py
│   ├── riopaila_rag/           # Módulos 1 y 2 — app + agente
│   │   ├── app.py              # interfaz Streamlit (5 pestañas)
│   │   ├── agent.py            # LangGraph ReAct + ask_streaming()
│   │   ├── kb.py               # lógica Q&A léxica (Módulo 1)
│   │   ├── chunking.py · ingest.py · memory.py · config.py · paths.py
│   │   ├── agent_chat_pdf.py   # export de conversación a PDF (fpdf2)
│   │   └── tools/              # rag_tool.py · structured_tool.py
│   └── scripts/                # ETL + Módulo 3 + Ruta B
│       ├── merge_reports.py · clean_context.py · convert_pdfs.py
│       ├── seed_openfang_kv.py · ingest_openfang.py · telegram_bridge.py
│       └── seed_interactions.py · tsne_analysis.py
│
├── openfang/                   # Módulo 3 — manifiestos del Agent OS
│   ├── riopaila-institucional/agent.toml
│   ├── riopaila-faq/agent.toml
│   ├── riopaila-coordinador/agent.toml
│   ├── hands/riopaila-inteligencia/  (HAND.toml · SKILL.md)
│   ├── config.toml.example · Modelfile.gemma3-gpu
│
├── supabase/
│   ├── migrations/001_init.sql # documents · chat_messages · company_info + match_documents()
│   └── seeds/company_info.sql  # datos estructurados verificados (9 categorías)
│
├── data/
│   ├── knowledge/              # KB consolidado + 25 PDFs → Markdown
│   └── analysis/               # salidas del t-SNE (Ruta B)
├── notebooks/analisis_tsne.ipynb
└── docs/                       # documentación de entrega (runbook, t-SNE, etc.)
```

---

## Seguridad y buenas prácticas

- **Secretos:** todas las claves se leen del `.env` (en `.gitignore`, nunca versionado). No hay secretos hardcodeados en el código.
- **Anti–prompt injection:** los system prompts establecen una jerarquía de instrucciones inmutable; el contenido del usuario y de las tools se trata como **datos, no órdenes** (Módulos 2 y 3).
- **Anti-alucinación:** datos verificados como identidad base; política explícita de "no inventar" y declinar cuando falta información.
- **XSS:** el render de las burbujas escapa el input del usuario y convierte el Markdown del modelo con `markdown-it` (`html: False`), neutralizando HTML/JS crudo.
- **Supabase:** en desarrollo se usa la `anon key` con RLS desactivada; **para producción deben configurarse políticas RLS** en las 3 tablas.
- **Telegram:** `allowed_users = []` deja el bot abierto para la demo; para uso real, restringir con la lista de IDs permitidos.

### Notas de compatibilidad

- Python 3.10+ (probado en 3.12). Se fija `supabase==2.3.8`, `gotrue>=2.4,<2.5`, `httpx>=0.24,<0.26` por compatibilidad.
- `config.py` se importa **antes** que cualquier módulo de LangChain para que `load_dotenv()` cargue el entorno antes de inicializar el tracing de LangSmith.

---

## Documentación

| Documento | Contenido |
|---|---|
| [`CONTEXT.md`](CONTEXT.md) | Contexto técnico completo del proyecto (decisiones, problemas resueltos). |
| [`docs/ENTREGA-3.md`](docs/ENTREGA-3.md) | **Guía de la Entrega 3 (Ruta B): qué mostrar y dónde está cada punto de la rúbrica.** |
| [`docs/runbook-openfang.md`](docs/runbook-openfang.md) | Guía reproducible paso a paso del Módulo 3. |
| [`docs/entrega-modulo3-openfang.md`](docs/entrega-modulo3-openfang.md) | Documento de entrega del Módulo 3. |
| [`docs/analisis-tsne.md`](docs/analisis-tsne.md) | Análisis e interpretación del t-SNE (Ruta B). |
| READMEs por carpeta | `src/riopaila_rag/`, `.../tools/`, `src/scripts/`, `openfang/`, `supabase/`. |

---

## Autores

- Nelcy Lucia Zapata Gil – 22502267
- Valentina Isaza Ospina – 22502266
- Oscar Fernando Pulgarin – 22500224
- Juan Andres Lopez – 2226490
