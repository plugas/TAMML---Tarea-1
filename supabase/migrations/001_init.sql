-- ============================================================
-- Migración 001: Tablas base para el agente conversacional RAG
-- Riopaila Castilla — Módulo 2
--
-- Ejecutar en el SQL Editor de Supabase (dashboard.supabase.com)
-- Orden: habilitar pgvector PRIMERO, luego este script completo.
-- ============================================================

-- 1. Extensión pgvector (habilitar desde Dashboard > Database > Extensions si falla)
create extension if not exists vector;

-- ============================================================
-- 2. Tabla: documents (vector store para RAG)
--    Cada fila = un chunk del texto consolidado de Riopaila
-- ============================================================
create table if not exists documents (
    id          uuid primary key default gen_random_uuid(),
    content     text        not null,   -- texto del chunk
    metadata    jsonb       default '{}',  -- {seccion, fuente, posicion}
    embedding   vector(1536),           -- text-embedding-3-small (OpenAI)
    created_at  timestamptz default now()
);

-- Índice IVFFLAT para búsqueda vectorial eficiente (cosine similarity)
create index if not exists documents_embedding_idx
    on documents using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);

-- ============================================================
-- 3. Tabla: chat_messages (memoria conversacional SQL persistente)
--    LangChain PostgresChatMessageHistory escribe/lee aquí
-- ============================================================
create table if not exists chat_messages (
    id          bigserial primary key,
    session_id  text        not null,   -- uuid4 generado por Streamlit
    message     jsonb       not null,   -- {type: 'human'|'ai', content: '...'}
    created_at  timestamptz default now()
);

create index if not exists chat_messages_session_idx
    on chat_messages (session_id, created_at);

-- ============================================================
-- 4. Tabla: company_info (datos estructurados para tool determinista)
--    Categorías: contacto | horarios | sedes | legal
-- ============================================================
create table if not exists company_info (
    id          serial primary key,
    category    text        not null,   -- 'contacto' | 'horarios' | 'sedes' | 'legal'
    key         text        not null,   -- 'telefono_pbx' | 'email_pqrs' | ...
    value       text        not null,   -- valor concreto
    description text,                  -- nota opcional
    created_at  timestamptz default now(),
    unique(category, key)
);

-- ============================================================
-- 5. Función: match_documents (búsqueda vectorial por similitud coseno)
--    Llamada por LangChain SupabaseVectorStore internamente
-- ============================================================
create or replace function match_documents (
    query_embedding vector(1536),
    match_count     int     default 6,
    filter          jsonb   default '{}'
)
returns table (
    id          uuid,
    content     text,
    metadata    jsonb,
    similarity  float
)
language plpgsql
as $$
begin
    return query
    select
        d.id,
        d.content,
        d.metadata,
        1 - (d.embedding <=> query_embedding) as similarity
    from documents d
    where d.metadata @> filter
    order by d.embedding <=> query_embedding
    limit match_count;
end;
$$;
