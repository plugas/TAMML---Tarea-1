"""

Memoria persistente del agente con PostgresSaver (Módulo 3).



Usa SUPABASE_DB_URL (PostgreSQL directo de Supabase). Si no está configurada

o la conexión falla (p. ej. bloqueo temporal ECIRCUITBREAKER), recurre a

InMemorySaver para que API/WhatsApp sigan operativos en desarrollo.

"""



from __future__ import annotations



import logging

from typing import TYPE_CHECKING



from riopaila_rag.config import SUPABASE_DB_URL



if TYPE_CHECKING:

    from langgraph.checkpoint.base import BaseCheckpointSaver



_logger = logging.getLogger(__name__)

_checkpointer: BaseCheckpointSaver | None = None

_pool = None





def _memory_checkpointer() -> BaseCheckpointSaver:

    from langgraph.checkpoint.memory import InMemorySaver



    _logger.warning(

        "Usando InMemorySaver (memoria solo hasta reiniciar la API). "

        "Revisa SUPABASE_DB_URL cuando Postgres esté disponible."

    )

    return InMemorySaver()





def _probe_postgres(conninfo: str, *, timeout: int = 12) -> bool:

    """Prueba una conexión antes de crear el pool (evita reintentos ruidosos)."""

    try:

        import psycopg



        with psycopg.connect(conninfo, connect_timeout=timeout) as conn:

            conn.execute("SELECT 1")

        return True

    except Exception as exc:

        _logger.warning("Postgres no accesible (%s).", exc)

        return False





def get_checkpointer() -> BaseCheckpointSaver:

    """Singleton del checkpointer LangGraph."""

    global _checkpointer, _pool

    if _checkpointer is not None:

        return _checkpointer



    if not SUPABASE_DB_URL or not _probe_postgres(SUPABASE_DB_URL):

        _checkpointer = _memory_checkpointer()

        return _checkpointer



    try:

        import psycopg

        from langgraph.checkpoint.postgres import PostgresSaver

        from psycopg_pool import ConnectionPool

        # setup() usa CREATE INDEX CONCURRENTLY: requiere autocommit (Supabase pooler).
        with psycopg.connect(
            SUPABASE_DB_URL,
            connect_timeout=15,
            autocommit=True,
        ) as conn:
            PostgresSaver(conn).setup()

        _pool = ConnectionPool(
            conninfo=SUPABASE_DB_URL,
            min_size=1,
            max_size=10,
            kwargs={"autocommit": True},
            open=True,
            timeout=15,
        )
        _checkpointer = PostgresSaver(_pool)

        _logger.info("PostgresSaver activo (memoria por thread_id / session_id).")

    except Exception as exc:

        _logger.warning(

            "PostgresSaver no disponible (%s). Fallback a InMemorySaver.",

            exc,

        )

        _checkpointer = _memory_checkpointer()

    return _checkpointer





def clear_thread(session_id: str) -> None:

    """Borra el historial del agente para una sesión (teléfono / session_id)."""

    cp = get_checkpointer()

    if hasattr(cp, "delete_thread"):

        cp.delete_thread(session_id)


