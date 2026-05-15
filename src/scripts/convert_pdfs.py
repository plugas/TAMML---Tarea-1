"""
Convierte todos los PDFs en data/pdfs/ a Markdown en data/knowledge/pdfs/.
Usa pymupdf4llm que preserva tablas, encabezados y estructura del documento.

Uso:
    uv run python src/scripts/convert_pdfs.py
    make convert-pdfs
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pymupdf4llm

ROOT = Path(__file__).parent.parent.parent
PDF_DIR = ROOT / "data" / "pdfs"
OUT_DIR = ROOT / "data" / "knowledge" / "pdfs"


def limpiar_texto(texto: str, nombre_pdf: str) -> str:
    """Limpia artefactos comunes de la conversion PDF -> MD."""
    # Quitar caracteres corruptos de encoding
    texto = re.sub(r"[^\x00-\x7FÀ-ɏ -ÿ]+", " ", texto)

    # Quitar líneas de imágenes omitidas
    texto = re.sub(r"\*\*==> picture \[.*?\] intentionally omitted <==\*\*\n?", "", texto)

    # Normalizar saltos de línea excesivos
    texto = re.sub(r"\n{3,}", "\n\n", texto)

    # Encabezado con nombre del archivo fuente
    encabezado = f"# {nombre_pdf}\n\n> Fuente: data/pdfs/{nombre_pdf}.pdf\n\n---\n\n"
    return encabezado + texto.strip()


def convertir_pdf(pdf_path: Path) -> Path:
    """Convierte un PDF a Markdown y lo guarda en OUT_DIR."""
    nombre = pdf_path.stem
    out_path = OUT_DIR / f"{nombre}.md"

    print(f"  Convirtiendo: {pdf_path.name} ...", end=" ", flush=True)
    try:
        md_raw = pymupdf4llm.to_markdown(str(pdf_path))
        md_limpio = limpiar_texto(md_raw, nombre)
        out_path.write_text(md_limpio, encoding="utf-8")
        kb = len(md_limpio) // 1024
        print(f"OK ({kb} KB -> {out_path.name})")
        return out_path
    except Exception as e:
        print(f"ERROR: {e}")
        raise


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No se encontraron PDFs en {PDF_DIR}")
        sys.exit(1)

    print(f"\nConvirtiendo {len(pdfs)} PDFs -> {OUT_DIR}\n")
    exitosos = 0
    fallidos: list[str] = []

    for pdf in pdfs:
        try:
            convertir_pdf(pdf)
            exitosos += 1
        except Exception:
            fallidos.append(pdf.name)

    print(f"\nOK {exitosos}/{len(pdfs)} convertidos exitosamente -> {OUT_DIR}")
    if fallidos:
        print(f"FAIL Fallidos: {', '.join(fallidos)}")
    else:
        print("  Ejecuta 'make ingest' para indexar todo en Supabase.")


if __name__ == "__main__":
    main()
