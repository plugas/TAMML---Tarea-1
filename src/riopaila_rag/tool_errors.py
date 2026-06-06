"""Respuestas uniformes cuando una herramienta falla (Módulo 3)."""

from __future__ import annotations

TOOL_ERROR_MARKER = "[HERRAMIENTA_NO_DISPONIBLE]"

_FALLBACK_HINT = (
    "datos de contacto, NIT y razón social (categoría legal), líneas de negocio, "
    "certificaciones o temas generales de sostenibilidad y operación"
)


def tool_failure_message(
    detail: str,
    *,
    hint: str = _FALLBACK_HINT,
) -> str:
    """Mensaje que el LLM interpreta como fallo sin inventar datos."""
    return (
        f"{TOOL_ERROR_MARKER} En este momento no pude verificar esa información "
        f"({detail}). Puedo ayudarte con: {hint}."
    )


def is_tool_failure(result: str) -> bool:
    return TOOL_ERROR_MARKER in result or result.strip().startswith("Error:")
