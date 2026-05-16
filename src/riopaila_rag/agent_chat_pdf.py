"""Exporta el historial del Agente a PDF (evidencias / pruebas manuales)."""

from __future__ import annotations

import html as html_lib
import os
import re
from datetime import datetime
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import MethodReturnValue, XPos, YPos

from riopaila_rag.paths import ASSETS_DIR


# Verde institucional (alineado con la paleta Streamlit).
_C_BRAND_GREEN: tuple[int, int, int] = (27, 94, 32)
_LOGO_CANDIDATES: tuple[str, ...] = (
    "logo_riopaila.png",
    "logotipo_riopaila.png",
)
_LOGO_W_MAX_MM = 48.0
_LOGO_H_MAX_MM = 20.0


def _first_institutional_logo() -> Path | None:
    extra = os.environ.get("RIOPAILA_PDF_LOGO", "").strip()
    if extra:
        p = Path(extra).expanduser()
        if p.is_file():
            return p
    for name in _LOGO_CANDIDATES:
        p = ASSETS_DIR / name
        if p.is_file():
            return p
    return None


def _logo_dimensions_mm(path: Path, epw_mm: float) -> tuple[float, float]:
    """Ancho x alto en mm manteniendo proporción y dentro de límites razonables."""
    w_cap = min(_LOGO_W_MAX_MM, epw_mm * 0.52)
    try:
        from PIL import Image

        with Image.open(path) as im:
            pw, ph = im.size
        if pw <= 0 or ph <= 0:
            return (w_cap * 0.72, _LOGO_H_MAX_MM)
        ratio = pw / ph
        w_try = w_cap
        h_try = w_try / ratio
        if h_try > _LOGO_H_MAX_MM:
            h_try = _LOGO_H_MAX_MM
            w_try = h_try * ratio
        return (w_try, h_try)
    except Exception:
        return (w_cap * 0.75, _LOGO_H_MAX_MM * 0.5)


