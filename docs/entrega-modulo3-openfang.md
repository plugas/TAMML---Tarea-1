# Módulo 3 — Documentación de entrega: Agente corporativo sobre OpenFang Agent OS

> Proyecto Riopaila Castilla Chatbot (TAMML — Tarea 1, Ruta B).
> Documento de entrega: qué se construyó, los agentes y su relación, los parámetros de los modelos
> (determinismo) y cómo desplegar el canal de Telegram.
> Fecha: 05 de junio de 2026.

---

## 1. Qué se ha hecho hasta el momento (bitácora real)

Todo lo siguiente fue ejecutado y verificado en una máquina Windows 11 (PowerShell, GPU NVIDIA
RTX 3050 de 4 GB, Python 3.12).

1. **Instalación de OpenFang Agent OS** (v0.6.9) — binario nativo en `~/.openfang/bin/openfang.exe`.
   Daemon corriendo en `http://127.0.0.1:4200` (API compatible con OpenAI + dashboard web).
2. **Instalación de Ollama** (v0.30.4) y descarga de 3 modelos locales: `gemma3:4b`, `qwen2.5:3b`,
   `llama3.2:3b`. Servicio en `localhost:11434` (auto-detectado por OpenFang).
3. **Configuración del kernel** (`~/.openfang/config.toml`): proveedor, memoria y compactación.
4. **Optimización GPU**: Modelfile `gemma3-riopaila` con `num_gpu 99`; se confirmó **100% GPU**
   (`ollama ps`) con gemma3:4b y qwen2.5:3b en la RTX 3050.
5. **Agente corporativo** `riopaila-institucional` desplegado desde manifiesto, con los datos
   verificados de la empresa embebidos como **identidad base** (anti-alucinación).
6. **Migración del conocimiento** al sustrato de memoria de OpenFang: **43 datos estructurados**
   (de `supabase/seeds/company_info.sql`) cargados al **KV Store** con `seed_openfang_kv.py`
   (UTF-8 verificado). Total en memoria: 49 pares.
7. **Hand autónomo** `riopaila-inteligencia` (HAND.toml + SKILL.md) instalado y **activado**
   (vigilancia sectorial programada).
8. **Backend del agente fijado en `gpt-4o-mini`** (OpenAI) tras detectar un bug de OpenFang con
   modelos locales (ver §5). Validado con preguntas reales **sin alucinaciones**.
9. **Artefactos versionados** en el repo: `openfang/`, `src/scripts/`, `docs/`, targets en el
   `Makefile`, `.env.example` y sección §20 en `CONTEXT.md`.

**Pruebas en vivo superadas:** año de fundación **1918** + NIT `900.087.414-4`; listado de
certificaciones ISO; correo de la línea ética + sitio web; y rechazo correcto de temas fuera de
alcance.

**Pendiente (requiere acción humana):** desplegar el canal de **Telegram** (necesita el token de
BotFather — ver §4).

---

## 2. Agentes construidos y cómo se relacionan

OpenFang es un *sistema operativo de agentes*: un **kernel** (daemon) orquesta múltiples agentes,
su memoria y sus canales. En este proyecto construimos **dos piezas propias** sobre ese kernel.

```
                          ┌──────────────────────────────────────────┐
        Telegram ───────► │           OpenFang Kernel (daemon)        │
        (canal)           │   API :4200 · enrutamiento · memoria      │
                          └───────────────┬───────────────┬──────────┘
                                          │               │
                    (reactivo, canales)   ▼               ▼   (autónomo, programado)
                 ┌───────────────────────────┐   ┌──────────────────────────────────┐
                 │  AGENTE                     │   │  HAND  riopaila-inteligencia      │
                 │  riopaila-institucional     │   │  (agente: riopaila-inteligencia-  │
                 │  • chat puro (sin tools)    │   │   hand)                           │
                 │  • identidad base + memoria │   │  • tools: web_search, web_fetch,  │
                 │  • gpt-4o-mini (temp 0.0)   │   │    memory_store, schedule_create  │
                 └─────────────┬───────────────┘   │  • multifase: research→analysis→  │
                               │                    │    report                         │
                               ▼                    └──────────────┬───────────────────┘
                     Memoria OpenFang                              │
                     ├─ KV Store (49 pares: 43 datos verificados)  │ escribe hallazgos / reportes
                     └─ memoria de sesión por conversación  ◄──────┘ a memoria y canal
```

### 2.1 Agente conversacional — `riopaila-institucional`
- **Rol:** atención institucional reactiva. Es el que responde en los canales (Telegram).
- **Tipo:** `module = "builtin:chat"`, **chat puro** (sin herramientas) → máxima fiabilidad.
- **Conocimiento:** los datos verificados de la empresa van embebidos en su `system_prompt`
  (identidad base permanente: NIT, fundación 1918, líneas de negocio, certificaciones, contacto,
  sostenibilidad). Esto garantiza respuestas correctas sin depender del *tool-calling*.
- **Manifiesto:** `openfang/riopaila-institucional/agent.toml`.

