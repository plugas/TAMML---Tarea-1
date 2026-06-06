"""
Esquemas Pydantic para Function Calling estricto (Módulo 3).

Cada herramienta del agente expone un JSON Schema validado antes de ejecutarse.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

CompanyInfoCategory = Literal[
    "contacto",
    "redes_sociales",
    "sedes",
    "legal",
    "cifras",
    "negocio",
    "sostenibilidad",
    "certificaciones",
    "fundacion",
]


class RagSearchInput(BaseModel):
    """Entrada estructurada para búsqueda semántica en la base documental."""

    query: str = Field(
        ...,
        min_length=3,
        max_length=800,
        description=(
            "Pregunta o tema a buscar en informes y comunicados oficiales de "
            "Riopaila Castilla. Para Junta Directiva incluya términos explícitos "
            "(integrantes, principales, suplentes, años de nombramiento)."
        ),
    )


class CompanyInfoSearchInput(BaseModel):
    """Entrada estructurada para datos verificados en company_info."""

    category: CompanyInfoCategory | Literal[""] = Field(
        default="",
        description=(
            "Categoría exacta a consultar. Dejar vacío para listar todas las "
            "categorías disponibles."
        ),
    )
