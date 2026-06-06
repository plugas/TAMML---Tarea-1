"""
ingest_openfang.py — Migra la base de conocimiento documental de Riopaila Castilla
al sustrato de memoria semántica (Vector Store) del agente de OpenFang.

Mecanismo: OpenFang expone una API compatible con OpenAI en http://127.0.0.1:4200/v1.
Cada documento se envía al agente con la instrucción de memorizarlo; el agente usa su
herramienta `memory_store` para persistirlo en su memoria semántica (búsqueda vectorial).

Complementa a seed_openfang_kv.py (que carga los datos estructurados en el KV Store).

Sin dependencias externas: usa únicamente la stdlib (urllib).

Uso:
    python src/scripts/ingest_openfang.py [--agent riopaila-institucional]
                                          [--max-files N] [--max-chars N]
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
KB_DIR = REPO_ROOT / "data" / "knowledge"
PDF_DIR = KB_DIR / "pdfs"
OPENFANG_URL = "http://127.0.0.1:4200/v1/chat/completions"
BATCH_DELAY = 0.5  # segundos entre documentos


def ingest_file(agent: str, path: Path, max_chars: int) -> bool:
    text = path.read_text(encoding="utf-8")[:max_chars]
    payload = {
        "model": f"openfang:{agent}",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Vas a recibir un documento corporativo de Riopaila Castilla. "
                    "Almacénalo en tu memoria (memory_store) por secciones para poder "
                    "recuperarlo después. Responde solo 'OK' cuando lo hayas memorizado."
                ),
            },
            {"role": "user", "content": f"Documento: {path.name}\n\n{text}"},
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OPENFANG_URL, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            json.loads(resp.read().decode("utf-8"))
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"  FALLO {path.name}: {exc}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", default="riopaila-institucional")
    parser.add_argument("--max-files", type=int, default=0, help="0 = todos")
    parser.add_argument("--max-chars", type=int, default=8000)
    args = parser.parse_args()

    files = [KB_DIR / "riopaila_castilla_clean.md"] + sorted(PDF_DIR.glob("*.md"))
    files = [f for f in files if f.exists()]
    if args.max_files:
        files = files[: args.max_files]

    print(f"Ingestando {len(files)} documentos en la memoria de '{args.agent}'...")
    ok = 0
    for f in files:
        if ingest_file(args.agent, f, args.max_chars):
            ok += 1
            print(f"  ✓ {f.name}")
        time.sleep(BATCH_DELAY)
    print(f"Documentos ingestados OK: {ok}/{len(files)}")


if __name__ == "__main__":
    main()