### 2.2 Hand autónomo — `riopaila-inteligencia`
- **Rol:** inteligencia sectorial autónoma. NO espera preguntas; corre en ciclos programados.
- **Agente interno:** al activarse crea el agente `riopaila-inteligencia-hand` (con herramientas).
- **Capacidades (tools):** `web_search`, `web_fetch`, `memory_store`, `memory_recall`,
  `schedule_create`, `file_write`, `event_publish`.
- **Flujo multifase:** *research* (busca novedades del sector azucarero/biocombustibles/empresa) →
  *analysis* (clasifica OPORTUNIDAD/RIESGO/NEUTRAL + relevancia) → *report* (reporte ejecutivo).
- **Conocimiento de dominio:** `SKILL.md` (fuentes ASOCAÑA, SFC, terminología ICUMSA, bagazo, etc.).
- **Manifiesto:** `openfang/hands/riopaila-inteligencia/HAND.toml`.

### 2.3 Agente de respuestas rápidas — `riopaila-faq`
- **Rol:** especialista en **FAQ**: respuestas cortas y directas (1-3 frases) a preguntas
  frecuentes (NIT, contacto, productos, certificaciones, cifras).
- **Tipo:** chat puro, `temperature 0.0`, `max_tokens 512` (fuerza brevedad). Datos verificados
  condensados en su prompt.
- **Manifiesto:** `openfang/riopaila-faq/agent.toml`.

### 2.4 Agente coordinador (router multi-agente) — `riopaila-coordinador`
- **Rol:** recibe la consulta y **delega en el especialista adecuado** usando la herramienta
  `agent_send` de OpenFang (interacción agente-a-agente):
  - pregunta simple / dato puntual → `riopaila-faq`
  - pregunta detallada / histórica → `riopaila-institucional`
- Devuelve la respuesta del especialista indicando quién respondió.
- **Tools:** `agent_list`, `agent_send`, `memory_recall`. **Manifiesto:** `openfang/riopaila-coordinador/agent.toml`.
- **El bot de Telegram apunta a este coordinador**, por lo que cada mensaje muestra la
  coordinación multi-agente en vivo.

### 2.5 Cómo se relacionan
- El **kernel** es el punto central: recibe mensajes del canal (Telegram → puente) y los entrega al
  **coordinador**; ejecuta el Hand según su programación; y administra la **memoria compartida**.
- El **coordinador** orquesta a `riopaila-faq` e `riopaila-institucional` vía `agent_send`
  (verificado funcionando con gpt-4o-mini).
- Los **4 agentes Riopaila corren en paralelo** (`institucional`, `faq`, `coordinador`,
  `inteligencia-hand`) y comparten el sustrato de memoria de OpenFang.
- OpenFang trae además ~30 agentes de ejemplo; los nuestros conviven con ellos pero son los únicos
  específicos de Riopaila Castilla.

---

## 3. Parámetros de los modelos (respuestas deterministas)

Para un asistente corporativo factual, lo crítico es **no variar los datos** (NIT, años, cifras).
Eso se controla con los parámetros de muestreo del modelo.

### 3.1 Agente conversacional (`gpt-4o-mini`) — configuración actual
Definidos en `openfang/riopaila-institucional/agent.toml`, bloque `[model]`:

| Parámetro | Valor | Para qué |
|---|---|---|
| `temperature` | **0.0** | Máximo determinismo. A 0 el modelo elige siempre el token más probable → respuestas reproducibles. |
| `top_p` | **1.0** | Nucleus sampling desactivado (irrelevante con temp 0). |
| `seed` | **7** | Semilla fija para reproducibilidad entre ejecuciones. |
| `max_tokens` | **4096** | Límite de longitud de respuesta. |

> **Nota honesta sobre el determinismo en LLMs:** ni siquiera con `temperature = 0` un LLM en la
> nube es 100% byte-idéntico (hay no-determinismo a nivel de infraestructura). Lo que SÍ se
> garantiza es la **consistencia factual**: en las pruebas, la misma pregunta devolvió siempre
> **1918** aunque el fraseo variara levemente. La combinación **temp 0 + identidad base con datos
> verificados** es la que asegura que los hechos no cambien.

### 3.2 Hand autónomo
En `openfang/hands/riopaila-inteligencia/HAND.toml`, bloque `[agent]`:

| Parámetro | Valor | Para qué |
|---|---|---|
| `temperature` | 0.2 | Ligera variabilidad: la investigación web se beneficia de algo de exploración. |
| `max_tokens` | 8192 | Reportes más largos. |
| `max_iterations` | 40 | Tope de pasos del ciclo autónomo (research→analysis→report). |

### 3.3 Modelos locales (Ollama) — si se usa la ruta local
En `openfang/Modelfile.gemma3-gpu`:

| Parámetro | Valor | Para qué |
|---|---|---|
| `num_gpu` | 99 | Fuerza todas las capas a la GPU (100% GPU). |
| `num_ctx` | 4096 | Ventana de contexto (ajustar a 2048 si falta VRAM). |
| `temperature` | 0.1 | Casi determinista. |
| `top_p` | 0.9 | Considera el 90% de probabilidad acumulada. |

