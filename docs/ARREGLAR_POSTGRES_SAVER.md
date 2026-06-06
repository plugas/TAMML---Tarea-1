# Arreglar PostgresSaver (memoria persistente M3)

Sin esto la API usa `InMemorySaver` y **pierde la memoria** al reiniciar.

## Pasos en Supabase (5 min)

1. Entra a [Supabase Dashboard](https://supabase.com/dashboard) → proyecto **azgfxiroyqyplqhncpjy**.
2. **Project Settings** → **Database**.
3. Clic en **Reset database password** → copia la contraseña nueva.
4. En la misma página, **Connection string** → pestaña **URI** → modo **Session pooler** → puerto **5432**.
5. Sustituye `[YOUR-PASSWORD]` por la contraseña (si tiene `@` o `#`, codifícala en URL).

Formato esperado en `.env`:

```env
SUPABASE_DB_URL=postgresql://postgres.azgfxiroyqyplqhncpjy:TU_PASSWORD@aws-1-us-west-2.pooler.supabase.com:5432/postgres
```

## Verificar

```powershell
python scripts/test_supabase_db.py
```

Debe mostrar `[OK] Conexion Postgres exitosa`.

## Reiniciar API

```powershell
.\scripts\start_api.ps1
```

`GET http://127.0.0.1:8000/health` debe incluir:

```json
"checkpointer": "PostgresSaver",
"postgres_saver": true,
"memory_persistent": true
```

## Prueba de memoria

Misma `session_id` dos veces seguidas:

```powershell
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"message\": \"Mi nombre es Valentina\", \"session_id\": \"573187337493\"}"
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"message\": \"Como me llamo?\", \"session_id\": \"573187337493\"}"
```

La segunda respuesta debe recordar el nombre.
