# `data/` — Corpus y salidas de análisis

![Markdown](https://img.shields.io/badge/Markdown-corpus-000000?logo=markdown&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-t--SNE-F7931E?logo=scikit-learn&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-embeddings-412991?logo=openai&logoColor=white)

| Carpeta | Contenido | Módulo |
|---|---|---|
| `knowledge/riopaila_castilla.md` | Consolidación directa del scraping (web + redes + SIMEV). | 1 |
| `knowledge/riopaila_castilla_clean.md` | Versión limpia que consumen el Módulo 1 (Q&A) y el ingest del Módulo 2. | 1–2 |
| `knowledge/pdfs/` | 25 PDFs corporativos convertidos a Markdown con `pymupdf4llm` (informes SFC, sostenibilidad, gobierno corporativo). | 2 |
| `pdfs/` | PDFs originales (binarios, **no versionados**). | 2 |
| `analysis/` | Salidas de la Ruta B: `tsne_intenciones.png`, `embeddings.json` (caché), `intent_labels.json`. | Ruta B |

> El corpus de `knowledge/` es la **fuente única de verdad**: alimenta los tres módulos (context stuffing → RAG en Supabase → memoria de OpenFang).
