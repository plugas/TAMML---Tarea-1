"""Configuración centralizada — lee todas las variables de entorno del proyecto."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    val = os.getenv(key, "").strip()
    if not val:
        raise EnvironmentError(
            f"Variable de entorno requerida no encontrada: {key}\n"
            f"Revisa el archivo .env en la raíz del proyecto."
        )
    return val


def _optional(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


# ── OpenAI ────────────────────────────────────────────────────────────────────
OPENAI_API_KEY: str = _optional("OPENAI_API_KEY")
LLM_MODEL: str = _optional("LLM_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL: str = _optional("EMBEDDING_MODEL", "text-embedding-3-small")

# ── Supabase ──────────────────────────────────────────────────────────────────
SUPABASE_URL: str = _optional("SUPABASE_URL")
SUPABASE_KEY: str = _optional("SUPABASE_KEY")       # legacy anon key
SUPABASE_DB_URL: str = _optional("SUPABASE_DB_URL")

# ── Groq (legado Módulo 1, mantenemos compatibilidad) ─────────────────────────
GROQ_API_KEY: str = _optional("GROQ_API_KEY")

# ── LangSmith (observabilidad) ────────────────────────────────────────────────
LANGCHAIN_TRACING_V2: str = _optional("LANGCHAIN_TRACING_V2", "false")
LANGCHAIN_API_KEY: str = _optional("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT: str = _optional("LANGCHAIN_PROJECT", "riopaila-agent-module2")

# ── Chunking (ajustable sin tocar código) ─────────────────────────────────────
CHUNK_SIZE: int = int(_optional("CHUNK_SIZE", "800"))
CHUNK_OVERLAP: int = int(_optional("CHUNK_OVERLAP", "120"))

# ── Retrieval ─────────────────────────────────────────────────────────────────
RAG_TOP_K: int = int(_optional("RAG_TOP_K", "5"))

# ── Rutas ─────────────────────────────────────────────────────────────────────
ROOT_DIR: Path = Path(__file__).resolve().parent.parent.parent
KNOWLEDGE_FILE: Path = ROOT_DIR / "data" / "knowledge" / "riopaila_castilla_clean.md"


def check_openai() -> None:
    """Lanza error claro si falta OPENAI_API_KEY."""
    if not OPENAI_API_KEY:
        raise EnvironmentError(
            "Falta OPENAI_API_KEY en el .env. "
            "Obtén una en platform.openai.com y agrégala al archivo .env"
        )


def check_supabase() -> None:
    """Lanza error claro si faltan credenciales de Supabase."""
    missing = [k for k in ("SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_DB_URL")
               if not os.getenv(k, "").strip()]
    if missing:
        raise EnvironmentError(
            f"Faltan variables de Supabase: {', '.join(missing)}\n"
            "Créalas en supabase.com y agrégalas al .env"
        )
