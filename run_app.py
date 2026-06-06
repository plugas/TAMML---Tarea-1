"""Lanzador de la app Streamlit. Ejecutar: python run_app.py  o  uv run app"""
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent
    app = root / "src" / "riopaila_rag" / "app.py"
    src = str(root / "src")
    env = os.environ.copy()
    prev = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src, prev]) if prev else src
    sys.exit(subprocess.call(["streamlit", "run", str(app)], env=env))


if __name__ == "__main__":
    main()
