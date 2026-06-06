"""Registro de conversaciones vía API para análisis t-SNE (Módulo 3)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from supabase import create_client

from riopaila_rag.config import SUPABASE_KEY, SUPABASE_URL, check_supabase

_logger = logging.getLogger(__name__)
_client = None


def _get_client():
    global _client
    if _client is None:
        check_supabase()
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def log_exchange(
    session_id: str,
    user_message: str,
    assistant_reply: str,
    *,
    channel: str = "api",
) -> None:
    """Persiste un turno completo (opcional si existe la tabla conversation_logs)."""
    try:
        _get_client().table("conversation_logs").insert(
            {
                "session_id": session_id,
                "channel": channel,
                "user_message": user_message,
                "assistant_reply": assistant_reply,
                "transcript": json.dumps(
                    {"user": user_message, "assistant": assistant_reply},
                    ensure_ascii=False,
                ),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ).execute()
    except Exception as exc:
        # Tabla aún no migrada o RLS: no bloquear el chat
        _logger.warning(
            "No se pudo guardar conversation_logs (ejecuta 002 y 003 en Supabase): %s",
            exc,
        )
