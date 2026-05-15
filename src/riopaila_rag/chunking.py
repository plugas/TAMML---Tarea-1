"""
Chunking manual basado en estructura semantica del Markdown.

Estrategia jerarquica:
  1. Divide por encabezados (## y ###) preservando secciones completas.
  2. Si una seccion excede chunk_size, divide por parrafos (doble salto de linea).
  3. Si un parrafo aun excede, divide por oraciones con overlap del 20%.

Cada chunk lleva metadata: {seccion, fuente, posicion, total_chunks}.

Uso:
    from riopaila_rag.chunking import chunk_file, Chunk
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from riopaila_rag.config import CHUNK_SIZE


@dataclass
class Chunk:
    content: str
    metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _overlap_size(chunk_size: int) -> int:
    """Overlap = 20% del chunk_size."""
    return max(0, int(chunk_size * 0.20))


def _split_by_sentences(text: str, chunk_size: int) -> list[str]:
    """
    Divide texto largo en fragmentos respetando oraciones.
    Aplica overlap del 20% para no perder contexto en los bordes.
    """
    overlap = _overlap_size(chunk_size)
    # Separar por punto, signo de exclamacion o interrogacion seguido de espacio/newline
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if current_len + len(sentence) + 1 > chunk_size and current:
            chunk_text = " ".join(current).strip()
            if chunk_text:
                chunks.append(chunk_text)

            # Overlap: mantener ultimas oraciones que quepan en `overlap` chars
            overlap_sentences: list[str] = []
            overlap_len = 0
            for s in reversed(current):
                if overlap_len + len(s) + 1 <= overlap:
                    overlap_sentences.insert(0, s)
                    overlap_len += len(s) + 1
                else:
                    break
            current = overlap_sentences
            current_len = overlap_len

        current.append(sentence)
        current_len += len(sentence) + 1

    if current:
        chunk_text = " ".join(current).strip()
        if chunk_text:
            chunks.append(chunk_text)

    return chunks


def _split_by_paragraphs(text: str, chunk_size: int) -> list[str]:
    """
    Divide por parrafos. Si un parrafo sigue siendo grande, baja a nivel de oraciones.
    Aplica overlap del 20% entre chunks de parrafos.
    """
    overlap = _overlap_size(chunk_size)
    paragraphs = [p.strip() for p in re.split(r'\n\n+', text) if p.strip()]

    chunks: list[str] = []
    current_parts: list[str] = []
    current_len = 0

    for para in paragraphs:
        # Parrafo individual mas grande que chunk_size -> bajar a oraciones
        if len(para) > chunk_size:
            # Primero vaciar lo acumulado
            if current_parts:
                chunks.append("\n\n".join(current_parts).strip())
                # Overlap: ultimo parrafo acumulado si cabe
                last = current_parts[-1]
                current_parts = [last] if len(last) <= overlap else []
                current_len = len(current_parts[0]) if current_parts else 0

            # Luego dividir el parrafo grande por oraciones
            chunks.extend(_split_by_sentences(para, chunk_size))
            continue

        if current_len + len(para) + 2 > chunk_size and current_parts:
            chunks.append("\n\n".join(current_parts).strip())
            # Overlap con el ultimo parrafo si cabe
            last = current_parts[-1]
            current_parts = [last] if len(last) <= overlap else []
            current_len = len(current_parts[0]) if current_parts else 0

        current_parts.append(para)
        current_len += len(para) + 2

    if current_parts:
        chunks.append("\n\n".join(current_parts).strip())

    return [c for c in chunks if c.strip()]


def _extraer_secciones(text: str) -> list[tuple[str, str]]:
    """
    Divide el texto en secciones segun encabezados ## y ###.
    Retorna lista de (titulo_seccion, contenido).
    """
    patron = re.compile(r'^(#{1,3})\s+(.+)$', re.MULTILINE)
    matches = list(patron.finditer(text))

    if not matches:
        return [("documento", text)]

    secciones: list[tuple[str, str]] = []

    # Contenido antes del primer encabezado
    if matches[0].start() > 0:
        contenido_inicial = text[:matches[0].start()].strip()
        if contenido_inicial:
            secciones.append(("inicio", contenido_inicial))

    for i, match in enumerate(matches):
        titulo = match.group(2).strip()
        inicio_contenido = match.end()
        fin_contenido = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        contenido = text[inicio_contenido:fin_contenido].strip()
        if contenido:
            secciones.append((titulo, contenido))

    return secciones


# ---------------------------------------------------------------------------
# API publica
# ---------------------------------------------------------------------------

def chunk_text(
    text: str,
    source: str = "desconocido",
    chunk_size: int = CHUNK_SIZE,
) -> list[Chunk]:
    """
    Divide texto Markdown en chunks semanticos con metadata.

    Args:
        text:       Texto en formato Markdown.
        source:     Nombre del archivo fuente (para metadata).
        chunk_size: Tamano maximo de cada chunk en caracteres.

    Returns:
        Lista de Chunk con content y metadata.
    """
    secciones = _extraer_secciones(text)
    chunks_raw: list[tuple[str, str]] = []  # (seccion, texto_chunk)

    for titulo, contenido in secciones:
        if len(contenido) <= chunk_size:
            chunks_raw.append((titulo, contenido))
        else:
            sub_chunks = _split_by_paragraphs(contenido, chunk_size)
            for sc in sub_chunks:
                chunks_raw.append((titulo, sc))

    total = len(chunks_raw)
    result: list[Chunk] = []
    for pos, (seccion, contenido) in enumerate(chunks_raw):
        result.append(Chunk(
            content=contenido,
            metadata={
                "seccion": seccion,
                "fuente": source,
                "posicion": pos,
                "total_chunks": total,
                "chunk_size_config": chunk_size,
                "overlap_config": _overlap_size(chunk_size),
            },
        ))

    return result


def chunk_file(path: Path, chunk_size: int = CHUNK_SIZE) -> list[Chunk]:
    """
    Lee un archivo Markdown y lo divide en chunks semanticos.

    Args:
        path:       Ruta al archivo .md
        chunk_size: Tamano maximo de cada chunk en caracteres.

    Returns:
        Lista de Chunk listos para generar embeddings.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    return chunk_text(text, source=path.name, chunk_size=chunk_size)
