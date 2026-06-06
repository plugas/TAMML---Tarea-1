# Guion de sustentación en vivo (15 minutos)

**Formato:** 100% práctica — terminales, N8N/Meta, sin diapositivas.

## Antes (30 min)

1. `make api` en terminal visible.
2. Túnel HTTPS activo (ngrok) apuntando al puerto 8000.
3. WhatsApp configurado (N8N o webhook).
4. `GET /health` muestra `"postgres_saver": true` (ideal).
5. Celular de prueba con mensaje ya enviado una vez.

## Minuto 0–2 — Contexto

- "Riopaila Castilla, Ruta A: LangChain Function Calling + FastAPI + WhatsApp."
- Mostrar `agent.py`: `create_agent`, `init_chat_model`, `HumanInTheLoopMiddleware`, `dynamic_prompt`.
- Mostrar `schemas.py` + `StructuredTool` en `tools/`.

## Minuto 2–5 — API

```powershell
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"message\": \"¿Cuál es el NIT?\", \"session_id\": \"demo_sustentacion\"}"
```

- Explicar `session_id` = teléfono = `thread_id` en PostgresSaver.

## Minuto 5–10 — Prueba de fuego WhatsApp

1. Pedir al profesor que envíe: *"¿Cuál es el NIT de Riopaila Castilla?"*
2. Señalar logs en terminal (POST /chat o webhook).
3. Mostrar respuesta en el teléfono.
4. Segunda pregunta con referencia: *"¿Y el teléfono de contacto?"* — misma sesión.

## Minuto 10–12 — Tras bambalinas

- Streamlit opcional: pestaña Agente + panel "Ver fuentes consultadas".
- Supabase: tabla `conversation_logs` (si aplica t-SNE).
- N8N: historial de ejecución del workflow (si usan Vía 1).

## Minuto 12–15 — Preguntas

Temas preparados:
- Por qué Pydantic evita invención de parámetros en tools.
- Diferencia N8N vs webhook propio.
- Qué pasa si RAG no encuentra chunks (`tool_errors`).
- Cómo escalaría a producción (RLS, service_role, rate limits).

## Si algo falla

| Síntoma | Acción rápida |
|---------|----------------|
| API 503 | Revisar `OPENAI_API_KEY` |
| Sin memoria | Completar `SUPABASE_DB_URL`, reiniciar API |
| WhatsApp no responde | Verificar token Meta, URL túnel, webhook verify |
| Respuesta vacía | `verify_modulo3.py --api ...` |
