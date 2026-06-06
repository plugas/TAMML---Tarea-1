"""
Vector store LangChain (Módulo 3): embeddings + SupabaseVectorStore.
"""

from __future__ import annotations

from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings
from supabase import create_client

from riopaila_rag.config import (
    EMBEDDING_MODEL,
    OPENAI_API_KEY,
    RAG_TOP_K,
    SUPABASE_KEY,
    SUPABASE_URL,
    check_openai,
    check_supabase,
)

_store: SupabaseVectorStore | None = None


def get_embeddings() -> OpenAIEmbeddings:
    check_openai()
    return OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=OPENAI_API_KEY)


def get_vectorstore() -> SupabaseVectorStore:
    global _store
    if _store is not None:
        return _store
    check_supabase()
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    _store = SupabaseVectorStore(
        client=client,
        embedding=get_embeddings(),
        table_name="documents",
        query_name="match_documents",
    )
    return _store


def similarity_search(query: str, k: int | None = None) -> list[tuple[str, dict, float]]:
    """Devuelve (contenido, metadata, score) por documento recuperado."""
    k = k or RAG_TOP_K
    store = get_vectorstore()
    docs_scores = store.similarity_search_with_relevance_scores(query, k=k)
    out: list[tuple[str, dict, float]] = []
    for doc, score in docs_scores:
        out.append((doc.page_content, doc.metadata or {}, float(score)))
    return out
