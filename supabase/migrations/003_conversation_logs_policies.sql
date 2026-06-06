-- Módulo 3: políticas RLS para conversation_logs (solo si RLS está activo en la tabla)
-- Si en dev tienes RLS desactivado, este script es opcional.

alter table conversation_logs enable row level security;

drop policy if exists conversation_logs_anon_insert on conversation_logs;
drop policy if exists conversation_logs_anon_select on conversation_logs;

create policy conversation_logs_anon_insert
    on conversation_logs
    for insert
    to anon, authenticated
    with check (true);

create policy conversation_logs_anon_select
    on conversation_logs
    for select
    to anon, authenticated
    using (true);
