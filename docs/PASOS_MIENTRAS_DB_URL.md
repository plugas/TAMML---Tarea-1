# Avanzar sin `SUPABASE_DB_URL` (mientras Juan envía la URI)

## 1. Actualizar `.env` con el proyecto del dashboard

En Supabase → **Juananalv205's Project** → **Project Settings → API**:

```env
SUPABASE_URL=https://azgfxiroyqyplqhncpjy.supabase.co
SUPABASE_KEY=eyJ...   # copiar anon (Legacy) de ESTE proyecto
SUPABASE_DB_URL=      # dejar vacío por ahora
```

(El `.env` del compañero apunta a `kosklmgiroproepajqiq`; usa el del proyecto donde están las tablas.)

## 2. SQL en Supabase (tú sí puedes)

**SQL Editor** → ejecutar `supabase/migrations/002_conversation_logs.sql`

## 3. Instalar y comprobar (PowerShell en la carpeta del proyecto)

```powershell
python -m pip install -e .
python -c "from riopaila_rag.checkpoint_store import get_checkpointer; print(type(get_checkpointer()).__name__)"
```

Esperado: `InMemorySaver` (normal sin `SUPABASE_DB_URL`).

## 4. Probar Streamlit

```powershell
python run_app.py
```

Abrir http://localhost:8501 → pestaña **Agente**.

## 5. Probar API

```powershell
uvicorn riopaila_rag.api.main:app --host 127.0.0.1 --port 8000
```

Otra terminal:

```powershell
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"message\": \"Hola\", \"session_id\": \"test001\"}"
```

## 6. Cuando llegue `SUPABASE_DB_URL`

Pegar en `.env` → repetir:

```powershell
python -c "from riopaila_rag.checkpoint_store import get_checkpointer; print(type(get_checkpointer()).__name__)"
```

Debe salir `PostgresSaver`.
