# Checklist de entrega — Módulo 3 (Ruta A)

Marca cada ítem antes de la sustentación. Orden sugerido.

## A. Base de datos y entorno

- [x] Copiar `.env.example` → `.env` y completar valores (sin subir `.env` a GitHub).
- [x] `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY` (JWT anon `eyJ...`).
- [ ] `SUPABASE_DB_URL` (URI PostgreSQL pooler) para **PostgresSaver** — ver `docs/ARREGLAR_POSTGRES_SAVER.md`
- [ ] SQL Editor Supabase:
  - [ ] `001_init.sql` (si falta)
  - [ ] `002_conversation_logs.sql`
  - [ ] `003_conversation_logs_policies.sql` (si usas RLS)
- [ ] `pip install -e .`
- [x] `python scripts/verify_modulo3.py` → sin `[XX]` (salvo PostgresSaver)

## B. API y agente

- [ ] Terminal 1: `make api` (puerto 8000).
- [ ] `python scripts/verify_modulo3.py --api http://127.0.0.1:8000`
- [ ] Probar misma `session_id` dos veces (debe recordar contexto con PostgresSaver).

## C. WhatsApp (elegir una vía)

### Vía 1 — N8N

- [ ] Cuenta Meta Developer + número de prueba WhatsApp Business.
- [ ] Importar `docs/n8n/workflow_whatsapp_riopaila.json` en N8N.
- [ ] Ajustar URL del nodo HTTP → tu túnel + `/chat`.
- [ ] `ngrok http 8000` (o Cloudflare Tunnel).
- [ ] Webhook Meta apunta a URL pública de N8N.
- [ ] Mensaje de prueba desde celular → respuesta coherente.

### Vía 2 — FastAPI webhook (activa en este proyecto)

- [x] `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` en `.env`.
- [x] `WHATSAPP_INTEGRATION=fastapi_webhook` en `.env`.
- [x] `ngrok http 8000`
- [x] Meta → Callback URL: `https://TU_TUNEL/webhooks/whatsapp`
- [x] Verificación GET exitosa.
- [x] Mensaje de prueba desde celular.
- [x] `/health` muestra `whatsapp_integration: fastapi_webhook`.
- [x] Webhook devuelve 200 aunque falle envío (revisar token/testers en logs).

## D. Bonus t-SNE (+10%)

- [x] `python scripts/seed_conversation_logs.py --api http://127.0.0.1:8000`
- [x] `python scripts/run_tsne.py` (o notebook `notebooks/tsne_conversaciones.ipynb`)
- [x] Exportar gráfico PNG: `docs/tsne_conversaciones.png`
- [x] Párrafo de interpretación de clústeres en el informe.

## E. Documentación y sustentación

- [x] `python scripts/generate_informe_pdf.py` → `docs/INFORME_TECNICO_MODULO3.pdf`
- [ ] Repositorio GitHub actualizado (sin secretos) — ver `docs/ENTREGA_FINAL_MODULO3.md`
- [ ] Ensayo con `docs/SUSTENTACION_EN_VIVO.md` (15 min, sin diapositivas).
- [ ] Celular del profesor en Meta testers + token renovado el día de la demo.

## Rúbrica — autoevaluación

| Criterio | Peso | Listo cuando… |
|----------|------|----------------|
| Arquitectura y agente | 30% | verify_modulo3 OK + PostgresSaver + Pydantic tools |
| Canal mensajería | 30% | WhatsApp responde en vivo |
| Calidad código | 20% | Repo limpio, API + agente estables |
| Informe técnico | 10% | PDF entregado con diagrama y decisión N8N/webhook |
| Demo en vivo | 10% | Prueba con teléfono del profesor sin caídas |
