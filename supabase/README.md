# `supabase/` — Esquema y datos del Módulo 2 (RAG)

Define el backend de datos del agente RAG: un Postgres gestionado por **Supabase** con la extensión **`pgvector`** para búsqueda semántica.

## Contenido

| Archivo | Qué hace |
|---|---|
| `migrations/001_init.sql` | Crea las 3 tablas, el índice vectorial y la función `match_documents()`. |
| `seeds/company_info.sql` | Inserta los datos estructurados verificados (9 categorías) que consume `company_info_search`. |

## Tablas

```sql
documents       -- vector store del RAG
  id uuid PK · content text · metadata jsonb · embedding vector(1536) · created_at

chat_messages   -- memoria conversacional persistente (Módulo 2)
  id bigserial PK · session_id text · message jsonb · created_at
  -- message = {type: 'human'|'ai', content: '...'}

company_info    -- datos estructurados verificados (tool determinista)
  id serial PK · category text · key text · value text · description text
  unique(category, key)
```

## Función de búsqueda semántica

```sql
match_documents(query_embedding vector(1536), match_count int, filter jsonb)
  -- returns (id, content, metadata, similarity)
  -- similarity = 1 - (embedding <=> query_embedding)   (coseno)
```

Es la función que invoca `rag_search` (vía `supabase.rpc(...)`) con `match_count = RAG_TOP_K` (12).

## Puesta en marcha

En el **SQL Editor** del dashboard de Supabase, en orden:

1. Habilitar la extensión: `Database → Extensions → vector`.
2. Ejecutar `migrations/001_init.sql`.
3. Ejecutar `seeds/company_info.sql`.
4. **Modo desarrollo:** desactivar RLS para que la `anon key` lea/escriba:
   ```sql
   ALTER TABLE documents     DISABLE ROW LEVEL SECURITY;
   ALTER TABLE chat_messages DISABLE ROW LEVEL SECURITY;
   ALTER TABLE company_info  DISABLE ROW LEVEL SECURITY;
   ```

Después, `make ingest` llena `documents` con ~2.515 chunks embebidos.

## Notas

- **Seguridad:** desactivar RLS es aceptable solo en desarrollo. **Para producción deben definirse políticas RLS** en las 3 tablas (la `anon key` es pública).
- **Índice IVFFLAT:** el script crea `documents_embedding_idx` (IVFFLAT, 100 listas). Con pocos vectores (~2.515) la búsqueda aproximada puede descartar resultados tabulares relevantes; en ese caso se usa búsqueda exacta (`DROP INDEX documents_embedding_idx`). Ver `CONTEXT.md` §14.
- **Calidad de embeddings tabulares:** durante la ingestión el texto se enriquece con prefijo `Documento:`/`Sección:` antes de embeber, para que tablas (p. ej. Junta Directiva) sean recuperables.
