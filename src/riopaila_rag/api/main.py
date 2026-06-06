"""
FastAPI — endpoint /chat para WhatsApp vía N8N (Módulo 3).

Ejecutar:
    uvicorn riopaila_rag.api.main:app --host 0.0.0.0 --port 8000
    # o: uv run api
"""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from riopaila_rag.agent import ask, clear_session
from riopaila_rag.api.whatsapp import router as whatsapp_router
from riopaila_rag.api.whatsapp import whatsapp_configured
from riopaila_rag.conversation_log import log_exchange

app = FastAPI(
    title="Riopaila Castilla — Agente API",
    description="Productización Módulo 3 (Ruta A)",
    version="0.3.0",
)
app.include_router(whatsapp_router)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str = Field(
        ...,
        min_length=3,
        max_length=64,
        description="Identificador de sesión (ej. número de teléfono WhatsApp)",
    )
    channel: str | None = Field(
        default=None,
        max_length=32,
        description="Canal opcional para logs (api, whatsapp, n8n)",
    )


class ChatResponse(BaseModel):
    reply: str
    session_id: str


@app.get("/health")
def health() -> dict[str, str | bool]:
    from riopaila_rag.checkpoint_store import get_checkpointer

    cp = get_checkpointer()
    cp_name = type(cp).__name__
    postgres = cp_name == "PostgresSaver"
    integration = os.getenv("WHATSAPP_INTEGRATION", "fastapi_webhook").strip()
    return {
        "status": "ok",
        "service": "riopaila-agent",
        "checkpointer": cp_name,
        "postgres_saver": postgres,
        "memory_persistent": postgres,
        "memory_note": (
            "Memoria por session_id en Postgres (sobrevive reinicios)."
            if postgres
            else "InMemorySaver: memoria se pierde al reiniciar la API."
        ),
        "whatsapp_webhook": whatsapp_configured(),
        "whatsapp_integration": integration,
    }


_FRIENDLY_AGENT_ERROR = (
    "En este momento no pude procesar su consulta. "
    "Por favor intente de nuevo en unos minutos."
)


@app.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    session_id = body.session_id.strip()
    message = body.message.strip()
    channel = (body.channel or os.getenv("CHAT_CHANNEL", "api")).strip()

    try:
        reply = ask(message, session_id)
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception:
        reply = _FRIENDLY_AGENT_ERROR

    if not reply or not str(reply).strip():
        reply = _FRIENDLY_AGENT_ERROR

    log_exchange(session_id, message, reply, channel=channel)
    return ChatResponse(reply=reply, session_id=session_id)


@app.delete("/chat/{session_id}")
def reset_session(session_id: str) -> dict[str, str]:
    clear_session(session_id)
    return {"status": "cleared", "session_id": session_id}


def run() -> None:
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("riopaila_rag.api.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    run()
