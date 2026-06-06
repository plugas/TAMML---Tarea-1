"""
Tool RAG: búsqueda semántica con esquema Pydantic (Function Calling, Módulo 3).
"""

from __future__ import annotations

from langchain_core.tools import StructuredTool

from riopaila_rag.rag_store import similarity_search
from riopaila_rag.schemas import RagSearchInput
from riopaila_rag.tool_errors import tool_failure_message


def _rag_search_impl(query: str) -> str:
    try:
        hits = similarity_search(query)
    except Exception as exc:
        return tool_failure_message(f"error al consultar documentos: {exc}")

    if not hits:
        return tool_failure_message("no hay fragmentos relevantes para esa consulta")

    fragments = []
    for content, meta, similarity in hits:
        seccion = meta.get("seccion", "sin sección")
        fuente = meta.get("fuente", "desconocida")
        posicion = meta.get("posicion", -1)
        total = meta.get("total_chunks", -1)
        fragments.append(
            f"[Fuente: {fuente} | Sección: {seccion} | "
            f"Fragmento: {posicion + 1}/{total} | "
            f"Similitud: {similarity:.2f}]\n{content.strip()}"
        )

    return "\n\n---\n\n".join(fragments)


rag_search = StructuredTool.from_function(
    func=_rag_search_impl,
    name="rag_search",
    description=(
        "Busca información narrativa sobre Riopaila Castilla en la base de conocimiento. "
        "Usar para historia, operaciones, sostenibilidad, gobierno corporativo, informes. "
        "Para Junta Directiva use consultas explícitas con integrantes, principales, suplentes."
    ),
    args_schema=RagSearchInput,
)
