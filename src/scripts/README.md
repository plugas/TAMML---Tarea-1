# `src/scripts/` — Scripts de pipeline (ETL)

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![pymupdf4llm](https://img.shields.io/badge/pymupdf4llm-PDF%20→%20Markdown-E94E1B)
![scikit-learn](https://img.shields.io/badge/scikit--learn-t--SNE%20%2B%20KMeans-F7931E?logo=scikit-learn&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-embeddings-412991?logo=openai&logoColor=white)

Scripts independientes que se ejecutan vía `make` para preparar el corpus de datos antes de la ingestión al agente. Hay dos generaciones de scripts:

- **Módulo 1 (legado)**: `merge_reports.py`, `clean_context.py` — preparan el archivo Markdown consolidado que consumen las pestañas Resumen / FAQ / Q&A.
- **Módulo 2 (nuevo)**: `convert_pdfs.py` — convierte PDFs a Markdown para el pipeline RAG.

Cada script calcula su `ROOT` como `Path(__file__).parent.parent.parent` (sube tres niveles desde `src/scripts/`).

## Archivos

### `convert_pdfs.py` (Módulo 2)
**Comando:** `make convert-pdfs`

Convierte todos los PDFs de `data/pdfs/` a Markdown limpio en `data/knowledge/pdfs/`.

**Por qué `pymupdf4llm`:**
- Preserva tablas, encabezados y estructura del documento.
- Compatible con Python 3.14 (al contrario de `markitdown` que arrastraba `onnxruntime==1.20.1` sin wheels para `cp314`).
- Genera Markdown nativo que el chunker jerárquico aprovecha por sus headers `##`/`###`.

**Limpieza aplicada a cada archivo:**
- Quita caracteres corruptos de encoding con regex.
- Elimina líneas con `**==> picture [...] intentionally omitted <==**` que pymupdf inserta para imágenes.
- Normaliza saltos de línea excesivos (`\n{3,}` → `\n\n`).
- Añade encabezado con `# <nombre>` y referencia `> Fuente: data/pdfs/<nombre>.pdf`.

**PDFs procesados (25):**
- 4 informes trimestrales 2025 (I/II/III TRIM)
- 2 informes de sostenibilidad (2024 y 2025)
- Código País, RAC, S&A Climáticos
- 5 comunicados a la SFC (decisiones de JD, escisión, JCSB)
- 4 convocatorias y reportes de Asamblea (AGA marzo 2026)
- 4 documentos de medidas y mecanismos para representación de accionistas
- 2 PDR 2026
- Junta Directiva 2026-2027

### `merge_reports.py` (Módulo 1, legado)
**Comando:** `make merge`

Consolida todos los `.md` de la carpeta `reports/` en un único archivo `data/knowledge/riopaila_castilla.md`. Fue el último paso del scraping del Módulo 1.

Lee `reporte_web_riopaila.md`, `reporte_linkedin_posts_riopaila.md`, `reporte_instagram_posts_riopaila.md`, `reporte_simev_riopaila.md` y los concatena con separadores claros.

### `clean_context.py` (Módulo 1, legado)
**Comando:** `make clean-ctx`

Limpia el archivo consolidado y produce `data/knowledge/riopaila_castilla_clean.md`, que es el archivo que **realmente** consume el motor del Módulo 1 (Resumen / FAQ / Q&A) **y** también consume el ingest del Módulo 2 como una de las 26 fuentes.

Aplica filtros como deduplicación de líneas, normalización de espacios y eliminación de ruido de scraping.

### Scripts del Módulo 3 (OpenFang) y Ruta B

| Script | Comando | Qué hace |
|---|---|---|
| `seed_openfang_kv.py` | `make openfang-kv` | Carga los datos estructurados de `company_info.sql` al **KV Store** del agente OpenFang (`openfang memory set`). Solo stdlib + binario `openfang`. |
| `ingest_openfang.py` | `make openfang-ingest` | Ingesta los documentos a la **memoria semántica** del agente vía la API OpenAI-compatible del OS (`:4200`). Solo stdlib (`urllib`). |
| `telegram_bridge.py` | `make openfang-telegram` | Puente Telegram ↔ agente: long-polling `getUpdates` → `POST /v1/chat/completions` (`openfang:riopaila-coordinador`) → `sendMessage`. Sortea el bug 404 del canal nativo de v0.6.9. Solo stdlib. |
| `seed_interactions.py` | `make tsne-seed` | [Ruta B] Siembra 48 preguntas (8 intenciones × 6 formulaciones) en el historial de `riopaila-faq` y guarda `data/analysis/intent_labels.json`. |
| `tsne_analysis.py` | `make tsne` | [Ruta B] Extrae el historial JSONL de OpenFang, embedde, reduce con **t-SNE + KMeans** y genera `data/analysis/tsne_intenciones.png` + interpretación de clústeres. Requiere `uv sync --extra analysis`. |

## Orden de ejecución completo (desde cero)

```bash
# === Módulo 1 (si no se tiene el KB consolidado) ===
make scrape-all          # 1. scrapers (web, linkedin, instagram, simev)
make build-knowledge     # 2. merge + clean → riopaila_castilla_clean.md

# === Módulo 2 ===
make convert-pdfs        # 3. PDFs → Markdown en data/knowledge/pdfs/
make ingest              # 4. chunk + embed + upload a Supabase
make app                 # 5. lanzar Streamlit
```

## Hallazgos importantes

- **Rutas absolutas con `ROOT`**: cada script declara `ROOT = Path(__file__).parent.parent.parent` para ser robusto independientemente del directorio desde el que se ejecute. No usar rutas relativas.
- **Encoding en Windows**: PowerShell con cp1252 no acepta `→`, `✓`, `✗`. Los scripts usan `OK`, `FAIL`, `->` para evitar `UnicodeEncodeError`.
- **`make` vs `$(MAKE)`**: el Makefile usa `make` literal (no `$(MAKE)`) porque la variable no se expande correctamente en el setup actual del usuario.
- **PDFs binarios no se versionan**: están en `data/pdfs/` pero ignorados por git. Los `.md` convertidos en `data/knowledge/pdfs/` sí pueden versionarse.
