# `docs/` — Documentación técnica del proyecto

![Markdown](https://img.shields.io/badge/Markdown-docs-000000?logo=markdown&logoColor=white)
![PDF](https://img.shields.io/badge/PDF-informe-E94E1B)

Documentación técnica de las tres entregas del proyecto Riopaila Castilla. Todos los archivos son de referencia permanente para entender la arquitectura, reproducir el sistema y operar el Módulo 3.

## Archivos

| Archivo | Qué contiene |
|---|---|
| `INFORME_TECNICO_MODULO3.pdf` | Informe técnico final del Módulo 3: arquitectura end-to-end, decisiones de diseño, parámetros de los modelos, diagrama de flujo y análisis de resultados. Documento de entrega oficial. |
| `entrega-modulo3-openfang.md` | Documentación de entrega del Módulo 3 (Ruta B): descripción detallada de los agentes, relaciones entre ellos, parámetros de modelos (temperatura, seed, max_tokens) y guía de despliegue del canal Telegram. |
| `runbook-openfang.md` | Guía reproducible paso a paso para levantar el sistema desde cero: instalación del daemon, despliegue de agentes, migración de memoria (KV Store + Vector Store), activación del Hand autónomo y configuración del puente Telegram. |
| `analisis-tsne.md` | Documentación del análisis Ruta Transversal B: metodología t-SNE + KMeans sobre embeddings de interacciones, interpretación de los clústeres de intención y métricas de pureza. |

## Lo que NO está aquí

- Los guiones de sustentación (`GUION_*.md`) están ignorados por git — son apoyo personal, no documentación del proyecto.
- El código del análisis t-SNE está en `src/scripts/tsne_analysis.py` y `notebooks/analisis_tsne.ipynb`.
- La configuración de los agentes está en `openfang/`.
