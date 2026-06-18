# `openfang/` — Módulo 3: Agente corporativo sobre OpenFang Agent OS (Ruta B)

![OpenFang](https://img.shields.io/badge/OpenFang-Agent%20OS%20v0.6.9-FF6B35)
![Rust](https://img.shields.io/badge/Rust-runtime-000000?logo=rust&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-gpt--4o--mini-412991?logo=openai&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-local%20LLM-000000?logo=ollama&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-@RioPaila__Bot-26A5E4?logo=telegram&logoColor=white)

Manifiestos (`.toml`) que definen el sistema **multi-agente** de Riopaila Castilla sobre **[OpenFang](https://github.com/RightNow-AI/openfang)**, un *Agent OS* escrito en **Rust** (MIT/Apache-2.0). El kernel corre como daemon en `127.0.0.1:4200` y expone una API **compatible con OpenAI**.

> Esta carpeta es la **fuente versionada** de la configuración. Los agentes se despliegan copiando/registrando estos manifiestos en el runtime (`~/.openfang/`). El binario y el estado del daemon viven fuera del repo.

## Arquitectura

```
Telegram (@RioPaila_Bot) ──▶ telegram_bridge.py ──▶ OpenFang API (:4200)
                                                          │
                                              riopaila-coordinador  (router)
                                                    │ agent_send │
                                       ┌────────────┘            └────────────┐
                                       ▼                                      ▼
                               riopaila-faq                        riopaila-institucional
                            (rápida, ≤3 frases)                    (detallada / histórica)

   Hand autónomo:  riopaila-inteligencia  (vigilancia sectorial programada)
   Memoria del OS:  KV Store (43 datos) + Vector Store (documentos)
```

## Contenido

| Ruta | Qué define |
|---|---|
| `riopaila-coordinador/agent.toml` | **Router** multi-agente. Clasifica la consulta y delega vía `agent_send` en el especialista adecuado. `tools = [agent_list, agent_send, memory_recall]`, `temp 0.1`. |
| `riopaila-institucional/agent.toml` | Asistente **detallado**. Lleva los **datos verificados como identidad base** en el system prompt (NIT, fundación 1918 vs fusión 2007, sedes, cifras, certificaciones, contacto) → anti-alucinación. `temp 0.0`, `seed 7`, `max_tokens 4096`. Chat puro (sin tools). |
| `riopaila-faq/agent.toml` | Especialista de **respuestas rápidas** (1–3 frases). `temp 0.0`, `seed 7`, `max_tokens 512`. |
| `hands/riopaila-inteligencia/HAND.toml` | **Hand autónomo** (playbook). Monitor de inteligencia sectorial (perfil "Collector"): recolecta (web_search), clasifica hallazgos como OPORTUNIDAD/RIESGO/NEUTRAL con relevancia 1–10, genera reportes programados y persiste el ciclo en memoria. Configurable (sujeto, frecuencia, enfoque, formato). |
| `hands/riopaila-inteligencia/SKILL.md` | Conocimiento de dominio sectorial que usa el Hand. |
| `config.toml.example` | Plantilla de `~/.openfang/config.toml` (modelo por defecto, memoria, compactación, canal Telegram). |
| `Modelfile.gemma3-gpu` | Modelfile de Ollama (`num_gpu 99`) para correr `gemma3:4b` a **100% GPU** (ruta local de soberanía de datos). |

## Decisiones clave

- **Identidad base permanente:** los datos verificados van en el system prompt del agente institucional para garantizar respuestas correctas incluso con modelos locales pequeños (que no invocan `memory_recall` de forma fiable). La memoria (KV + semántica) **complementa**.
- **Modelo recomendado `gpt-4o-mini`:** fiable en el agent-loop de OpenFang. La ruta local (Ollama, `gemma3:4b`/`qwen2.5:3b` a 100% GPU) queda instalada y documentada, pero en **v0.6.9** esos modelos rompen el agent-loop (bucle `##`); `llama3.2:3b` funciona pero con calidad limitada.
- **Puente de Telegram propio:** el canal nativo de OpenFang v0.6.9 da 404 al activarse; `telegram_bridge.py` lo sortea con long-polling.

## Despliegue

```bash
make openfang-start     # daemon (API + dashboard :4200)
make openfang-spawn     # despliega institucional + faq + coordinador
make openfang-migrate   # KV Store + memoria semántica
make openfang-hand      # instala y activa el Hand de inteligencia
make openfang-telegram  # puente Telegram (@RioPaila_Bot)
```

Configuración previa: copiar `config.toml.example` → `~/.openfang/config.toml` y exportar `OPENAI_API_KEY` + `TELEGRAM_BOT_TOKEN`.

> Guía reproducible: [`docs/runbook-openfang.md`](../docs/runbook-openfang.md). Documentación técnica de entrega: [`docs/entrega-modulo3-openfang.md`](../docs/entrega-modulo3-openfang.md).
