"""Lanzador de la app Streamlit. Ejecutar: python run_app.py  o  uv run app"""
import subprocess
import sys
from pathlib import Path


def main() -> None:
    app = Path(__file__).parent / "src" / "riopaila_rag" / "app.py"
    sys.exit(subprocess.call(["streamlit", "run", str(app)]))


if __name__ == "__main__":
    main()
