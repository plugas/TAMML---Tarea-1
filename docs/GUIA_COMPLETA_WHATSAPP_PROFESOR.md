# Guía completa — WhatsApp como pide el profesor (Ruta A)

**Ruta del curso:** LangChain + **FastAPI** + **N8N** + **WhatsApp Cloud API (Meta)**.

No uses Streamlit para WhatsApp. Streamlit es solo demo interna en clase.

---

## Qué vas a construir (para entenderlo)

```
[Celular del usuario]
        |
        v
[WhatsApp / Meta Cloud API]  ----webhook HTTPS---->  [N8N en la nube o local]
                                                          |
                                                          | POST http://127.0.0.1:8000/chat
                                                          v
                                                    [Tu API FastAPI en VS Code]
                                                          |
                                                          v
                                                    [Agente LangChain + Supabase]
                                                          |
     Meta envía la respuesta <---- N8N llama Graph API ----'
```

**Tú en VS Code:** solo mantienes la API corriendo.  
**Tú en el navegador:** Meta Developer + N8N.  
**Tú en el celular:** escribes al número de prueba de WhatsApp.

---

## Antes de empezar — checklist de instalación

| Herramienta | Para qué | Dónde conseguirla |
|-------------|----------|-------------------|
| Python + proyecto | API y agente | Ya lo tienes |
| Cuenta Meta Developer | WhatsApp de prueba gratis | developers.facebook.com |
| Cuenta N8N | Workflow visual (pide el profe) | n8n.io (cloud gratis) o `npx n8n` |
| ngrok | HTTPS público hacia tu PC | ngrok.com |

En `.env` (copia de `.env.example`) deben estar como mínimo:

- `OPENAI_API_KEY`
- `SUPABASE_URL` + `SUPABASE_KEY` (JWT `eyJ...`)
- `SUPABASE_DB_URL` (URI PostgreSQL de Supabase) — **memoria por teléfono**

En Supabase SQL Editor, ejecuta si falta:

- `supabase/migrations/002_conversation_logs.sql`

---

## FASE 1 — Solo VS Code (sin WhatsApp aún)

Objetivo: que el “cerebro” funcione antes de conectar el cable WhatsApp.

### Terminal 1 en VS Code (PowerShell)

```powershell
cd "RUTA\A\TU\PROYECTO\TAMML---Tarea-1-feat-rag-langchain"
pip install -e .
python scripts/verify_modulo3.py
```

Debe salir todo `[OK]` o solo avisos `[!!]` en DB_URL / WhatsApp (normal aún).

### Terminal 2 en VS Code — API (déjala abierta siempre)

```powershell
uvicorn riopaila_rag.api.main:app --host 0.0.0.0 --port 8000
```

### Probar en el navegador del PC

Abre: `http://127.0.0.1:8000/health`

Deberías ver JSON con `"status": "ok"`.

### Probar con PowerShell (simula un mensaje de WhatsApp)

```powershell
$body = '{"message":"Cual es el NIT de Riopaila Castilla?","session_id":"573001234567"}'
Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" -Method POST -ContentType "application/json" -Body $body
```

Si recibes `reply` con el NIT, **Fase 1 lista**. Sigue a Fase 2.

> Streamlit (`python run_app.py`) puede quedar en otra terminal para practicar UI; **no cuenta** para WhatsApp.

---

## FASE 2 — Meta Developer (navegador, 20–30 min)

Objetivo: tener número de prueba, token y tu celular autorizado.

1. Entra a https://developers.facebook.com  
2. **Mis aplicaciones** → **Crear aplicación** → tipo **Otro** → nombre: `Riopaila Agente`  
3. Panel de la app → **Añadir producto** → **WhatsApp** → **Configurar**  
4. Menú **WhatsApp** → **API Setup** (Configuración de API). Anota en un bloc:

   | Dato | Dónde está | Para qué |
   |------|------------|----------|
   | **Phone number ID** | API Setup | Enviar respuestas |
   | **Temporary access token** | API Setup (botón copiar) | Autenticación (~24h en prueba) |
   | **Número de prueba de Meta** | Muestra en la misma página | Al que escribirás desde tu celular |

5. Sección **To** (Para) → **Add phone number** → pon **tu celular** → confirma el código que llega por WhatsApp.

Sin el paso 5 no podrás chatear con el bot de prueba.

Guarda en `.env` (para N8N y/o envío de respuestas):

```env
WHATSAPP_ACCESS_TOKEN=el_token_copiado
WHATSAPP_PHONE_NUMBER_ID=el_id_numerico
CHAT_CHANNEL=whatsapp
```

(No hace falta para N8N en el `.env` de Python si el token solo lo pones en el nodo HTTP de N8N; pero conviene tenerlo documentado.)

---

## FASE 3 — N8N (navegador, como pide el profesor)

Objetivo: workflow que recibe WhatsApp y llama tu API.

