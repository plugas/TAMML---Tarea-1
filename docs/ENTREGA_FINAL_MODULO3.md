# Entrega final Módulo 3 — estado del equipo

**Ruta:** A (LangChain + FastAPI + WhatsApp Vía 2)  
**Empresa:** Riopaila Castilla

## Completado

- [x] Function Calling + Pydantic (`schemas.py`, `tools/`)
- [x] Agente LangChain (`create_agent`, `init_chat_model`, `HumanInTheLoopMiddleware`, `dynamic_prompt`)
- [x] API FastAPI (`/chat`, `/health`, `/webhooks/whatsapp`)
- [x] WhatsApp Vía 2 operativo (Meta + ngrok)
- [x] `conversation_logs` + seed de datos
- [x] Bonus t-SNE: `docs/tsne_conversaciones.png` + `scripts/run_tsne.py`
- [x] Informe: `docs/INFORME_TECNICO_MODULO3.md` + PDF generado
- [x] Guion sustentación: `docs/SUSTENTACION_EN_VIVO.md`

## Pendiente (requiere acción humana)

### 1. PostgresSaver — **prioridad alta** (30% rúbrica)

Sigue `docs/ARREGLAR_POSTGRES_SAVER.md`:

1. Reset password en Supabase Dashboard.
2. Actualizar `SUPABASE_DB_URL` en `.env`.
3. `python scripts/test_supabase_db.py` → `[OK]`
4. Reiniciar API → `/health` con `postgres_saver: true`.

### 2. GitHub

```powershell
cd "ruta\al\proyecto\TAMML---Tarea-1-feat-rag-langchain"
git init
git add .
git commit -m "Entrega Módulo 3: agente productizado WhatsApp + t-SNE"
git remote add origin https://github.com/TU_USUARIO/TAMML-Tarea-1.git
git push -u origin main
```

**No subir:** `.env`, `.venv/`, tokens WhatsApp.

### 3. Día de sustentación (15 min)

- [ ] Renovar `WHATSAPP_ACCESS_TOKEN` en Meta (caduca ~24 h).
- [ ] `.\scripts\start_api.ps1` + `ngrok http 8000` + (opcional) `python run_app.py`.
- [ ] Agregar celular del **profesor** en Meta → API Setup → **To**.
- [ ] Ensayo: profesor envía NIT → segunda pregunta con contexto.

## Comandos rápidos

```powershell
python scripts/verify_modulo3.py --api http://127.0.0.1:8000
python scripts/generate_informe_pdf.py
python scripts/run_tsne.py
```

## Archivos a entregar al profesor

1. `docs/INFORME_TECNICO_MODULO3.pdf`
2. `docs/tsne_conversaciones.png` (bonus)
3. URL del repositorio GitHub
4. Demo en vivo WhatsApp
