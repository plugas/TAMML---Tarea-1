"""
Tool estructurada: company_info con esquema Pydantic (Function Calling, Módulo 3).
"""

from __future__ import annotations

from langchain_core.tools import StructuredTool

from riopaila_rag.config import SUPABASE_KEY, SUPABASE_URL
from riopaila_rag.schemas import CompanyInfoSearchInput
from riopaila_rag.tool_errors import tool_failure_message

try:
    from supabase import create_client as _create_client

    _supabase = _create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    _supabase = None

_VALID_CATEGORIES = {
    "contacto",
    "redes_sociales",
    "sedes",
    "legal",
    "cifras",
    "negocio",
    "sostenibilidad",
    "certificaciones",
    "fundacion",
}


def _company_info_search_impl(category: str = "") -> str:
    if _supabase is None:
        return tool_failure_message("servicio de datos estructurados no disponible")

    category = (category or "").strip().lower()

    if category and category not in _VALID_CATEGORIES:
        cats = ", ".join(sorted(_VALID_CATEGORIES))
        return tool_failure_message(
            f"categoría '{category}' no reconocida; categorías válidas: {cats}"
        )

    try:
        query = _supabase.table("company_info").select(
            "category, key, value, description"
        )
        if category:
            query = query.eq("category", category)
        result = query.order("category").order("key").execute()
    except Exception as exc:
        return tool_failure_message(f"error al consultar datos corporativos: {exc}")

    if not result.data:
        return tool_failure_message("no hay datos para esa categoría")

    grouped: dict[str, list[str]] = {}
    for row in result.data:
        cat = row["category"]
        key = row["key"]
        value = row["value"]
        desc = row.get("description") or ""
        entry = f"  {key}: {value}"
        if desc:
            entry += f"  ({desc})"
        grouped.setdefault(cat, []).append(entry)

    parts = []
    for cat, entries in grouped.items():
        parts.append(f"## {cat.upper()}\n" + "\n".join(entries))

    return "\n\n".join(parts)


company_info_search = StructuredTool.from_function(
    func=_company_info_search_impl,
    name="company_info_search",
    description=(
        "Consulta datos exactos y verificados: contacto, redes, sedes, legal (NIT), "
        "cifras, negocio, sostenibilidad, certificaciones, fundación."
    ),
    args_schema=CompanyInfoSearchInput,
)
