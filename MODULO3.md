# Módulo 3 — Ruta A (LangChain + FastAPI + WhatsApp)

## Estado del repositorio

| Etapa | Estado | Artefacto |
|-------|--------|-----------|
| 1. Agente + Function Calling | ✅ Código | `src/riopaila_rag/agent.py`, `schemas.py`, `tools/` |
| 2. RAG LangChain | ✅ Código | `rag_store.py`, `chunking.py`, `dynamic_prompt` |
| 3. API REST | ✅ Código | `src/riopaila_rag/api/main.py` |
| 4. WhatsApp | 📋 Operativo | N8N: `docs/n8n/workflow_whatsapp_riopaila.json` **o** webhook: `api/whatsapp.py` |
| 5. t-SNE (bonus) | 📋 Datos | `notebooks/tsne_conversaciones.ipynb`, `conversation_logs` |
| 6. Informe PDF | ✅ Generable | `docs/INFORME_TECNICO_MODULO3.md` → `scripts/generate_informe_pdf.py` |

**Checklist completo:** `docs/CHECKLIST_ENTREGA_MODULO3.md`  
**Sustentación:** `docs/SUSTENTACION_EN_VIVO.md`

## Mientras Postgres se desbloquea

- La API usa **InMemorySaver** automáticamente si Postgres falla.
- Guía N8N con tus datos: `docs/N8N_PASO_A_PASO.md`
- Arrancar API en Windows: `scripts/start_api.ps1`
- SQL `conversation_logs`: pegar `supabase/migrations/002_conversation_logs.sql` en el [SQL Editor](https://supabase.com/dashboard/project/azgfxiroyqyplqhncpjy/sql/new)

## Comandos rápidos

```bash
pip install -e .

# Verificar requisitos (sin API)
python scripts/verify_modulo3.py

# API producto
make api
# o: uvicorn riopaila_rag.api.main:app --host 0.0.0.0 --port 8000

# Verificar con API en marcha
python scripts/verify_modulo3.py --api http://127.0.0.1:8000

# Poblar logs para t-SNE (con API activa)
python scripts/seed_conversation_logs.py --api http://127.0.0.1:8000

# Informe PDF
python scripts/generate_informe_pdf.py

# Streamlit (demo interna, opcional)
python run_app.py
```

## Variables de entorno

Copia `.env.example` → `.env`. Crítico para la nota:

- `SUPABASE_DB_URL` → **PostgresSaver** (memoria por teléfono entre reinicios)
- `WHATSAPP_*` → solo si usas webhook FastAPI (Vía 2)

## Migraciones Supabase (SQL Editor)

1. `supabase/migrations/001_init.sql`
2. `supabase/migrations/002_conversation_logs.sql`
3. `supabase/migrations/003_conversation_logs_policies.sql` (si RLS activo)

## WhatsApp — dos vías

| Vía | Documentación |
|-----|----------------|
| **1 — N8N** | `docs/MODULO3_N8N_WHATSAPP.md` + importar workflow JSON |
| **2 — FastAPI** | Webhook `GET/POST /webhooks/whatsapp` + Meta Developer |

## Arquitectura (resumen)

Usuario WhatsApp → Meta → (N8N o webhook) → `POST /chat` → LangChain agent → Supabase (RAG + company_info + checkpoints) → respuesta JSON → WhatsApp.

Diagrama completo en `docs/INFORME_TECNICO_MODULO3.md`.
