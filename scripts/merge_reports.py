"""
Consolida todos los reportes de scraping en un único archivo Markdown de conocimiento.
Entrada : reports/*.md
Salida  : data/knowledge/riopaila_castilla.md
"""
from pathlib import Path

ROOT = Path(__file__).parent.parent
REPORTS_DIR = ROOT / "reports"
OUTPUT_FILE = ROOT / "data" / "knowledge" / "riopaila_castilla.md"

ARCHIVOS_INSUMO = [
    "reporte_web_riopaila.md",
    "reporte_linkedin_posts_riopaila.md",
    "reporte_simev_riopaila.md",
    "reporte_instagram_posts_riopaila.md",
]


def consolidar_contexto():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as salida:
        salida.write("# Base de Conocimiento — Riopaila Castilla\n\n")
        for nombre in ARCHIVOS_INSUMO:
            ruta = REPORTS_DIR / nombre
            if ruta.exists():
                salida.write(f"---\n\n")
                salida.write(ruta.read_text(encoding="utf-8"))
                salida.write("\n")
                print(f"Agregado: {nombre}")
            else:
                print(f"Advertencia: No se encontró {ruta}")

    print(f"\nArchivo consolidado generado: {OUTPUT_FILE}")


if __name__ == "__main__":
    consolidar_contexto()
