#!/usr/bin/env python3
"""
Genera docs/INFORME_TECNICO_MODULO3.pdf desde el Markdown del informe.

Uso:
    python scripts/generate_informe_pdf.py
"""

from __future__ import annotations

import re
from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parent.parent
MD_PATH = ROOT / "docs" / "INFORME_TECNICO_MODULO3.md"
OUT_PATH = ROOT / "docs" / "INFORME_TECNICO_MODULO3.pdf"


def _ascii_safe(line: str) -> str:
    line = line.strip()
    line = re.sub(r"^#+\s*", "", line)
    line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
    line = re.sub(r"`([^`]+)`", r"\1", line)
    line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
    return line.encode("ascii", "replace").decode("ascii")


class InformePDF(FPDF):
    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Pagina {self.page_no()}", align="C")

    def write_line(self, text: str, *, bold: bool = False, size: int = 10) -> None:
        if not text:
            self.ln(3)
            return
        self.set_x(self.l_margin)
        w = self.w - self.l_margin - self.r_margin
        style = "B" if bold else ""
        self.set_font("Helvetica", style, size)
        self.multi_cell(w, 5, text)


def build_pdf() -> None:
    if not MD_PATH.is_file():
        raise FileNotFoundError(f"No existe {MD_PATH}")

    pdf = InformePDF()
    pdf.set_margins(18, 18, 18)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    in_code = False
    for raw in MD_PATH.read_text(encoding="utf-8").splitlines():
        if raw.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue

        line = _ascii_safe(raw)
        if not line or line.startswith("|") or line.replace("-", "").replace("|", "").strip() == "":
            continue

        if raw.startswith("# "):
            pdf.ln(4)
            pdf.write_line(line, bold=True, size=14)
            continue
        if raw.startswith("## "):
            pdf.ln(3)
            pdf.write_line(line, bold=True, size=12)
            continue
        if raw.startswith("- "):
            line = "- " + line.lstrip("- ")
        pdf.write_line(line)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUT_PATH))
    print(f"PDF generado: {OUT_PATH}")


if __name__ == "__main__":
    build_pdf()
