"""
tsne_analysis.py — Ruta Transversal B: análisis de comportamiento con t-SNE.

Pipeline:
  1. EXTRACCIÓN  — lee el historial de interacciones desde las sesiones JSONL de OpenFang
                   (~/.openfang/workspaces/<agente>/sessions/*.jsonl).
  2. VECTORIZACIÓN — convierte los mensajes de usuario en embeddings (OpenAI
                   text-embedding-3-small, 1536 dims). Cachea en data/analysis/embeddings.json.
  3. REDUCCIÓN   — proyecta a 2D con t-SNE (sklearn).
  4. CLÚSTERES   — KMeans para descubrir agrupaciones de intención.
  5. VISUALIZACIÓN — gráfico 2D (coloreado por intención real y por clúster) → PNG.
  6. INTERPRETACIÓN — imprime, por clúster, la intención dominante y ejemplos.

Uso:
    python src/scripts/tsne_analysis.py
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE

REPO_ROOT = Path(__file__).resolve().parents[2]
# Solo las sesiones de NUESTROS agentes (evita ticks de health-tracker/ops/orchestrator, etc.)
SESSIONS_GLOB = list((Path.home() / ".openfang" / "workspaces").glob("riopaila*/sessions/*.jsonl"))
OUT_DIR = REPO_ROOT / "data" / "analysis"
LABELS_PATH = OUT_DIR / "intent_labels.json"
EMB_CACHE = OUT_DIR / "embeddings.json"
PNG_PATH = OUT_DIR / "tsne_intenciones.png"
EMBED_MODEL = "text-embedding-3-small"

# Mensajes a excluir (ruido, no son intenciones de usuario)
SKIP = {"please continue.", "/start", "/help", "ok", "okay", "##", "¡", ""}


def load_env_key() -> str:
    import os
    if os.environ.get("OPENAI_API_KEY"):
        return os.environ["OPENAI_API_KEY"]
    env = (REPO_ROOT / ".env").read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"^\s*OPENAI_API_KEY\s*=\s*(.+?)\s*$", env, re.MULTILINE)
    if not m:
        raise SystemExit("No se encontró OPENAI_API_KEY (ni en entorno ni en .env).")
    return m.group(1).strip()


def extract_user_messages() -> list[str]:
    seen, msgs = set(), []
    for f in SESSIONS_GLOB:
        for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("role") != "user":
                continue
            text = (obj.get("content") or "").strip()
            key = text.lower()
            # descarta ruido: comandos, ticks programados/autónomos y mensajes de sistema ([...])
            if not text or key in SKIP or text.startswith("["):
                continue
            if key in seen:
                continue
            seen.add(key)
            msgs.append(text)
    return msgs


def embed(texts: list[str], api_key: str) -> np.ndarray:
    from openai import OpenAI
    cache = {}
    if EMB_CACHE.exists():
        cache = json.loads(EMB_CACHE.read_text(encoding="utf-8"))
    client = OpenAI(api_key=api_key)
    pending = [t for t in texts if t not in cache]
    for i in range(0, len(pending), 100):
        batch = pending[i : i + 100]
        resp = client.embeddings.create(model=EMBED_MODEL, input=batch)
        for t, d in zip(batch, resp.data):
            cache[t] = d.embedding
    EMB_CACHE.write_text(json.dumps(cache), encoding="utf-8")
    return np.array([cache[t] for t in texts], dtype=np.float32)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    msgs = extract_user_messages()
    n_jsonl = len(msgs)
    labels_map = json.loads(LABELS_PATH.read_text(encoding="utf-8")) if LABELS_PATH.exists() else {}

    # Une el historial real (JSONL de agentes riopaila) con las interacciones sembradas
    # registradas en intent_labels.json (son las preguntas efectivamente enviadas al agente).
    seen = {m.lower() for m in msgs}
    for q in labels_map:
        if q.lower() not in seen:
            msgs.append(q)
            seen.add(q.lower())

    print(f"Mensajes analizados: {len(msgs)} "
          f"({n_jsonl} del historial JSONL riopaila + {len(msgs) - n_jsonl} sembrados)")
    if len(msgs) < 6:
        raise SystemExit("Muy pocos mensajes para t-SNE. Corre seed_interactions.py primero.")

    intents = [labels_map.get(m, "otro") for m in msgs]

    X = embed(msgs, load_env_key())
    # Normalización L2 → distancia euclidiana sobre vectores unitarios ≡ similitud coseno,
    # la métrica adecuada para embeddings de texto.
    Xn = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)
    print(f"Embeddings: {X.shape} (normalizados L2)")

    n = len(msgs)
    perp = max(5, min(30, n // 3))
    coords = TSNE(n_components=2, perplexity=perp, init="pca", metric="cosine",
                  learning_rate="auto", random_state=7).fit_transform(X)

    # KMeans sobre los embeddings normalizados (1536-D, ≈ k-means esférico/coseno): más fiel que
    # agrupar sobre el 2D de t-SNE, que es solo una proyección para visualizar.
    k = max(2, len(set(i for i in intents if i != "otro")) or 8)
    k = min(k, n)  # KMeans exige n_clusters <= n_muestras
    km = KMeans(n_clusters=k, n_init=10, random_state=7).fit(Xn)
    clusters = km.labels_

    # ── Gráfico: dos paneles ────────────────────────────────────────────────
    uniq_intents = sorted(set(intents))
    cmap = plt.get_cmap("tab10")
    color_by_intent = {it: cmap(i % 10) for i, it in enumerate(uniq_intents)}

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    for it in uniq_intents:
        pts = coords[[j for j, x in enumerate(intents) if x == it]]
        axes[0].scatter(pts[:, 0], pts[:, 1], s=60, alpha=0.8,
                        color=color_by_intent[it], label=it)
    axes[0].set_title("t-SNE de intenciones (etiqueta real)")
    axes[0].legend(fontsize=8, loc="best")

    sc = axes[1].scatter(coords[:, 0], coords[:, 1], s=60, alpha=0.8,
                         c=clusters, cmap="tab10")
    axes[1].set_title(f"t-SNE + KMeans (k={k}, clústeres descubiertos)")
    for ax in axes:
        ax.set_xlabel("dim 1"); ax.set_ylabel("dim 2")

    fig.suptitle("Riopaila Castilla — Análisis de comportamiento de usuarios (OpenFang)",
                 fontsize=14)
    fig.tight_layout()
    fig.savefig(PNG_PATH, dpi=130, bbox_inches="tight")
    print(f"Gráfico guardado en {PNG_PATH}")

    # ── Interpretación: intención dominante por clúster + pureza ────────────
    print("\n=== Interpretación de clústeres ===")
    purities = []
    for c in range(k):
        idx = [j for j in range(n) if clusters[j] == c]
        counts = Counter(intents[j] for j in idx)
        dom, dom_n = counts.most_common(1)[0]
        purity = dom_n / len(idx)
        purities.append(purity)
        ejemplos = [msgs[j] for j in idx[:3]]
        print(f"\nClúster {c}: {len(idx)} mensajes | intención dominante = '{dom}' "
              f"(pureza {purity:.0%})")
        for e in ejemplos:
            print(f"    - {e}")
    print(f"\nPureza media de clústeres: {np.mean(purities):.0%}")


if __name__ == "__main__":
    main()
