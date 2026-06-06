#!/usr/bin/env python3
"""
Inserta conversaciones de ejemplo en conversation_logs (bonus t-SNE).

Requiere: migración 002 aplicada y SUPABASE_URL/KEY en .env.

Uso:
    python scripts/seed_conversation_logs.py
    python scripts/seed_conversation_logs.py --api http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

SAMPLE_TURNS = [
    ("573001111001", "¿Cuál es el NIT de Riopaila Castilla?"),
    ("573001111002", "¿Cuáles son los teléfonos de contacto?"),
    ("573001111003", "¿Qué líneas de negocio tiene la empresa?"),
    ("573001111004", "¿Qué certificaciones ambientales reportan?"),
    ("573001111005", "¿Quiénes integran la Junta Directiva?"),
    ("573001111006", "¿Dónde están las sedes principales?"),
    ("573001111007", "¿Qué hace la fundación Riopaila Castilla?"),
    ("573001111008", "¿Cuáles son las cifras clave del último informe?"),
    ("573001111009", "¿Qué redes sociales oficiales tienen?"),
    ("573001111010", "¿Qué reporta el informe de sostenibilidad 2025?"),
    ("573001111011", "¿Cuál es la razón social completa?"),
    ("573001111012", "¿Tienen WhatsApp para accionistas?"),
    ("573001111001", "¿Y el correo de PQRS?"),
    ("573001111013", "Háblame de economía circular en la operación"),
    ("573001111014", "¿Cuántas toneladas de caña procesan?"),
]


def seed_via_api(base: str) -> int:
    import httpx

    ok = 0
    with httpx.Client(timeout=120.0) as client:
        for session_id, message in SAMPLE_TURNS:
            r = client.post(
                f"{base.rstrip('/')}/chat",
                json={"message": message, "session_id": session_id},
            )
            if r.is_success:
                ok += 1
                print(f"  OK {session_id}: {message[:50]}...")
            else:
                print(f"  FAIL {session_id}: {r.status_code} {r.text[:80]}")
    return ok


def seed_via_supabase() -> int:
    from riopaila_rag.conversation_log import log_exchange

    ok = 0
    for session_id, message in SAMPLE_TURNS:
        reply = f"[demo] Respuesta simulada para: {message[:60]}"
        log_exchange(session_id, message, reply, channel="seed")
        ok += 1
        print(f"  OK insert {session_id}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--api",
        default=None,
        help="Si se indica, genera logs reales llamando POST /chat",
    )
    args = parser.parse_args()

    print("=== Seed conversation_logs ===\n")
    if args.api:
        n = seed_via_api(args.api)
    else:
        print("Modo directo Supabase (respuestas simuladas).\n")
        n = seed_via_supabase()
    print(f"\nProcesados: {n}/{len(SAMPLE_TURNS)}")
    print("Siguiente: jupyter notebooks/tsne_conversaciones.ipynb")
    return 0 if n else 1


if __name__ == "__main__":
    raise SystemExit(main())
