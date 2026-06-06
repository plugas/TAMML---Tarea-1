-- Módulo 3: logs de conversación para análisis t-SNE
-- Ejecutar en: https://supabase.com/dashboard/project/azgfxiroyqyplqhncpjy/sql/new

create table if not exists conversation_logs (
    id               bigserial primary key,
    session_id       text        not null,
    channel          text        default 'api',
    user_message     text        not null,
    assistant_reply  text        not null,
    transcript       text,
    created_at       timestamptz default now()
);

create index if not exists conversation_logs_session_idx
    on conversation_logs (session_id, created_at);
