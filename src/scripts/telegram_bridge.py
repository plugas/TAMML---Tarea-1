"""
telegram_bridge.py — Puente Telegram ↔ agente de OpenFang.

OpenFang v0.6.9 tiene un bug: su canal nativo de Telegram no se activa
(`POST /api/channels/telegram/enable` → 404). Este puente ligero lo sortea:

  Telegram (long-polling getUpdates)
        │  texto del usuario
        ▼
  OpenFang API OpenAI-compatible  →  POST /v1/chat/completions
        │  (model = openfang:riopaila-institucional)
        ▼
  Telegram sendMessage  →  respuesta del agente

Sin dependencias externas (solo stdlib). Lee TELEGRAM_BOT_TOKEN del .env del proyecto.

Uso:
    python src/scripts/telegram_bridge.py
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# La consola de Windows usa cp1252 por defecto; forzar UTF-8 evita UnicodeEncodeError
# al imprimir acentos o símbolos del texto del usuario.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = REPO_ROOT / ".env"
OPENFANG_CHAT = "http://127.0.0.1:4200/v1/chat/completions"
AGENT_MODEL = "openfang:riopaila-coordinador"   # router multi-agente (delega en faq/institucional)

WELCOME = (
    "👋 Hola, soy el asistente institucional de *Riopaila Castilla S.A.*\n\n"
    "Puedo ayudarte con información sobre la empresa: historia, productos (azúcar, "
    "alcohol carburante, energía, miel), gobierno corporativo, sostenibilidad, "
    "certificaciones y datos de contacto.\n\n"
    "¿Qué te gustaría saber?"
)


def load_token() -> str:
    text = ENV_PATH.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"^\s*TELEGRAM_BOT_TOKEN\s*=\s*(.+?)\s*$", text, re.MULTILINE)
    if not m:
        raise SystemExit("No se encontró TELEGRAM_BOT_TOKEN en .env")
    # limpia posibles caracteres no-ASCII (BOM) en el token
    return re.sub(r"[^\x20-\x7E]", "", m.group(1)).strip()


def http_json(url: str, payload: dict | None = None, timeout: int = 60) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def ask_agent(text: str) -> str:
    payload = {
        "model": AGENT_MODEL,
        "messages": [{"role": "user", "content": text}],
        "stream": False,
    }
    try:
        r = http_json(OPENFANG_CHAT, payload, timeout=120)
        return r["choices"][0]["message"]["content"].strip() or "(respuesta vacía)"
    except Exception as exc:  # noqa: BLE001
        return f"Lo siento, hubo un error consultando al agente: {exc}"


def main() -> None:
    token = load_token()
    api = f"https://api.telegram.org/bot{token}"
    me = http_json(f"{api}/getMe", timeout=15)["result"]
    print(f"Puente activo para @{me['username']}  (Ctrl+C para detener)")
    print(f"Agente: {AGENT_MODEL} vía {OPENFANG_CHAT}")

    offset = 0
    while True:
        try:
            updates = http_json(
                f"{api}/getUpdates?timeout=30&offset={offset}", timeout=40
            ).get("result", [])
        except Exception as exc:  # noqa: BLE001
            print(f"getUpdates error: {exc}; reintentando…")
            time.sleep(3)
            continue

        for upd in updates:
            offset = upd["update_id"] + 1
            msg = upd.get("message") or upd.get("edited_message")
            if not msg or "text" not in msg:
                continue
            chat_id = msg["chat"]["id"]
            user_text = msg["text"]
            print(f">> IN  [{chat_id}] {user_text}")
            if user_text.strip().lower() in ("/start", "/help"):
                reply = WELCOME
            else:
                reply = ask_agent(user_text)
            print(f"<< OUT {reply[:80]}")
            try:
                http_json(
                    f"{api}/sendMessage",
                    {"chat_id": chat_id, "text": reply, "parse_mode": "Markdown"},
                    timeout=20,
                )
            except Exception:
                # reintento sin Markdown por si el formato falla
                http_json(
                    f"{api}/sendMessage",
                    {"chat_id": chat_id, "text": reply},
                    timeout=20,
                )


if __name__ == "__main__":
    main()
