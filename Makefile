.DEFAULT_GOAL := help

# ── Aplicación ─────────────────────────────────────────────────────────────────
app:             ## [Módulo 2] Lanza la interfaz Streamlit del agente conversacional
	uv run python run_app.py

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

# ── Módulo 3: OpenFang Agent OS ────────────────────────────────────────────────
openfang-start:  ## [Módulo 3] Arranca el daemon de OpenFang (API + dashboard :4200)
	openfang start

openfang-status: ## [Módulo 3] Estado del daemon y agentes activos
	openfang status

openfang-spawn:  ## [Módulo 3] Despliega los 3 agentes (institucional, faq, coordinador)
	openfang agent spawn openfang/riopaila-institucional/agent.toml
	openfang agent spawn openfang/riopaila-faq/agent.toml
	openfang agent spawn openfang/riopaila-coordinador/agent.toml

openfang-kv:     ## [Módulo 3] Carga los datos estructurados al KV Store del agente
	python src/scripts/seed_openfang_kv.py

openfang-ingest: ## [Módulo 3] Ingesta los documentos a la memoria semántica del agente
	python src/scripts/ingest_openfang.py

openfang-hand:   ## [Módulo 3] Instala y activa el Hand de inteligencia sectorial
	openfang hand install openfang/hands/riopaila-inteligencia
	openfang hand activate riopaila-inteligencia

openfang-telegram: ## [Módulo 3] Arranca el puente Telegram ↔ agente (bot @RioPaila_Bot)
	python src/scripts/telegram_bridge.py

# ── Ruta Transversal B: análisis de comportamiento (t-SNE) ──────────────────────
tsne-seed:       ## [Ruta B] Siembra interacciones representativas en el historial
	python src/scripts/seed_interactions.py

tsne:            ## [Ruta B] Genera el análisis t-SNE de intenciones (PNG + interpretación)
	python src/scripts/tsne_analysis.py

openfang-migrate: ## [Módulo 3] Migración completa de conocimiento (KV + documentos)
	make openfang-kv
	make openfang-ingest

# ── Ayuda ──────────────────────────────────────────────────────────────────────
help:            ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
