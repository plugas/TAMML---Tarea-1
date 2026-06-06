# N8N paso a paso — Riopaila (datos del equipo)

## Antes de empezar

| Terminal | Comando |
|----------|---------|
| **A** | `uvicorn riopaila_rag.api.main:app --host 0.0.0.0 --port 8000` |
| **B** | `ngrok http 8000` → copia `https://xxxx.ngrok-free.app` |

Datos Meta (del compañero, en tu `.env`):

- Phone number ID: `285101171362806`
- Número de prueba (escribir a): `+1 555 059 8036`
- Token: en `WHATSAPP_ACCESS_TOKEN` (no compartir)

---

## Paso 1 — Cuenta N8N

1. https://app.n8n.cloud → registro gratis.
2. **Workflows** → **Import from file**.
3. Archivo: `docs/n8n/workflow_whatsapp_riopaila.json`

---

## Paso 2 — Nodo «POST Agente /chat»

- **Method:** POST
- **URL:** `https://TU-NGROK.ngrok-free.app/chat` (sin barra final)
- **Body JSON:**

```json
{
  "message": "{{ $json.message }}",
  "session_id": "{{ $json.session_id }}"
}
```

- **Timeout:** 120000 ms

Prueba manual: con la API encendida, en el navegador `http://127.0.0.1:8000/health`.

---

## Paso 3 — Nodo «Enviar respuesta WhatsApp»

- **Method:** POST
- **URL:** `https://graph.facebook.com/v21.0/285101171362806/messages`
- **Authentication:** Header Auth
  - Name: `Authorization`
  - Value: `Bearer TU_TOKEN_DE_META`
- **Body JSON:**

```json
{
  "messaging_product": "whatsapp",
  "to": "{{ $('Parsear mensaje Meta').item.json.session_id }}",
  "type": "text",
  "text": { "body": "{{ $json.reply }}" }
}
```

---

## Paso 4 — Activar y webhook Meta

1. N8N: toggle **Active** ON.
2. Nodo **Webhook Meta WhatsApp** → copia **Production URL**.
3. Meta → WhatsApp → **Configuration** → Webhook:
   - Callback URL = URL de N8N
   - Campo **messages** suscrito
4. Guardar.

---

## Paso 5 — Prueba

1. Celular (número en **Para** de Meta).
2. WhatsApp al `+1 555 059 8036`.
3. Mensaje: `¿Cuál es el NIT de Riopaila Castilla?`
4. Revisar: N8N Executions (verde) + terminal uvicorn + respuesta en celular.

---

## Errores frecuentes

| Síntoma | Solución |
|---------|----------|
| N8N HTTP error ECONNREFUSED | API apagada o ngrok caído |
| 401 en WhatsApp | Token vencido; renovar en Meta API Setup |
| Meta no verifica webhook | Workflow inactivo o URL mal copiada |
| Sin respuesta en celular | Phone number ID incorrecto en nodo envío |
