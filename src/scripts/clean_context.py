"""
Limpia el archivo de conocimiento Markdown eliminando ruido sin romper la estructura.
Entrada : data/knowledge/riopaila_castilla.md
Salida  : data/knowledge/riopaila_castilla_clean.md
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
INPUT_FILE = ROOT / "data" / "knowledge" / "riopaila_castilla.md"
OUTPUT_FILE = ROOT / "data" / "knowledge" / "riopaila_castilla_clean.md"


def limpiar_contexto():
    if not INPUT_FILE.exists():
        print(f"Error: No se encontro {INPUT_FILE}")
        return

    texto = INPUT_FILE.read_text(encoding="utf-8")

    # Eliminar URLs sueltas (no las que están dentro de sintaxis Markdown [texto](url))
    texto = re.sub(r'(?<!\()https?://\S+(?!\))', '', texto)

    # Normalizar saltos de línea excesivos (más de 2 consecutivos -> 2)
    texto = re.sub(r'\n{3,}', '\n\n', texto)

    # Eliminar espacios al final de línea
    texto = re.sub(r'[ \t]+$', '', texto, flags=re.MULTILINE)

    OUTPUT_FILE.write_text(texto, encoding="utf-8")
    print(f"Contexto limpio guardado en: {OUTPUT_FILE}")


if __name__ == "__main__":
    limpiar_contexto()