### 3.1 Crear cuenta N8N Cloud (recomendado para no pelear con ngrok en N8N)

1. https://app.n8n.cloud → registro gratis  
2. Crea un workflow vacío o **Import from file**  
3. Archivo del repo: `docs/n8n/workflow_whatsapp_riopaila.json`

### 3.2 Editar 3 nodos del workflow importado

**Nodo «POST Agente /chat»**

- Method: POST  
- URL: `http://127.0.0.1:8000/chat` **NO sirve si N8N está en la nube**

Si usas **N8N Cloud**, tu API en el PC debe ser pública:

1. En VS Code, Terminal 3: `ngrok http 8000`  
2. Copia la URL `https://xxxx.ngrok-free.app`  
3. URL del nodo: `https://xxxx.ngrok-free.app/chat`  
4. Body JSON:

```json
{
  "message": "{{ $json.message }}",
  "session_id": "{{ $json.session_id }}"
}
```

**Nodo «Enviar respuesta WhatsApp»**

- URL: `https://graph.facebook.com/v21.0/TU_PHONE_NUMBER_ID/messages`  
  (reemplaza `TU_PHONE_NUMBER_ID`)  
- Authentication: Header Auth  
  - Name: `Authorization`  
  - Value: `Bearer TU_TOKEN_DE_META`  
- Body:

```json
{
  "messaging_product": "whatsapp",
  "to": "{{ $('Parsear mensaje Meta').item.json.session_id }}",
  "type": "text",
  "text": { "body": "{{ $json.reply }}" }
}
```

**Nodo «Webhook Meta WhatsApp»**

- Copia la **Production URL** del webhook (aparece al activar el workflow).

### 3.3 Activar workflow

Toggle **Active** = ON. Sin esto Meta no puede llamar a N8N.

---

## FASE 4 — Conectar Meta con N8N (navegador)

1. Meta Developer → tu app → **WhatsApp** → **Configuration**  
2. **Webhook** → **Edit**  
3. **Callback URL:** pega la Production URL del webhook de N8N  
4. **Verify token:** inventa uno (ej. `riopaila_n8n_2025`) — si N8N no valida token, usa el modo test de Meta primero  
5. **Webhook fields:** suscríbete a **messages**  
6. Guardar. Debe decir que verificó correctamente.

---

## FASE 5 — Trabajo en paralelo el día de la prueba

| Dónde | Qué tener abierto |
|-------|-------------------|
| **VS Code Terminal A** | `uvicorn ... port 8000` (API) |
| **VS Code Terminal B** | `ngrok http 8000` (solo si N8N Cloud) |
| **Navegador** | N8N → Executions (historial) |
| **Navegador** | Meta Developer (por si renuevas token) |
| **Celular** | WhatsApp → chat con **número de prueba de Meta** |

### Prueba final

1. Desde tu celular (número registrado en **To**), envía:  
   `¿Cuál es el NIT de Riopaila Castilla?`  
2. En N8N: ejecución verde del workflow  
3. En Terminal A: log de petición  
4. En el celular: respuesta del bot en segundos  

Segunda pregunta (memoria):  
`¿Y el teléfono de contacto?`  
— debe recordar contexto si `SUPABASE_DB_URL` está bien.

---

## Qué mostrar al profesor (sustentación 15 min)

1. **Código VS Code:** `agent.py` (create_agent, Pydantic), `api/main.py` (`/chat`)  
2. **Terminal:** API + log cuando él escribe por WhatsApp  
3. **N8N:** pantalla Executions con el flujo webhook → HTTP → WhatsApp  
4. **Celular:** él escribe → respuesta en vivo  
5. **Opcional:** Supabase `conversation_logs` o notebook t-SNE  

---

## Si algo falla

| Problema | Solución |
|----------|----------|
| Meta no verifica webhook | URL incorrecta; workflow N8N inactivo |
| N8N verde pero sin respuesta en celular | Token vencido; Phone number ID mal; Bearer sin `Bearer ` |
| N8N error en HTTP Request | API apagada; ngrok caído; URL sin `/chat` |
| API 503 | Falta `OPENAI_API_KEY` |
| No recuerda conversación | Falta `SUPABASE_DB_URL` |

---

## Alternativa (solo si el profe acepta “servidor propio” sin N8N)

Usa `docs/WHATSAPP_WEBHOOK_FASTAPI.md`: un solo ngrok al 8000 y webhook `/webhooks/whatsapp`.  
**Para la rúbrica que menciona N8N explícitamente, usa esta guía (Fases 3–4 con N8N).**

---

## Orden resumido (no saltar pasos)

1. API `/chat` funciona en local (Fase 1)  
2. Meta: token + tu celular tester (Fase 2)  
3. N8N importado y nodos editados (Fase 3)  
4. Meta webhook → URL de N8N (Fase 4)  
5. Prueba desde celular (Fase 5)

Cuando termines Fase 1, ya cumples gran parte del código; WhatsApp es conectar los cables.
