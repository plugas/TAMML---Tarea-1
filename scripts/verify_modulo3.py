#!/usr/bin/env python3
"""
Verificación de entrega Módulo 3 (Ruta A).

Uso:
    python scripts/verify_modulo3.py
    python scripts/verify_modulo3.py --api http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def _ok(msg: str) -> None:
    print(f"  [OK] {msg}")


def _warn(msg: str) -> None:
    print(f"  [!!] {msg}")


def _fail(msg: str) -> None:
    print(f"  [XX] {msg}")


def check_env() -> bool:
    print("\n1. Variables de entorno (.env)")
    from riopaila_rag.config import (
        OPENAI_API_KEY,
        SUPABASE_DB_URL,
        SUPABASE_KEY,
        SUPABASE_URL,
        WHATSAPP_ACCESS_TOKEN,
    )

    ok = True
    if OPENAI_API_KEY:
        _ok("OPENAI_API_KEY")
    else:
        _fail("Falta OPENAI_API_KEY")
        ok = False
    if SUPABASE_URL and SUPABASE_KEY:
        _ok("SUPABASE_URL + SUPABASE_KEY")
    else:
        _fail("Faltan SUPABASE_URL o SUPABASE_KEY")
        ok = False
    if SUPABASE_DB_URL:
        _ok("SUPABASE_DB_URL (PostgresSaver)")
    else:
        _warn("SUPABASE_DB_URL vacia - InMemorySaver (sin memoria entre reinicios)")
    if WHATSAPP_ACCESS_TOKEN:
        _ok("WhatsApp configurado (webhook FastAPI)")
    else:
        _warn("WhatsApp no configurado (usa N8N o completa WHATSAPP_* en .env)")
    return ok


def check_langchain_stack() -> bool:
    print("\n2. Stack LangChain exigido")
    try:
        from langchain.agents import create_agent  # noqa: F401
        from langchain.agents.middleware import (  # noqa: F401
            HumanInTheLoopMiddleware,
            dynamic_prompt,
        )
        from langchain.chat_models import init_chat_model  # noqa: F401
        from langchain_core.tools import StructuredTool  # noqa: F401
        from langchain_text_splitters import RecursiveCharacterTextSplitter  # noqa: F401

        _ok("imports LangChain M3")
    except ImportError as exc:
        _fail(f"Import fallido: {exc}")
        return False

    from riopaila_rag.schemas import CompanyInfoSearchInput, RagSearchInput
    from riopaila_rag.tools import company_info_search, rag_search

    _ok(f"tools: {rag_search.name}, {company_info_search.name}")
    _ok(f"Pydantic: {RagSearchInput.__name__}, {CompanyInfoSearchInput.__name__}")
    return True


def check_checkpointer() -> None:
    print("\n3. Memoria (checkpointer)")
    from riopaila_rag.checkpoint_store import _probe_postgres, get_checkpointer
    from riopaila_rag.config import SUPABASE_DB_URL

    if SUPABASE_DB_URL and not _probe_postgres(SUPABASE_DB_URL):
        _warn("SUPABASE_DB_URL configurada pero Postgres no conecta (contraseña/URI)")
        _warn("Ejecuta: python scripts/test_supabase_db.py")

    try:
        cp = get_checkpointer()
    except Exception as exc:
        _warn(f"Checkpointer no inicializado: {exc}")
        return
    name = type(cp).__name__
    if name == "PostgresSaver":
        _ok("PostgresSaver activo")
    else:
        _warn(f"Usando {name} (temporal) - memoria se pierde al reiniciar la API")


def check_supabase_logs() -> None:
    print("\n4. Tabla conversation_logs")
    try:
        from riopaila_rag.conversation_log import _get_client

        client = _get_client()
        r = client.table("conversation_logs").select("id").limit(1).execute()
        _ok(f"conversation_logs accesible ({len(r.data or [])} fila muestra)")
    except Exception as exc:
        _warn(f"No accesible: {exc}")
        _warn("Ejecuta supabase/migrations/002 y 003 en SQL Editor")


def check_api(base: str | None) -> None:
    if not base:
        print("\n5. API REST (omitido; pasa --api http://127.0.0.1:8000)")
        return
    print(f"\n5. API REST ({base})")
    try:
        import httpx
    except ImportError:
        _warn("httpx no disponible")
        return

    try:
        with httpx.Client(timeout=180.0) as client:
            h = client.get(f"{base.rstrip('/')}/health")
            h.raise_for_status()
            data = h.json()
            _ok(f"/health OK: {data}")
            r = client.post(
                f"{base.rstrip('/')}/chat",
                json={
                    "message": "¿Cuál es el NIT de Riopaila Castilla?",
                    "session_id": "verify_modulo3_test",
                },
            )
            r.raise_for_status()
            body = r.json()
            reply = (body.get("reply") or "")[:120]
            _ok(f"/chat OK: {reply}...")
    except Exception as exc:
        _fail(f"API no responde: {exc}")
        _warn("Arranca con: make api  o  uvicorn riopaila_rag.api.main:app --port 8000")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default=None, help="URL base FastAPI para probar /health y /chat")
    args = parser.parse_args()

    print("=== Verificación Módulo 3 — Ruta A ===")
    ok = check_env()
    ok = check_langchain_stack() and ok
    check_checkpointer()
    check_supabase_logs()
    check_api(args.api)

    print("\n--- Resumen ---")
    if ok:
        print("Requisitos de código: listos. Completa WhatsApp (N8N o webhook) y el informe PDF.")
        return 0
    print("Corrige los ítems [XX] antes de la sustentación.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
