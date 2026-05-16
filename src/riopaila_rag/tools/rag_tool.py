"""
Tool RAG: búsqueda semántica en la tabla `documents` de Supabase.

Convierte la pregunta del usuario en un embedding y llama a
match_documents() para obtener los chunks más relevantes.
El agente usa esta tool para preguntas narrativas sobre Riopaila Castilla.
"""

from __future__ import annotations

from langchain_core.tools import tool
from openai import OpenAI

from riopaila_rag.config import (
    EMBEDDING_MODEL,
    OPENAI_API_KEY,
    RAG_TOP_K,
    SUPABASE_KEY,
    SUPABASE_URL,
)

_openai = OpenAI(api_key=OPENAI_API_KEY)

try:
    from supabase import create_client as _create_client
    _supabase = _create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    _supabase = None


def _embed_query(text: str) -> list[float]:
    response = _openai.embeddings.create(model=EMBEDDING_MODEL, input=[text])
    return response.data[0].embedding


@tool
def rag_search(query: str) -> str:
    """
    Busca información narrativa sobre Riopaila Castilla en la base de conocimiento.

    Usa esta herramienta para responder preguntas sobre historia, operaciones,
    sostenibilidad, productos, certificaciones, informes financieros, estrategia
    corporativa, gobierno corporativo o cualquier tema general de la empresa.

    Para integrantes de la **Junta Directiva** (principales y suplentes), formula
    la consulta de forma explícita: incluye términos como "Junta Directiva",
    "integrantes", "principales", "suplentes", "2026", "2027", "nombramiento",
    porque otros documentos mencionan la JD en genérico y pueden ganar similitud
    si la consulta es demasiado vaga.

    Args:
        query: Pregunta o tema a buscar en la base de conocimiento.

    Returns:
        Fragmentos de texto relevantes con su sección de origen.
    """
    if _supabase is None:
        return "Error: cliente Supabase no disponible."

    embedding = _embed_query(query)

    result = _supabase.rpc(
        "match_documents",
        {
            "query_embedding": embedding,
            "match_count": RAG_TOP_K,
            "filter": {},
        },
    ).execute()

    if not result.data:
        return "No se encontró información relevante para esa consulta."

    fragments = []
    for row in result.data:
        meta = row.get("metadata", {}) or {}
        seccion = meta.get("seccion", "sin sección")
        fuente = meta.get("fuente", "desconocida")
        posicion = meta.get("posicion", -1)
        total = meta.get("total_chunks", -1)
        similarity = row.get("similarity", 0)
        content = row.get("content", "").strip()
        fragments.append(
            f"[Fuente: {fuente} | Sección: {seccion} | "
            f"Fragmento: {posicion + 1}/{total} | "
            f"Similitud: {similarity:.2f}]\n{content}"
        )

    return "\n\n---\n\n".join(fragments)
