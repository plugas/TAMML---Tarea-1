#!/usr/bin/env python3
"""Prueba SUPABASE_DB_URL sin imprimir la contraseña."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def _mask(url: str) -> str:
    return re.sub(r":([^:@/]+)@", ":***@", url)


def main() -> int:
    from riopaila_rag.checkpoint_store import _probe_postgres
    from riopaila_rag.config import SUPABASE_DB_URL

    print("=== Test PostgresSaver (SUPABASE_DB_URL) ===")
    if not SUPABASE_DB_URL:
        print("[XX] SUPABASE_DB_URL vacía en .env")
        print("     Dashboard Supabase → Database → Connection string (URI)")
        return 1

    print(f"URI: {_mask(SUPABASE_DB_URL)}")
    if _probe_postgres(SUPABASE_DB_URL):
        print("[OK] Conexión Postgres exitosa — reinicia la API para activar PostgresSaver")
        return 0

    print("[XX] Conexion fallida (revisa contrasena o formato URI)")
    print("     1. Supabase > Database > Reset database password")
    print("     2. Copia URI Session pooler (puerto 5432)")
    print("     3. Actualiza .env y vuelve a ejecutar este script")
    print("     Guia: docs/ARREGLAR_POSTGRES_SAVER.md")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
