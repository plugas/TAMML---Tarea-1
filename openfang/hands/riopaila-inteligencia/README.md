# `riopaila-inteligencia/` — Hand autónomo de inteligencia sectorial

![OpenFang](https://img.shields.io/badge/OpenFang-Hands%20System-FF6B35)
![OpenAI](https://img.shields.io/badge/OpenAI-gpt--4o--mini-412991?logo=openai&logoColor=white)

Manifiesto del **Hand autónomo** del sistema (Opción B — Perfil Analítico / "Collector"). Un Hand en OpenFang es un agente que ejecuta tareas programadas de forma autónoma, sin input humano. Este Hand monitorea la inteligencia sectorial del azúcar y agroindustria colombiana de manera continua.

## Archivos

### `HAND.toml` — Playbook del Hand

Define el ciclo completo de operación autónoma en 4 fases:

| Fase | Nombre | Qué hace |
|---|---|---|
| **1** | `recoleccion` | Ejecuta búsquedas web (`web_search`) sobre el sector azucarero y agroindustrial colombiano. Consultas parametrizables: competidores, precios, regulación, clima, mercados. |
| **2** | `clasificacion` | Clasifica cada hallazgo como `OPORTUNIDAD`, `RIESGO` o `NEUTRAL` con una puntuación de relevancia 1–10. El criterio es el impacto potencial sobre Riopaila Castilla. |
| **3** | `consolidacion` | Deduplica hallazgos de ciclos anteriores, prioriza por relevancia y descarta los de baja puntuación (< umbral configurable). |
| **4** | `reporte` | Genera un reporte en Markdown con los hallazgos clasificados y lo persiste en la memoria del OS. Puede configurarse para enviarlo por canal. |

**Settings del HAND.toml:**

| Setting | Descripción |
|---|---|
| `subject` | Tema de vigilancia (sector azucarero colombiano) |
| `frequency` | Frecuencia del ciclo autónomo (configurable, default diario) |
| `focus` | Áreas de interés (precios, clima, competidores, regulación) |
| `output_format` | Formato del reporte (`markdown`) |
| `relevance_threshold` | Puntuación mínima para incluir un hallazgo (1–10) |

**Métricas del Hand** (visibles en dashboard `:4200`):
- Ciclos ejecutados
- Hallazgos clasificados totales
- Timestamp del último reporte

---

### `SKILL.md` — Conocimiento de dominio

Documento de contexto que el Hand usa como referencia durante la clasificación. Contiene:
- Descripción del sector azucarero colombiano
- Principales competidores y actores del mercado
- Variables clave de impacto (precio internacional del azúcar, clima en el Valle del Cauca, política de biocombustibles)
- Criterios para clasificar como OPORTUNIDAD vs RIESGO

## Activación

```bash
make openfang-hand   # instala el Hand en el runtime y lo activa
```

El Hand comienza a ejecutar ciclos autónomamente según la frecuencia configurada. El primer ciclo corre inmediatamente al activarse.
