# Módulo 3 — Ruta A: API + N8N + WhatsApp

> **Vía alternativa (sin N8N):** webhook en FastAPI — `GET/POST /webhooks/whatsapp`.  
> Ver variables `WHATSAPP_*` en `.env.example` y `src/riopaila_rag/api/whatsapp.py`.

## 0. Importar workflow N8N

1. Abre N8N → **Workflows** → **Import from file**.
2. Selecciona `docs/n8n/workflow_whatsapp_riopaila.json`.
3. Edita el nodo **POST Agente /chat**: reemplaza `https://TU_TUNEL_AQUI` por tu URL ngrok.
4. Edita **Enviar respuesta WhatsApp**: `TU_PHONE_NUMBER_ID` y credencial Bearer con `WHATSAPP_ACCESS_TOKEN`.
5. Activa el workflow y copia la URL del webhook a Meta Developer.

## 1. Variables de entorno

En `.env` agrega:

```env
OPENAI_API_KEY=...
SUPABASE_URL=...
SUPABASE_KEY=...          # JWT anon (eyJ...)
SUPABASE_DB_URL=postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
CHAT_CHANNEL=whatsapp
API_PORT=8000
```

`SUPABASE_DB_URL`: Supabase → Project Settings → Database → Connection string (URI).

## 2. Migraciones Supabase

Ejecuta en el SQL Editor:

1. `supabase/migrations/001_init.sql` (si no está aplicada)
2. `supabase/migrations/002_conversation_logs.sql`

## 3. Arrancar la API

```bash
pip install -e .
uvicorn riopaila_rag.api.main:app --host 0.0.0.0 --port 8000
```

Prueba:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"¿Cuál es el NIT?\", \"session_id\": \"573001234567\"}"
```

## 4. Exponer HTTPS (Meta webhook)

Usa **ngrok** o Cloudflare Tunnel:

```bash
ngrok http 8000
```

Anota la URL pública `https://xxxx.ngrok-free.app`.

## 5. Workflow N8N (vía low-code)

1. **Webhook** (POST) — recibe payload de Meta/Twilio.
2. **Function / Set** — extrae:
   - `message` = texto del usuario
   - `session_id` = teléfono (`from`)
3. **HTTP Request** — POST `https://TU-TUNEL/chat`
   ```json
   {
     "message": "{{ $json.message }}",
     "session_id": "{{ $json.session_id }}"
   }
   ```
4. **HTTP Response / WhatsApp node** — envía `reply` del JSON al usuario.

## 6. Memoria por teléfono

El campo `session_id` del body se usa como `thread_id` en **PostgresSaver** (LangGraph). Mismo número = misma conversación.

## 7. Demo en vivo (sustentación)

- Terminal 1: API (`uvicorn ...`) — muestra logs de peticiones.
- Terminal 2 (opcional): Streamlit (`python run_app.py`) — panel interno.
- N8N: historial de ejecuciones del workflow.
- Profesor escribe por WhatsApp → debe verse el POST en logs y la respuesta con fuentes.
