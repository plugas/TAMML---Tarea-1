"""
Webhook WhatsApp Cloud API (Meta) — Módulo 3, Vía 2 code-centric.

Alternativa a N8N: Meta envía POST a /webhooks/whatsapp y esta app responde
vía Graph API. Requiere WHATSAPP_* en .env (ver .env.example).
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query, Request, Response

from riopaila_rag.agent import ask
from riopaila_rag.config import (
    WHATSAPP_ACCESS_TOKEN,
    WHATSAPP_API_VERSION,
    WHATSAPP_PHONE_NUMBER_ID,
    WHATSAPP_VERIFY_TOKEN,
)
from riopaila_rag.conversation_log import log_exchange

_logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["whatsapp"])


def whatsapp_configured() -> bool:
    return bool(
        WHATSAPP_VERIFY_TOKEN
        and WHATSAPP_ACCESS_TOKEN
        and WHATSAPP_PHONE_NUMBER_ID
    )


@router.get("/whatsapp")
async def verify_webhook(
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
) -> Response:
    """Verificación del webhook en Meta Developer Console."""
    if not WHATSAPP_VERIFY_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="WHATSAPP_VERIFY_TOKEN no configurado en .env",
        )
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        return Response(content=hub_challenge or "", media_type="text/plain")
    raise HTTPException(status_code=403, detail="Token de verificación inválido")


def _extract_inbound_text(body: dict[str, Any]) -> list[tuple[str, str]]:
    """Devuelve lista de (session_id, message) desde el payload de Meta."""
    out: list[tuple[str, str]] = []
    if body.get("object") != "whatsapp_business_account":
        return out
    for entry in body.get("entry") or []:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            for msg in value.get("messages") or []:
                if msg.get("type") != "text":
                    continue
                text = (msg.get("text") or {}).get("body", "").strip()
                wa_from = (msg.get("from") or "").strip()
                if text and wa_from:
                    out.append((wa_from, text))
    return out


def format_reply_for_whatsapp(text: str) -> str:
    """Adapta Markdown del agente al formato que WhatsApp renderiza bien."""
    if not text:
        return text

    out = text

    # [etiqueta](url) no funciona en WhatsApp; mostrar etiqueta y URL aparte.
    out = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1\n\2", out)

    # Negrita Markdown (**texto**) -> sintaxis WhatsApp (*texto*).
    out = re.sub(r"\*\*(.+?)\*\*", r"*\1*", out)

    # Encabezados ## Título -> línea en negrita.
    out = re.sub(r"^#{1,6}\s*(.+)$", r"*\1*", out, flags=re.MULTILINE)

    # Listas con guión o asterisco suelto -> viñeta más legible en móvil.
    out = re.sub(r"^-\s+", "• ", out, flags=re.MULTILINE)
    out = re.sub(r"^\*\s+(?![*\s])", "• ", out, flags=re.MULTILINE)

    # Sección de fuentes con separador visual.
    out = re.sub(
        r"(?im)^\*Fuentes\*$",
        "──────────\n*Fuentes*",
        out,
    )
    out = re.sub(
        r"(?im)^•\s*company_info,\s*categor[ií]a\s+(.+)$",
        r"• company_info · \1",
        out,
    )

    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


async def _send_whatsapp_text(to: str, body: str) -> bool:
    """Envía texto por Graph API. Devuelve False si Meta rechaza el envío."""
    url = (
        f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/"
        f"{WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body[:4096]},
    }
    headers = {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code >= 400:
                _logger.error(
                    "WhatsApp send failed %s to %s: %s",
                    resp.status_code,
                    to,
                    resp.text,
                )
                return False
            return True
    except httpx.HTTPError as exc:
        _logger.exception("WhatsApp send error to %s: %s", to, exc)
        return False


@router.post("/whatsapp")
async def receive_whatsapp(request: Request) -> dict[str, str]:
    """Recibe mensajes de Meta, consulta al agente y responde por Graph API."""
    if not whatsapp_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "WhatsApp no configurado. Define WHATSAPP_VERIFY_TOKEN, "
                "WHATSAPP_ACCESS_TOKEN y WHATSAPP_PHONE_NUMBER_ID en .env"
            ),
        )

    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="JSON inválido") from exc

    pairs = _extract_inbound_text(body)
    if not pairs:
        return {"status": "ignored"}

    channel = os.getenv("CHAT_CHANNEL", "whatsapp")
    for session_id, message in pairs:
        try:
            reply = ask(message, session_id)
        except Exception as exc:
            _logger.exception("Error en agente para %s", session_id)
            reply = (
                "En este momento no pude procesar tu consulta. "
                "Por favor intenta de nuevo en unos minutos."
            )
            _logger.debug("Detalle: %s", exc)

        log_exchange(session_id, message, reply, channel=channel)
        sent = await _send_whatsapp_text(
            session_id,
            format_reply_for_whatsapp(reply),
        )
        if not sent:
            _logger.warning(
                "Respuesta generada pero no enviada a %s (revisa token o lista de testers).",
                session_id,
            )

    # Meta requiere 200 aunque falle el envío; si no, reintenta el webhook.
    return {"status": "ok", "processed": str(len(pairs))}