def _render_institutional_header(pdf: FPDF) -> None:
    """Cabecera con logotipo (si existe), nombre corporativo y regla institucional."""
    epw = pdf.epw
    lm = pdf.l_margin

    logo_path = _first_institutional_logo()
    y_top = pdf.get_y()

    if logo_path is not None:
        lw, lh = _logo_dimensions_mm(logo_path, epw)
        x_logo = lm + (epw - lw) / 2
        pdf.image(str(logo_path), x=x_logo, y=y_top, w=lw, h=lh)
        pdf.set_y(y_top + lh + 3)
    else:
        pdf.set_y(y_top + 0.5)

    pdf.set_font("ExportFont", style="B", size=12.5)
    pdf.set_text_color(*_C_BRAND_GREEN)
    pdf.cell(epw, 6.5, "Riopaila Castillo", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("ExportFont", style="", size=9.8)
    pdf.set_text_color(55, 71, 79)
    pdf.cell(
        epw,
        5.0,
        "Asistente corporativo — Conversación (Agente)",
        align="C",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    pdf.set_font("ExportFont", style="", size=8.8)
    pdf.set_text_color(90, 103, 113)
    pdf.cell(
        epw,
        4.3,
        "Preguntas y respuestas (vista para impresión / evidencias)",
        align="C",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    pdf.cell(
        epw,
        4.3,
        f"Documento generado: {ts}",
        align="C",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    pdf.set_text_color(0, 0, 0)
    pdf.ln(1)
    pdf.set_draw_color(*_C_BRAND_GREEN)
    pdf.set_line_width(0.45)
    yy = pdf.get_y()
    pdf.line(lm, yy, lm + epw, yy)
    pdf.set_line_width(0.2)
    pdf.set_draw_color(200, 210, 216)
    pdf.set_y(yy + 2.5)


def _font_candidates() -> list[Path]:
    home = Path.home()
    return [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\calibri.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
        Path("/usr/share/fonts/TTF/DejaVuSans.ttf"),
        home / "Library/Fonts/Arial.ttf",
        home / "Library/Fonts/Arial Unicode.ttf",
    ]


def _pick_font_path() -> Path | None:
    extra = os.environ.get("RIOPAILA_EXPORT_PDF_FONT", "").strip()
    if extra:
        p = Path(extra).expanduser()
        if p.is_file():
            return p
    for p in _font_candidates():
        if p.is_file():
            return p
    return None


def _strip_basic_html(s: str) -> str:
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"<[^>]+>", "", s)
    return html_lib.unescape(s)


_RE_PICTURE = re.compile(
    r"(?:\*\*)?\s*-{3,}\s*Start of picture text\s*-{3,}\s*(?:\*\*)?"
    r".*?"
    r"(?:\*\*)?\s*-{3,}\s*End of picture text\s*-{3,}\s*(?:\*\*)?",
    re.DOTALL | re.IGNORECASE,
)


def _strip_noise_blocks(s: str) -> str:
    # No dejar marcador en PDF: se elimina el bloque OCR/tabla incrustada.
    return _RE_PICTURE.sub("\n", s)


def _remove_pipe_table_blocks(text: str) -> str:
    """Elimina por completo bloques de líneas tipo tabla markdown (|)."""
    lines = text.splitlines()
    res: list[str] = []
    i = 0
    while i < len(lines):
        if lines[i].count("|") >= 2:
            while i < len(lines) and lines[i].count("|") >= 2:
                i += 1
        else:
            res.append(lines[i])
            i += 1
    return "\n".join(res)


_RE_FUENTES_HEAD = re.compile(
    r"(?is)(?:^|\n)[ \t]*(?:#{1,6}[ \t]+)?(?:\*\*)?[ \t]*Fuentes\b"
)
_RE_REFERENCIAS_HEAD = re.compile(
    r"(?is)(?:^|\n)[ \t]*(?:#{1,6}[ \t]+)?(?:\*\*)?[ \t]*Referencias\b"
)


def _cut_from_regex(s: str, rx: re.Pattern[str]) -> str:
    m = rx.search(s)
    return (s[: m.start()].strip() if m else s).strip()


def _strip_assistant_evidence_for_pdf(s: str) -> str:
    """Quita del texto del asistente citas, metadatos RAG y eco de herramientas (solo exportación PDF)."""
    if not (s or "").strip():
        return s
    # Secciones finales típicas
    for rx in (_RE_FUENTES_HEAD, _RE_REFERENCIAS_HEAD):
        s = _cut_from_regex(s, rx)
    s = re.split(
        r"(?is)(?:^|\n)\s*Herramientas y evidencias recuperadas\s*$",
        s,
        maxsplit=1,
    )[0]
    s = re.split(
        r"(?is)(?:^|\n)\s*Herramientas\s*/\s*fuentes\s*:?\s*$",
        s,
        maxsplit=1,
    )[0]
    s = re.split(
        r"(?is)(?:^|\n)\s*Resultado recuperado \(recorte\)\s*:\s*",
        s,
        maxsplit=1,
    )[0]
    # Encabezados de bloque estructurado (company_info pegado al final)
    for sec in (
        "LEGAL",
        "CERTIFICACIONES",
        "CONTACTO",
        "ORGANIZACION",
        "GOBIERNO",
    ):
        s = re.split(rf"(?m)^[ \t]*{re.escape(sec)}[ \t]*$", s, maxsplit=1)[0].strip()

    lines_out: list[str] = []
    for raw in s.splitlines():
        ln = raw.rstrip()
        st = ln.strip()
        if not st:
            lines_out.append("")
            continue
        if st.startswith("[Fuente:"):
            continue
        if "[Fuente:" in ln:
            ln2 = re.sub(r"\[Fuente:[^\]]*\]", " ", ln)
            ln2 = re.sub(r"\s+", " ", ln2).strip()
            if not ln2:
                continue
            lines_out.append(ln2)
            continue
        if "omitida en PDF" in ln and ("Tabla" in ln or "[" in ln):
            continue
        if "[Ficha de tabla" in ln or "tabla/imagen omitida" in ln:
            continue
        if re.match(
            r"^\s*(?:•\s*)?(?:rag_search|company_info_search)\s*$",
            ln,
            re.I,
        ):
            continue
        if re.search(r"argumentos\s*:\s*\{", ln, re.I):
            continue
        if re.search(r"Similitud\s*:", ln, re.I) and "|" not in ln:
            continue
        if re.fullmatch(r"\s*•\s*-\s*", ln):
            continue
        if ln.count("|") >= 3:
            continue
        # Campos tipo company_info (snake_case / nit)
        if re.match(r"(?i)^\s*[a-z][a-z0-9_]*_[a-z0-9_]+\s*:", ln):
            continue
        if re.match(r"(?i)^\s*nit\s*:", ln):
            continue
        lines_out.append(ln.rstrip())

    s = "\n".join(lines_out)
    s = re.sub(r"(?i)\bpágina\s*\d+\s*/\s*\d+\b", "", s)
    return _normalize_paragraph_spaces(s)


def format_chat_content_for_pdf(
    s: str,
    *,
    assistant_mode: bool = False,
) -> str:
    """Legibilidad en papel. ``assistant_mode`` elimina citas/tablas tipo RAG del mensaje."""
    s = _strip_basic_html(s)
    s = _strip_noise_blocks(s)
    # Guiones pegados antes de otro elemento en negrita ("Capurro- **Nombre**").
    s = re.sub(r"(?<=\S)-\s*\*\*", r"\n\n- **", s)
    lines = [_strip_md_headers_line(ln).rstrip() for ln in s.splitlines()]
    s = "\n".join(lines)
    s = _strip_bold_pairs(s)
    s = _split_glued_sections(s)
    if assistant_mode:
        s = _remove_pipe_table_blocks(s)
    else:
        s = _collapse_pipe_tables(s, min_rows=8)
    s = _normalize_list_hyphens(s)
    s = _normalize_paragraph_spaces(s)
    if assistant_mode:
        s = _strip_assistant_evidence_for_pdf(s)
        # Texto más continuo en el PDF (menos párrafos vacíos intermedios).
        s = re.sub(r"\n\s*\n+", "\n", (s or "").strip())
        s = re.sub(r"\n{3,}", "\n", s)
    return s


def _strip_md_headers_line(line: str) -> str:
    return re.sub(r"^#{1,6}\s+", "", line)


def _strip_bold_pairs(s: str) -> str:
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
        s = re.sub(r"\*([^*\n]+)\*", r"\1", s)
    return s


def _is_markdown_table_separator(line: str) -> bool:
    inner = line.replace("|", "").strip()
    return bool(inner) and set(inner) <= {"-", ":"} and "-" in inner


def _collapse_pipe_tables(text: str, *, min_rows: int) -> str:
    """Convierte bloques tipo tabla markdown (muchas '|') en un aviso corto."""
    lines = text.splitlines()
    res: list[str] = []
    i = 0
    while i < len(lines):
        if lines[i].count("|") >= 2:
            start = i
            while i < len(lines) and lines[i].count("|") >= 2:
                i += 1
            run_len = i - start
            if run_len >= min_rows:
                res.append(
                    f"[Tabla de {run_len} filas omitida en PDF; "
                    "véase la conversación en la aplicación.]"
                )
            else:
                # Tabla corta: dejar más legible reemplazando pipes por bullets por fila
                for ln in lines[start:i]:
                    if _is_markdown_table_separator(ln):
                        continue
                    cells = [c.strip() for c in ln.split("|") if c.strip()]
                    if cells:
                        res.append(" · ".join(cells))
                    else:
                        res.append(ln)
        else:
            res.append(lines[i])
            i += 1
    return "\n".join(res)


def _normalize_list_hyphens(s: str) -> str:
    lines_out: list[str] = []
    for line in s.splitlines():
        raw = line.rstrip()
        indent = len(raw) - len(raw.lstrip())
        ind = " " * indent
        st = raw.lstrip()
        if st.startswith(("- ", "* ")):
            core = st[2:].lstrip()
            lines_out.append(f"{ind}• {core}")
        elif len(st) > 1 and st[0] == "-" and st[1] != " ":
            # viñeta sin espacio tras el guion: "-nombre" o "- **..."
            lines_out.append(f"{ind}• {st[1:].lstrip()}")
        else:
            lines_out.append(raw)
    return "\n".join(lines_out)


def _normalize_paragraph_spaces(s: str) -> str:
    s = re.sub(r"[ \t]+$", "", s, flags=re.MULTILINE)
    s = re.sub(r"[ \t]{2,}", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def _split_glued_sections(s: str) -> str:
    """Separa tramos pegados como 'Fuentes - siguiente' cuando el modelo no pone salto."""
    return re.sub(r"(?i)(Referencias|Fuentes)\s*-\s*", r"\1 -\n\n", s)


class _ExportPDF(FPDF):
    def footer(self) -> None:
        try:
            self.set_font("ExportFont", "", 8)
        except Exception:
            self.set_font("Helvetica", "", 8)
        self.set_text_color(100, 100, 100)
        self.set_y(-12)
        self.cell(0, 8, f"Página {self.page_no()}/{{nb}}", align="C")
        self.set_text_color(0, 0, 0)


# Tarjetas con color (mejor lectura). Si un turno supera el alto útil de una página,
# se usa el layout compacto sólo en ese caso extremo.
_CARD_PAD_X = 4.2
_CARD_PAD_Y = 3.8
_CARD_GAP_ROLE_BODY = 2.2
_CARD_BELOW = 5.2
_CARD_OUTER_X = 1.0
_CARD_STRIPE_W = 3.2
_FOOTER_SLACK_MM = 17.0


def _render_turn_compact(
    pdf: FPDF,
    *,
    role: str,
    fallback_label: str,
    body_text: str,
    margin_body: float,
    body_ln: float,
    body_size: float,
    index: int,
) -> None:
    """Reserva para turnos demasiado altos para un solo recuadro (evita fondos cortados)."""
    if role == "user":
        chip = "Pregunta"
        title_rgb = (21, 71, 26)
    elif role == "assistant":
        chip = "Respuesta"
        title_rgb = (43, 53, 61)
    else:
        chip = fallback_label or "Mensaje"
        title_rgb = (54, 62, 71)

    if index > 0:
        pdf.ln(2.6)

    txt = (body_text if (body_text or "").strip() else " ").strip("\n")

    pdf.set_font("ExportFont", style="B", size=11.0)
    pdf.set_text_color(*title_rgb)
    pdf.multi_cell(
        margin_body,
        5.0,
        chip,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.ln(0.6)

    pdf.set_font("ExportFont", style="", size=body_size)
    pdf.set_text_color(36, 44, 52)
    pdf.multi_cell(
        margin_body,
        body_ln,
        txt,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.set_text_color(0, 0, 0)


def _render_message_card(
    pdf: FPDF,
    *,
    role: str,
    fallback_label: str,
    body_text: str,
    margin_body: float,
    body_ln: float,
    body_size: float,
    turn_index: int,
) -> None:
    """Turno como recuadro con fondo suave y franja de color (identidad visual)."""
    if role == "user":
        chip = "Pregunta"
        fill_rgb = (236, 246, 239)
        stripe_rgb = _C_BRAND_GREEN
        title_rgb = (21, 71, 26)
        border_rgb = (196, 212, 199)
    elif role == "assistant":
        chip = "Respuesta"
        fill_rgb = (243, 246, 251)
        stripe_rgb = (71, 94, 109)
        title_rgb = (43, 53, 61)
        border_rgb = (207, 216, 226)
    else:
        chip = fallback_label or "Mensaje"
        fill_rgb = (249, 250, 251)
        stripe_rgb = (120, 126, 134)
        title_rgb = (54, 62, 71)
        border_rgb = (222, 224, 228)

    inner_w = margin_body - 2 * _CARD_PAD_X
    x_text = pdf.l_margin + _CARD_PAD_X
    text_for_body = body_text if (body_text or "").strip() else " "

    ym = pdf.get_y()
    pdf.set_xy(x_text, ym)

    pdf.set_font("ExportFont", style="B", size=11.2)
    h_title = pdf.multi_cell(
        inner_w,
        6.4,
        chip,
        new_x=XPos.LEFT,
        new_y=YPos.NEXT,
        dry_run=True,
        output=MethodReturnValue.HEIGHT,
    )
    pdf.set_font("ExportFont", style="", size=body_size)
    h_body = pdf.multi_cell(
        inner_w,
        body_ln,
        text_for_body,
        new_x=XPos.LEFT,
        new_y=YPos.NEXT,
        dry_run=True,
        output=MethodReturnValue.HEIGHT,
    )

    card_h = (
        _CARD_PAD_Y
        + h_title
        + _CARD_GAP_ROLE_BODY
        + h_body
        + _CARD_PAD_Y
        + 0.5
    )

    y0 = pdf.get_y()
    full_usable = (
        pdf.h - pdf.t_margin - pdf.b_margin - _FOOTER_SLACK_MM - 2.0
    )
    if card_h > full_usable:
        _render_turn_compact(
            pdf,
            role=role,
            fallback_label=fallback_label,
            body_text=text_for_body,
            margin_body=margin_body,
            body_ln=body_ln,
            body_size=body_size,
            index=turn_index,
        )
        return

    avail_here = pdf.h - pdf.b_margin - _FOOTER_SLACK_MM - y0
    if card_h > avail_here:
        pdf.add_page()
        y0 = pdf.get_y()
        avail_here = pdf.h - pdf.b_margin - _FOOTER_SLACK_MM - y0
        if card_h > avail_here:
            _render_turn_compact(
                pdf,
                role=role,
                fallback_label=fallback_label,
                body_text=text_for_body,
                margin_body=margin_body,
                body_ln=body_ln,
                body_size=body_size,
                index=turn_index,
            )
            return

    x_card = pdf.l_margin - _CARD_OUTER_X
    w_card = margin_body + 2 * _CARD_OUTER_X

    pdf.set_fill_color(*fill_rgb)
    pdf.rect(x_card, y0, w_card, card_h, style="F")

    pdf.set_fill_color(*stripe_rgb)
    pdf.rect(x_card, y0, _CARD_STRIPE_W, card_h, style="F")

    pdf.set_draw_color(*border_rgb)
    pdf.set_line_width(0.2)
    pdf.rect(x_card, y0, w_card, card_h, style="D")

    pdf.set_xy(x_text, y0 + _CARD_PAD_Y)
    pdf.set_text_color(*title_rgb)
    pdf.set_font("ExportFont", style="B", size=11.2)
    pdf.multi_cell(inner_w, 6.4, chip, new_x=XPos.LEFT, new_y=YPos.NEXT)

    pdf.set_text_color(36, 44, 52)
    pdf.set_font("ExportFont", style="", size=body_size)
    pdf.multi_cell(inner_w, body_ln, text_for_body, new_x=XPos.LEFT, new_y=YPos.NEXT)

    pdf.set_text_color(0, 0, 0)
    pdf.set_y(y0 + card_h + _CARD_BELOW)


def build_agent_chat_pdf_bytes(historial: list[dict]) -> bytes:
    """Construye el PDF como bytes UTF-8 (requiere una fuente .ttf en el sistema
    o la variable ``RIOPAILA_EXPORT_PDF_FONT``).
    """
    pdf = _ExportPDF()
    pdf.alias_nb_pages()
    pdf.set_margins(16, 12, 16)
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()

    font_path = _pick_font_path()
    if font_path is None:
        raise RuntimeError(
            "No se encontró ninguna fuente TrueType para el PDF "
            "(español y símbolos). Instala DejaVu o define RIOPAILA_EXPORT_PDF_FONT "
            "con la ruta a un archivo .ttf."
        )

    pdf.add_font("ExportFont", "", str(font_path))
    pdf.add_font("ExportFont", style="B", fname=str(font_path))

    _render_institutional_header(pdf)

    margin_body = pdf.epw
    body_ln = 5.35
    body_size = 10.4

    for i, msg in enumerate(historial):
        role = msg.get("role") or ""
        raw_content = msg.get("content") or ""
        fallback = {"user": "Usuario", "assistant": "Asistente"}.get(role, role or "Mensaje")

        cleaned = format_chat_content_for_pdf(
            str(raw_content),
            assistant_mode=(role == "assistant"),
        )

        _render_message_card(
            pdf,
            role=role,
            fallback_label=fallback,
            body_text=cleaned if cleaned else " ",
            margin_body=margin_body,
            body_ln=body_ln,
            body_size=body_size,
            turn_index=i,
        )

    out = pdf.output()
    if out is None:
        return b""
    return bytes(out)
