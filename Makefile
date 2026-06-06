.DEFAULT_GOAL := help

# ── Aplicación ─────────────────────────────────────────────────────────────────
app:             ## [Módulo 2] Lanza la interfaz Streamlit del agente conversacional
	uv run python run_app.py

api:             ## [Módulo 3] API FastAPI del agente (puerto 8000)
	uv run uvicorn riopaila_rag.api.main:app --host 0.0.0.0 --port 8000

verify-m3:       ## [Módulo 3] Verifica stack LangChain, env y Supabase
	uv run python scripts/verify_modulo3.py

test-api:        ## [Módulo 3] Verifica + prueba POST /chat (API debe estar en marcha)
	uv run python scripts/verify_modulo3.py --api http://127.0.0.1:8000

seed-logs:       ## [Módulo 3] Pobla conversation_logs vía API (requiere make api)
	uv run python scripts/seed_conversation_logs.py --api http://127.0.0.1:8000

informe-pdf:     ## [Módulo 3] Genera docs/INFORME_TECNICO_MODULO3.pdf
	uv run python scripts/generate_informe_pdf.py

# ── Scrapers ───────────────────────────────────────────────────────────────────
scrape-web:      ## Extrae contenido del sitio web de Riopaila
	uv run python -m riopaila_chatbot.scrapers.web

scrape-linkedin: ## Extrae posts de LinkedIn (requiere login manual)
	uv run python -m riopaila_chatbot.scrapers.linkedin

scrape-instagram: ## Extrae posts de Instagram (requiere login manual)
	uv run python -m riopaila_chatbot.scrapers.instagram

scrape-simev:    ## Extrae reportes de SIMEV y descarga PDFs
	uv run python -m riopaila_chatbot.scrapers.simev

scrape-all:      ## Ejecuta todos los scrapers en secuencia
	make scrape-web
	make scrape-simev
	make scrape-linkedin
	make scrape-instagram

# ── Pipeline de conocimiento ───────────────────────────────────────────────────
merge:           ## Une todos los reportes .md en data/knowledge/riopaila_castilla.md
	uv run python src/scripts/merge_reports.py

clean-ctx:       ## Limpia y optimiza el archivo de conocimiento para el LLM
	uv run python src/scripts/clean_context.py

build-knowledge: ## Pipeline completo: merge + limpieza del contexto
	make merge
	make clean-ctx

# ── Módulo 2: RAG con embeddings ───────────────────────────────────────────────
convert-pdfs:    ## [Módulo 2] Convierte PDFs en data/pdfs/ a Markdown
	uv run python src/scripts/convert_pdfs.py

ingest:          ## [Módulo 2] Genera embeddings y sube chunks a Supabase pgvector
	uv run python -m riopaila_rag.ingest

# ── Ayuda ──────────────────────────────────────────────────────────────────────
help:            ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
