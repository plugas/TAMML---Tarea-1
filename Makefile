.DEFAULT_GOAL := help

# ── Aplicación ─────────────────────────────────────────────────────────────────
app:             ## Lanza la interfaz Gradio del chatbot
	uv run python -m riopaila_chatbot.app

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
	MAKE scrape-web
	MAKE scrape-simev
	MAKE scrape-linkedin
	MAKE  scrape-instagram

# ── Pipeline de conocimiento ───────────────────────────────────────────────────
merge:           ## Une todos los reportes .md en data/knowledge/riopaila_castilla.md
	uv run python scripts/merge_reports.py

clean-ctx:       ## Limpia y optimiza el archivo de conocimiento para el LLM
	uv run python scripts/clean_context.py

build-knowledge: ## Pipeline completo: merge + limpieza del contexto
	MAKE merge
	MAKE clean-ctx

