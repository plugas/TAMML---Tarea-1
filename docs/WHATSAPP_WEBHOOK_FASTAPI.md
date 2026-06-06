# WhatsApp Vía 2 — Webhook en FastAPI (sin N8N)

## Variables (.env)

```env
WHATSAPP_VERIFY_TOKEN=un_token_secreto_largo
WHATSAPP_ACCESS_TOKEN=EAAxx...   # Meta Developer → token temporal/permanente
WHATSAPP_PHONE_NUMBER_ID=123456789012345
CHAT_CHANNEL=whatsapp
```

## Pasos Meta Developer

1. Crear app **WhatsApp** en developers.facebook.com.
2. Añadir número de prueba y destinatarios de prueba.
3. **Callback URL:** `https://TU_TUNEL/webhooks/whatsapp`
4. **Verify token:** igual a `WHATSAPP_VERIFY_TOKEN`.
5. Suscribirse al campo `messages`.

## Arranque

```bash
make api
ngrok http 8000
```

Verificación: Meta hace `GET /webhooks/whatsapp?hub.mode=subscribe&...` — debe devolver el challenge.

## Prueba

Envía un mensaje de texto desde el celular registrado como tester. La API:

1. Parsea `from` y `text.body` del payload Meta.
2. Llama `ask(mensaje, session_id=from)`.
3. Responde con Graph API `POST .../messages`.

Logs en terminal uvicorn + `conversation_logs` si la migración 002 está aplicada.