> Referencia: el **Módulo 2** ya usaba `temperature 0.1` y `top_p 0.9` — los valores de aquí son
> coherentes con esa decisión, llevados a `0.0` en el agente de Módulo 3 para máxima reproducibilidad.

---

## 4. Cómo crear el token de Telegram (paso a paso)

El token es lo único que falta y **debe crearlo una persona** (no se puede automatizar).

1. Abre **Telegram** (app o web) e inicia conversación con **@BotFather** (el bot oficial; tiene
   marca de verificación azul).
2. Envía el comando: `/newbot`
3. BotFather pide un **nombre** para el bot (visible, p. ej. `Riopaila Castilla Asistente`).
4. Luego pide un **username** único que **debe terminar en `bot`** (p. ej. `riocas_asistente_bot`).
5. BotFang responde con el **token de acceso**, con este formato:
   `1234567890:AAH...cadena_larga...`
   ⚠️ Ese token es **secreto** — quien lo tenga controla el bot. No lo subas a GitHub.
6. Entrega el token de una de estas dos formas:
   - **Opción A:** pégalo en el archivo `.env` del proyecto como:
     `TELEGRAM_BOT_TOKEN=1234567890:AAH...`
   - **Opción B:** pásalo por un canal privado para que se configure.

### Cómo queda conectado (puente Telegram)
> **Hallazgo:** el canal **nativo** de Telegram de OpenFang v0.6.9 **no se activa** en esta build
> (`POST /api/channels/telegram/enable` → **404**; el daemon tampoco lo auto-arranca desde la
> config). Para sortearlo se implementó un **puente ligero** (`src/scripts/telegram_bridge.py`,
> solo stdlib) que conecta Telegram con la API del agente (que sí funciona perfecto):
>
> ```
> Telegram (long-polling) → OpenFang /v1/chat/completions (gpt-4o-mini) → Telegram sendMessage
> ```

Arranque del puente (con el token ya en `.env`):
```powershell
python src/scripts/telegram_bridge.py        # o: make openfang-telegram
# Imprime "Puente activo para @RioPaila_Bot" y queda escuchando.
```
Luego, escribir al bot **@RioPaila_Bot** desde Telegram (p. ej. *"¿Cuál es el NIT de Riopaila
Castilla?"*) devuelve la respuesta del agente. El puente debe quedar corriendo durante la demo.

---

## 5. Hallazgo técnico (decisión de diseño justificada)

Durante el despliegue se documentó, con evidencia en los logs de sesión, que **OpenFang v0.6.9
tiene un bug en su *agent-loop*** con varios modelos locales:

- Con `gemma3:4b` y `qwen2.5:3b` el agente recibe **un solo token** y entra en bucle infinito
  ("##" / "Okay" → "Please continue" → …), nunca completa la respuesta.
- Esto ocurre tanto por el driver nativo de Ollama como por la API OpenAI-compatible de Ollama.
- Los **mismos modelos responden perfecto directo en Ollama** (`/api/chat`) y alcanzan **100% GPU**.
- El único modelo local que responde completo dentro del loop es `llama3.2:3b`, pero su calidad
  (3B) es insuficiente (ignora datos del contexto).

**Decisión:** usar **`gpt-4o-mini`** como backend del agente conversacional (fiable, sin
alucinaciones, ya disponible con créditos del Módulo 2). La **ruta 100% local con Ollama + GPU**
queda **instalada y documentada** como capacidad demostrada y para futuras versiones de OpenFang
que corrijan el bug. El backend se cambia en una línea de `~/.openfang/config.toml`.

---

## 6. Comandos útiles (demo)

```powershell
$of = "$env:USERPROFILE\.openfang\bin\openfang.exe"

& $of status                       # estado del daemon (provider/model/agentes)
& $of dashboard                    # abre http://127.0.0.1:4200
& $of agent list                   # lista de agentes
& $of memory list riopaila-institucional   # datos en el KV Store
& $of hand active                  # hands en ejecución

# Chatear con el agente (UUID en openfang/.agent_id)
& $of message <UUID> "¿Qué productos fabrica Riopaila Castilla?"
```

Atajos del repo: `make help` → targets `openfang-start`, `openfang-status`, `openfang-spawn`,
`openfang-kv`, `openfang-hand`, `openfang-migrate`.

---

## 7. Estado final

| Componente | Estado |
|---|---|
| OpenFang daemon + dashboard | ✅ operativo |
| Agente `riopaila-institucional` (gpt-4o-mini, temp 0.0) | ✅ responde sin alucinaciones |
| Migración de conocimiento (KV Store, 49 pares) | ✅ |
| Hand `riopaila-inteligencia` | ✅ activo |
| Ollama local + 100% GPU (gemma3 / qwen2.5) | ✅ demostrado |
| Artefactos en el repo + documentación | ✅ |
| Canal de Telegram (@RioPaila_Bot, vía puente) | ✅ operativo — puente corriendo |
