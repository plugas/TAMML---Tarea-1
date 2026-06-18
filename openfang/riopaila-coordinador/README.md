# `riopaila-coordinador/` — Agente router del sistema multi-agente

![OpenFang](https://img.shields.io/badge/OpenFang-agent-FF6B35)
![OpenAI](https://img.shields.io/badge/modelo-default%20(gpt--4o--mini)-412991?logo=openai&logoColor=white)

Manifiesto del agente coordinador (router) del sistema multi-agente de Riopaila Castilla. Es el **punto de entrada único**: recibe todas las consultas desde el canal Telegram y decide a qué especialista delegarlas.

## Archivo

### `agent.toml`

Define el comportamiento completo del agente en el runtime OpenFang.

**Parámetros del modelo:**

| Parámetro | Valor | Por qué |
|---|---|---|
| `max_tokens` | `2048` | Suficiente para la respuesta del especialista más contexto de enrutamiento |
| `temperature` | `0.1` | Casi determinista; permite pequeñas variaciones en frases de presentación |
| `provider` | `default` | Hereda el modelo configurado en `~/.openfang/config.toml` |

**Herramientas registradas:**

| Tool | Para qué |
|---|---|
| `agent_list` | Consulta qué agentes están activos en el OS antes de delegar |
| `agent_send` | Envía la consulta al especialista seleccionado y espera su respuesta |
| `memory_recall` | Consulta la memoria semántica del OS si necesita contexto adicional para enrutar |

**Lógica de enrutamiento (system prompt):**
- Pregunta puntual o FAQ (NIT, contacto, certificaciones, cifras) → `riopaila-faq`
- Pregunta narrativa, histórica o de gobierno corporativo → `riopaila-institucional`
- La respuesta al usuario incluye una indicación de qué especialista respondió

## Relación con los otros agentes

```
Usuario (Telegram)
       ↓
riopaila-coordinador  ←── este agente
       ↓ agent_send
  ┌────┴────┐
  ▼         ▼
riopaila-faq   riopaila-institucional
```
