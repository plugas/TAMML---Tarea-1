# `src/scripts/` — Scripts de pipeline (ETL)

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
