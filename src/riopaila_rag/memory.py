"""
Memoria conversacional persistente en Supabase (tabla chat_messages).

Cada sesión tiene un session_id único. Los mensajes se guardan como
{type: 'human'|'ai', content: '...'} en la columna jsonb `message`.
LangChain los lee como HumanMessage / AIMessage automáticamente.
"""

from __future__ import annotations

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, messages_from_dict
from supabase import create_client, Client

from riopaila_rag.config import SUPABASE_KEY, SUPABASE_URL


class SupabaseChatHistory(BaseChatMessageHistory):
    """
    Historial de mensajes almacenado en la tabla chat_messages de Supabase.
    Compatible con RunnableWithMessageHistory de LangChain.
    """

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self._client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    @property
    def messages(self) -> list[BaseMessage]:
        result = (
            self._client.table("chat_messages")
            .select("message")
            .eq("session_id", self.session_id)
            .order("created_at")
            .execute()
        )
        msgs: list[BaseMessage] = []
        for row in result.data:
            msg_dict = row["message"]
            msg_type = msg_dict.get("type", "")
            content = msg_dict.get("content", "")
            if msg_type == "human":
                msgs.append(HumanMessage(content=content))
            elif msg_type == "ai":
                msgs.append(AIMessage(content=content))
        return msgs

    def add_message(self, message: BaseMessage) -> None:
        msg_type = "human" if isinstance(message, HumanMessage) else "ai"
        self._client.table("chat_messages").insert({
            "session_id": self.session_id,
            "message": {"type": msg_type, "content": message.content},
        }).execute()

    def clear(self) -> None:
        self._client.table("chat_messages").delete().eq(
            "session_id", self.session_id
        ).execute()


def get_session_history(session_id: str) -> SupabaseChatHistory:
    """Factory que RunnableWithMessageHistory usa para obtener el historial."""
    return SupabaseChatHistory(session_id)
