"""
seed_openfang_kv.py — Carga los datos estructurados verificados de Riopaila Castilla
en el Structured KV Store del agente de OpenFang.

Lee supabase/seeds/company_info.sql (la misma fuente verificada del Módulo 2) y, por
cada fila (category, key, value), ejecuta `openfang memory set <agente> <cat.key> <value>`.

No requiere dependencias externas: usa la stdlib + el binario openfang.

Uso:
    python src/scripts/seed_openfang_kv.py [--agent riopaila-institucional]
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SQL_PATH = REPO_ROOT / "supabase" / "seeds" / "company_info.sql"

# Captura los 3 primeros campos de cada tupla VALUES: ('category', 'key', 'value', ...)
# El 4º campo (description) puede ser texto o NULL; lo ignoramos.
TUPLE_RX = re.compile(
    r"\(\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'((?:[^']|'')*)'",
    re.DOTALL,
)


def find_openfang() -> str:
    """Localiza el ejecutable openfang (PATH o instalación por defecto)."""
    exe = shutil.which("openfang")
    if exe:
        return exe
    default = Path.home() / ".openfang" / "bin" / (
        "openfang.exe" if os.name == "nt" else "openfang"
    )
    if default.exists():
        return str(default)
    sys.exit("ERROR: no se encontró el binario 'openfang'. Instálalo primero.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", default="riopaila-institucional")
    args = parser.parse_args()

    of = find_openfang()
    sql = SQL_PATH.read_text(encoding="utf-8")
    rows = TUPLE_RX.findall(sql)
    print(f"Tuplas encontradas en {SQL_PATH.name}: {len(rows)}")

    ok, fail = 0, 0
    for category, key, value in rows:
        kv_key = f"{category}.{key}"
        value = value.replace("''", "'")
        result = subprocess.run(
            [of, "memory", "set", args.agent, kv_key, value],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if result.returncode == 0:
            ok += 1
        else:
            fail += 1
            print(f"  FALLO {kv_key}: {result.stderr.strip()}")

    print(f"KV cargados OK: {ok} | Fallos: {fail}")


if __name__ == "__main__":
    main()
