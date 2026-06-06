"""
Agente conversacional Riopaila — Módulo 3.

Stack LangChain exigido:
  - init_chat_model
  - create_agent
  - HumanInTheLoopMiddleware
  - PostgresSaver (checkpointer)
  - Tools con esquemas Pydantic (Function Calling estricto)
"""

from __future__ import annotations

import os
from typing import Iterator, Literal, TypedDict

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware, dynamic_prompt
from langchain.agents.middleware.types import ModelRequest
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, ToolMessage

from riopaila_rag.checkpoint_store import clear_thread, get_checkpointer
from riopaila_rag.config import LLM_MODEL, OPENAI_API_KEY, check_openai
from riopaila_rag.tools import company_info_search, rag_search

# Re-export del prompt para tests/documentación
from riopaila_rag.agent_prompt import SYSTEM_PROMPT  # noqa: F401

_agent = None


@dynamic_prompt
def riopaila_dynamic_prompt(request: ModelRequest) -> str:
    """
    dynamic_prompt (Módulo 3): ajusta el system prompt según el hilo conversacional.
    """
    msg_count = len(request.state.get("messages", []))
    extra = ""
    if msg_count > 12:
        extra = (
            "\n\n# Contexto de sesión\nLa conversación es extensa; prioriza respuestas "
            "concisas y evita repetir información ya entregada en turnos anteriores."
        )
    return SYSTEM_PROMPT + extra


class AgentEvent(TypedDict, total=False):
    """Evento emitido por ask_streaming durante la ejecución del agente."""

    kind: Literal["tool_call", "tool_result", "token", "final"]
    name: str
    args: dict
    content: str


def _build_agent():
    global _agent
    if _agent is not None:
        return _agent

    check_openai()

    model = init_chat_model(
        f"openai:{LLM_MODEL}",
        api_key=OPENAI_API_KEY,
        temperature=0.1,
        top_p=0.9,
        streaming=True,
    )

    # HITL exigido en M3. En WhatsApp/N8N debe ser False (flujo automático).
    # En Streamlit puede activarse con HITL_INTERRUPT_TOOLS=true en .env.
    hitl_enabled = os.getenv("HITL_INTERRUPT_TOOLS", "false").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    hitl = HumanInTheLoopMiddleware(
        interrupt_on={
            "rag_search": hitl_enabled,
            "company_info_search": hitl_enabled,
        },
        description_prefix="Aprobación pendiente de herramienta",
    )

    _agent = create_agent(
        model=model,
        tools=[rag_search, company_info_search],
        middleware=[riopaila_dynamic_prompt, hitl],
        checkpointer=get_checkpointer(),
    )
    return _agent


def _thread_config(session_id: str) -> dict:
    return {"configurable": {"thread_id": session_id}}


def ask(question: str, session_id: str) -> str:
    """
    Envía una pregunta al agente. La memoria persiste en PostgresSaver por session_id.
    """
    agent = _build_agent()
    result = agent.invoke(
        {"messages": [HumanMessage(content=question)]},
        config=_thread_config(session_id),
    )
    ai_content = result["messages"][-1].content
    reply = ai_content if isinstance(ai_content, str) else str(ai_content)
    if not reply.strip():
        return (
            "En este momento no pude elaborar una respuesta. "
            "Por favor reformule su consulta sobre Riopaila Castilla."
        )
    return reply


def ask_streaming(question: str, session_id: str) -> Iterator[AgentEvent]:
    """Versión streaming para Streamlit y depuración en vivo."""
    agent = _build_agent()
    final_text_parts: list[str] = []

    for stream_mode, payload in agent.stream(
        {"messages": [HumanMessage(content=question)]},
        config=_thread_config(session_id),
        stream_mode=["updates", "messages"],
    ):
        if stream_mode == "updates":
            if not isinstance(payload, dict):
                continue
            for _node_name, node_data in payload.items():
                # create_agent + HumanInTheLoopMiddleware puede emitir nodos con valor None
                if not isinstance(node_data, dict):
                    continue
                for msg in node_data.get("messages", []):
                    if isinstance(msg, AIMessage) and msg.tool_calls:
                        for tc in msg.tool_calls:
                            yield {
                                "kind": "tool_call",
                                "name": tc.get("name", ""),
                                "args": tc.get("args") or {},
                            }
                    elif isinstance(msg, ToolMessage):
                        yield {
                            "kind": "tool_result",
                            "name": msg.name or "",
                            "content": str(msg.content),
                        }

        elif stream_mode == "messages":
            chunk, _meta = payload
            if (
                isinstance(chunk, AIMessageChunk)
                and chunk.content
                and not chunk.tool_call_chunks
            ):
                text = chunk.content if isinstance(chunk.content, str) else ""
                if text:
                    final_text_parts.append(text)
                    yield {"kind": "token", "content": text}

    final_text = "".join(final_text_parts).strip()
    yield {"kind": "final", "content": final_text}


def clear_session(session_id: str) -> None:
    """Borra el hilo del checkpointer (PostgresSaver / InMemorySaver)."""
    clear_thread(session_id)
