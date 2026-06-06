# Runbook — Módulo 3: Agente corporativo sobre OpenFang Agent OS

Guía reproducible para levantar el agente institucional de Riopaila Castilla sobre **OpenFang**
(Agent OS en Rust) con modelo local **Ollama**, memoria migrada, Hand autónomo y canal Telegram.

Probado en: **Windows 11**, PowerShell, GPU NVIDIA RTX 3050 (4 GB VRAM), Python 3.12.

---

## 0. Arquitectura

```
Telegram  ──►  OpenFang Kernel (daemon Rust, API+dashboard :4200)
                   │
        ┌──────────┼─────────────────────┐
        ▼                                 ▼
 Agente: riopaila-institucional     Hand: riopaila-inteligencia
 (reactivo, canales)                (autónomo, programado)
        │                                 │
        ▼                                 ▼
 Memoria OpenFang                    web_search → reporte
  • KV Store (43 datos verificados)
  • Memoria semántica (documentos)
        │
        ▼
 Ollama (gemma3:4b) — localhost:11434  ← 100% local (soberanía de datos)
```

---

## 1. Instalar OpenFang

```powershell
irm https://openfang.sh/install.ps1 | iex      # Windows
# Linux/macOS/WSL2:  curl -fsSL https://openfang.sh/install | sh
```
Binario instalado en `~/.openfang/bin/openfang.exe` (v0.6.9). Si `openfang` no está en el PATH
de la sesión, usar la ruta completa o reabrir la terminal.

```powershell
openfang init --quick        # crea ~/.openfang/config.toml
```

## 2. Instalar Ollama y el modelo local

```powershell
winget install --id Ollama.Ollama --accept-source-agreements --accept-package-agreements
# El servicio queda escuchando en http://127.0.0.1:11434 (OpenFang lo auto-detecta).

ollama pull gemma3:4b        # ~3.3 GB. Alternativa liviana: ollama pull llama3.2:3b (~2 GB)
```

### 2.1 Forzar 100% GPU (RTX 3050, 4 GB)
La GPU de 4 GB es ajustada. Para que el modelo corra **100% en GPU**:
1. Libera VRAM cerrando apps que la consuman (Docker Desktop, pestañas del navegador con
   aceleración). Verifica con `nvidia-smi` que `memory.used` sea bajo (< 600 MiB ideal).
2. Crea un modelo con todas las capas en GPU y contexto acotado (ver `openfang/Modelfile.gemma3-gpu`):
   ```powershell
   ollama create gemma3-riopaila -f openfang/Modelfile.gemma3-gpu
   ```
3. Verifica el porcentaje de GPU tras la primera consulta:
   ```powershell
   ollama ps        # la columna PROCESSOR debe decir "100% GPU"
   ```
> Si `ollama ps` muestra reparto CPU/GPU, no hay suficiente VRAM libre: cierra más apps o usa
> `llama3.2:3b` (cabe con holgura) o reduce `num_ctx` en el Modelfile.

## 3. Configurar OpenFang

Copia la plantilla y reinicia:
```powershell
copy openfang\config.toml.example $env:USERPROFILE\.openfang\config.toml
openfang start               # daemon + dashboard en http://127.0.0.1:4200
openfang status
```
El `config.toml` apunta a `provider = "ollama"` / `model = "gemma3:4b"` (sin API key).

## 4. Desplegar el agente corporativo

```powershell
openfang agent spawn openfang/riopaila-institucional/agent.toml
openfang agent list          # anota el UUID del agente "riopaila-institucional"
```
El agente lleva los **datos verificados como identidad base permanente** en su system prompt
(evita alucinaciones en NIT, año de fundación, certificaciones, etc.).

## 5. Migrar el conocimiento a la memoria

```powershell
python src/scripts/seed_openfang_kv.py        # 43 datos estructurados → KV Store
python src/scripts/ingest_openfang.py         # documentos → memoria semántica
# Atajo: make openfang-migrate
```
Verificar:
```powershell
openfang memory list riopaila-institucional   # debe listar las claves cat.key
openfang message <UUID> "¿En qué año fue fundada Riopaila Castilla y cuál es su NIT?"
# Esperado: 1918 y 900.087.414-4 (sin alucinar)
```

## 6. Activar el Hand autónomo

```powershell
openfang hand install openfang/hands/riopaila-inteligencia
openfang hand activate riopaila-inteligencia
openfang hand info riopaila-inteligencia
# Ejecución/monitoreo desde el dashboard :4200 → Hands
```

## 7. Desplegar en Telegram

> **Requiere acción humana** (token del bot — no puede automatizarse).

1. En Telegram, habla con **@BotFather** → `/newbot` → nombre y username (termina en `bot`).
   Copia el **token** (`1234567890:ABC...`).
2. Añade el token al `.env`:  `TELEGRAM_BOT_TOKEN=<token>`
3. Asegura que `~/.openfang/config.toml` tiene la sección `[telegram]` (ya incluida en la plantilla).
4. Arranca el **puente** Telegram (el canal nativo de OpenFang v0.6.9 da 404 al activar; el
   puente lo sortea conectando Telegram con la API del agente):
   ```powershell
   python src/scripts/telegram_bridge.py        # o: make openfang-telegram
   # Debe imprimir "Puente activo para @RioPaila_Bot" y quedar escuchando.
   ```
5. **Prueba en vivo:** escribe al bot **@RioPaila_Bot** desde Telegram:
   - "¿Cuál es el NIT de Riopaila Castilla?"
   - "¿Qué certificaciones tiene la empresa?"
   El puente recibe el mensaje, consulta al agente (gpt-4o-mini) y responde en el chat.

---

## Notas operativas

- **Proveedor LLM (IMPORTANTE)**: el backend **recomendado** es `gpt-4o-mini` (OpenAI), porque es
  fiable dentro del *agent-loop* de OpenFang y responde sin alucinaciones (validado).
  - **Hallazgo / limitación de OpenFang v0.6.9**: con modelos locales `gemma3:4b` y `qwen2.5:3b`
    el agent-loop entra en un bucle infinito "##" y no responde (los modelos funcionan **perfecto
    directo en Ollama** y logran **100% GPU**). El único modelo local que responde completo en el
    loop es `llama3.2:3b`, pero su calidad es limitada.
  - **Ruta local (soberanía de datos)**: queda instalada y documentada (Ollama + Modelfile GPU).
    Para usarla, cambia `[default_model]` a `provider = "ollama"` / `model = "llama3.2:3b"`.
  - **Groq** es otra alternativa nube (`provider = "groq"`, `GROQ_API_KEY`); tier gratuito con
    rate limits.
- **Arranque del daemon con secretos**: el daemon lee las API keys de variables de entorno
  (`GROQ_API_KEY`, etc.). El snippet del paso 7 carga el `.env` del proyecto en el proceso sin
  exponer los valores en la línea de comandos.
- **Dashboard**: http://127.0.0.1:4200 — agentes, memoria, hands y trazas.
- **Logs**: `openfang logs` o `~/.openfang/tui.log`.
