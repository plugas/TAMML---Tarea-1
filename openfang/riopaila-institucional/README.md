# `riopaila-institucional/` — Agente especialista en respuestas detalladas

![OpenFang](https://img.shields.io/badge/OpenFang-agent-FF6B35)
![OpenAI](https://img.shields.io/badge/modelo-default%20(gpt--4o--mini)-412991?logo=openai&logoColor=white)

Manifiesto del agente institucional de Riopaila Castilla. Responde a preguntas **narrativas, históricas y de gobierno corporativo** con respuestas extensas y bien estructuradas. Es el agente con mayor contexto embebido del sistema.

## Archivo

### `agent.toml`

**Parámetros del modelo:**

| Parámetro | Valor | Por qué |
|---|---|---|
| `max_tokens` | `4096` | Permite respuestas largas con contexto completo e histórico |
| `temperature` | `0.0` | Determinista: datos corporativos sensibles requieren reproducibilidad |
| `seed` | `7` | Fijado para garantizar consistencia entre sesiones distintas |
| `provider` | `default` | Hereda el modelo del daemon |

**Identidad base (system prompt):**

Lleva embebidos todos los datos verificados de la empresa como parte de su identidad, no como contexto recuperable. Esto garantiza que incluso con modelos locales pequeños (Ollama, llama3.2:3b) el agente responda correctamente sin depender de `memory_recall`:

- Historia completa: fundación 1918 (Riopaila) + 2007 (fusión con Castilla)
- Líneas de negocio y productos
- Gobierno corporativo (Junta Directiva, estructura legal)
- Sostenibilidad e iniciativas ambientales
- Certificaciones con contexto (qué certifica cada una)
- Datos de contacto completos

**Sin herramientas:** este agente es puramente conversacional (`module = "builtin:chat"`). El coordinador ya filtró la consulta antes de delegarla; no necesita hacer búsquedas adicionales.

## Cuándo lo invoca el coordinador

- "¿Cuál es la historia de Riopaila Castilla?"
- "Explícame el proceso de cogeneración de energía"
- "¿Cómo está compuesta la Junta Directiva?"
- "¿Qué hace la empresa en sostenibilidad?"
- Cualquier pregunta que requiera más de 3 frases de respuesta
