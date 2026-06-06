"""
Pipeline de ingestión: Markdown -> chunks -> embeddings -> Supabase.

Lee riopaila_castilla_clean.md y todos los PDFs convertidos en
data/knowledge/pdfs/, los divide en chunks semánticos, genera
embeddings con OpenAI y los sube a la tabla `documents` en Supabase.

Uso:
    uv run python -m riopaila_rag.ingest
    make ingest
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from openai import OpenAI
from supabase import create_client

from riopaila_rag.chunking import Chunk, chunk_file
from riopaila_rag.config import (
    CHUNK_SIZE,
    EMBEDDING_MODEL,
    KNOWLEDGE_FILE,
    OPENAI_API_KEY,
    SUPABASE_KEY,
    SUPABASE_URL,
    check_openai,
    check_supabase,
)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

BATCH_SIZE = 100  # chunks por llamada a la API de embeddings
PDF_DIR = KNOWLEDGE_FILE.parent / "pdfs"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _collect_files() -> list[Path]:
    """Devuelve todos los .md a ingestar: KB principal + PDFs convertidos."""
    files: list[Path] = []

    if KNOWLEDGE_FILE.exists():
        files.append(KNOWLEDGE_FILE)
    else:
        print(f"WARN  Archivo principal no encontrado: {KNOWLEDGE_FILE}")

    if PDF_DIR.exists():
        files.extend(sorted(PDF_DIR.glob("*.md")))

    return files


def _embed_batch(client: OpenAI, texts: list[str]) -> list[list[float]]:
    """Llama a la API de OpenAI y retorna los vectores para un lote."""
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def _upload_batch(
    supabase,
    chunks: list[Chunk],
    embeddings: list[list[float]],
) -> None:
    """Inserta un lote de chunks + embeddings en la tabla documents."""
    rows = [
        {
            "content": chunk.content,
            "metadata": chunk.metadata,
            "embedding": embedding,
        }
        for chunk, embedding in zip(chunks, embeddings)
    ]
    supabase.table("documents").insert(rows).execute()


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def ingest(force: bool = False) -> None:
    """
    Ejecuta el pipeline completo de ingestión.

    Borra todos los documentos existentes en Supabase y re-ingesta
    desde cero. Si force=False, pide confirmación interactiva primero.
    """
    check_openai()
    check_supabase()

    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # 1. Recopilar archivos
    files = _collect_files()
    if not files:
        print("ERROR No se encontraron archivos .md para ingestar.")
        sys.exit(1)

    print(f"\nArchivos a ingestar: {len(files)}")
    for f in files:
        print(f"  - {f.name}")

    # 2. Confirmación
    if not force:
        print(
            "\nEsto borrara todos los documentos existentes en Supabase y "
            "re-indexara todo desde cero."
        )
        resp = input("Continuar? [s/N] ").strip().lower()
        if resp not in ("s", "si", "sí", "y", "yes"):
            print("Cancelado.")
            return

    # 3. Limpiar tabla (en lotes para evitar timeout de Supabase con tablas grandes)
    print("\nLimpiando tabla documents...")
    total_borrados = 0
    while True:
        # Trae 500 ids, los borra, repite hasta que no haya más
        batch = supabase.table("documents").select("id").limit(500).execute()
        if not batch.data:
            break
        ids = [row["id"] for row in batch.data]
        supabase.table("documents").delete().in_("id", ids).execute()
        total_borrados += len(ids)
        print(f"  Borrados {total_borrados} chunks…", flush=True)
    print(f"  OK tabla limpia ({total_borrados} filas eliminadas)")

    # 4. Chunking
    print(f"\nGenerando chunks (chunk_size={CHUNK_SIZE})...")
    all_chunks: list[Chunk] = []
    for f in files:
        file_chunks = chunk_file(f, chunk_size=CHUNK_SIZE)
        all_chunks.extend(file_chunks)
        print(f"  {f.name}: {len(file_chunks)} chunks")

    print(f"\nTotal: {len(all_chunks)} chunks")

    # 5. Embeddings + upload por batches
    print(f"\nGenerando embeddings y subiendo a Supabase (batch={BATCH_SIZE})...")
    total_batches = (len(all_chunks) + BATCH_SIZE - 1) // BATCH_SIZE
    uploaded = 0

    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch_chunks = all_chunks[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        # Enriquecemos el texto a embedder con metadata de contexto
        # (documento + sección) para que el embedding capture mejor de qué
        # trata el chunk. Crítico para chunks tabulares con poca prosa.
        # El campo `content` que se guarda en BD permanece igual; solo el
        # texto que va al modelo de embeddings se enriquece.
        texts = [
            f"Documento: {c.metadata.get('fuente', 'desconocido')}\n"
            f"Sección: {c.metadata.get('seccion', 'sin sección')}\n\n"
            f"{c.content}"
            for c in batch_chunks
        ]

        print(
            f"  Batch {batch_num}/{total_batches} "
            f"({len(batch_chunks)} chunks)...",
            end=" ",
            flush=True,
        )

        embeddings = _embed_batch(openai_client, texts)
        _upload_batch(supabase, batch_chunks, embeddings)
        uploaded += len(batch_chunks)
        print(f"OK ({uploaded}/{len(all_chunks)})")

        # Pausa breve para no saturar rate-limits de OpenAI
        if i + BATCH_SIZE < len(all_chunks):
            time.sleep(0.3)

    print(f"\nIngestión completada.")
    print(f"  Chunks subidos : {uploaded}")
    print(f"  Modelo         : {EMBEDDING_MODEL}")
    print(f"  Tabla          : documents")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingestión RAG -> Supabase")
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Salta la confirmacion interactiva",
    )
    args = parser.parse_args()

    ingest(force=args.force)
