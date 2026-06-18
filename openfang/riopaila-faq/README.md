# `riopaila-faq/` — Agente especialista en respuestas rápidas

![OpenFang](https://img.shields.io/badge/OpenFang-agent-FF6B35)
![OpenAI](https://img.shields.io/badge/modelo-default%20(gpt--4o--mini)-412991?logo=openai&logoColor=white)

Manifiesto del agente especialista en preguntas frecuentes. Responde con **1 a 3 frases** a consultas puntuales sobre datos verificados de Riopaila Castilla. No usa herramientas externas — todo el conocimiento factual está embebido en su system prompt.

## Archivo

### `agent.toml`

**Parámetros del modelo:**

| Parámetro | Valor | Por qué |
|---|---|---|
| `max_tokens` | `512` | Limita la extensión de la respuesta — este agente debe ser breve |
| `temperature` | `0.0` | Completamente determinista: misma pregunta = misma respuesta |
| `seed` | `7` | Reproducibilidad garantizada entre ejecuciones |
| `provider` | `default` | Hereda el modelo del daemon (`~/.openfang/config.toml`) |

**Conocimiento embebido en el system prompt:**

Los datos verificados se inyectan directamente como identidad base del agente:
- NIT: `900.087.414-4`
- Año de fundación: `1918` (fusión con Castilla: `2007`)
- Sedes (Valle del Cauca)
- Certificaciones (ISO 9001/14001/17025, FSSC 22000, Rainforest Alliance, Gluten Free, Non-GMO, Vegan)
- Contactos (PBX, emails de proveedores, línea ética, ventas)
- Segmentos de negocio (azúcar, alcohol carburante, cogeneración, mieles, aceite de palma)

**Por qué sin herramientas:** la latencia de `memory_recall` o `rag_search` es innecesaria para preguntas frecuentes. El dato canónico ya está en el prompt → respuesta inmediata sin round-trip al OS.

## Cuándo lo invoca el coordinador

- "¿Cuál es el NIT?"
- "¿Cómo contacto a proveedores?"
- "¿Qué certificaciones tiene?"
- Cualquier pregunta cuya respuesta sea un dato puntual conocido
