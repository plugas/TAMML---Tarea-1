# `notebooks/` — Análisis exploratorio (Ruta Transversal B)

![Jupyter](https://img.shields.io/badge/Jupyter-notebook-F37626?logo=jupyter&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-t--SNE%20%2B%20KMeans-F7931E?logo=scikit-learn&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-text--embedding--3--small-412991?logo=openai&logoColor=white)

Notebooks de análisis de datos del proyecto. Corresponden a la **Ruta Transversal B**: análisis del comportamiento de usuarios a partir del historial de interacciones del agente OpenFang.

## Archivos

### `analisis_tsne.ipynb`

Notebook interactivo que implementa el pipeline completo de análisis t-SNE sobre las conversaciones del bot:

| Sección | Qué hace |
|---|---|
| **1. Extracción** | Lee el historial de interacciones en formato JSONL desde el daemon de OpenFang (`tsne_analysis.TsneAnalyzer.extract_user_messages()`). |
| **2. Vectorización** | Embebe cada mensaje con `text-embedding-3-small` de OpenAI (1536 dimensiones). Los embeddings se cachean en `data/analysis/embeddings.json` para evitar llamadas repetidas a la API. |
| **3. t-SNE** | Reducción de 1536D → 2D con `sklearn.manifold.TSNE` (`perplexity=30`, `n_iter=1000`, `random_state=7`). |
| **4. KMeans** | Agrupación en `k` clústeres (k = número de intenciones únicas detectadas, mínimo 2). Guarda etiquetas en `data/analysis/intent_labels.json`. |
| **5. Visualización** | Scatter plot coloreado por clúster con `matplotlib`. Salida: `data/analysis/tsne_intenciones.png`. |
| **6. Interpretación** | Calcula pureza por clúster e identifica las intenciones dominantes (contacto, productos, historia, certificaciones…). |

## Dependencias

Requiere el extra `analysis` del proyecto:

```
uv sync --extra analysis
```

Instala: `numpy`, `scikit-learn`, `matplotlib`. El notebook consume la misma lógica que el script `src/scripts/tsne_analysis.py` (`make tsne`), pero de forma interactiva con visualización inline.

## Salidas

- `data/analysis/tsne_intenciones.png` — gráfico final de clústeres.
- `data/analysis/embeddings.json` — caché de embeddings (evita costo repetido de API).
- `data/analysis/intent_labels.json` — etiquetas de intención por mensaje (generadas por `make tsne-seed`).
