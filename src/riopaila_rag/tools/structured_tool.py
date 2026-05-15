"""
Tool estructurada: consulta determinista a la tabla `company_info` de Supabase.

Para datos exactos (teléfonos, emails, direcciones, NIT, redes sociales, etc.)
donde una búsqueda semántica podría dar respuestas incorrectas o desactualizadas.
El agente usa esta tool cuando el usuario pregunta por datos de contacto o
información puntual verificable.
"""

from __future__ import annotations

from langchain_core.tools import tool

from riopaila_rag.config import SUPABASE_KEY, SUPABASE_URL

try:
    from supabase import create_client as _create_client
    _supabase = _create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    _supabase = None

# Categorías válidas en company_info
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


@tool
def company_info_search(category: str = "") -> str:
    """
    Consulta datos estructurados y verificados de Riopaila Castilla.

    Usa esta herramienta para preguntas sobre datos puntuales y exactos como:
    - Contacto: teléfonos, emails, PBX, líneas de atención
    - Redes sociales: URLs de LinkedIn, Instagram, YouTube, X
    - Sedes: direcciones de oficinas y plantas
    - Legal: NIT, razón social, tipo de sociedad, bolsa de valores
    - Cifras: empleados, hectáreas, capacidad de producción, toneladas
    - Negocio: segmentos, productos principales
    - Sostenibilidad: iniciativas, metas
    - Certificaciones: normas ISO, FSSC, Rainforest Alliance, etc.
    - Fundacion: información de la Fundación Riopaila Castilla

    Args:
        category: Categoría a consultar. Valores válidos:
            contacto | redes_sociales | sedes | legal | cifras |
            negocio | sostenibilidad | certificaciones | fundacion
            Deja vacío para obtener todas las categorías disponibles.

    Returns:
        Datos estructurados de la categoría solicitada.
    """
    if _supabase is None:
        return "Error: cliente Supabase no disponible."

    category = category.strip().lower()

    if category and category not in _VALID_CATEGORIES:
        cats = ", ".join(sorted(_VALID_CATEGORIES))
        return (
            f"Categoría '{category}' no reconocida. "
            f"Categorías disponibles: {cats}"
        )

    query = _supabase.table("company_info").select("category, key, value, description")
    if category:
        query = query.eq("category", category)

    result = query.order("category").order("key").execute()

    if not result.data:
        return "No se encontraron datos para esa categoría."

    # Agrupar por categoría para una respuesta legible
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
