#!/usr/bin/env python3
"""Genera docs/tsne_conversaciones.png desde conversation_logs (bonus M3)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from langchain_openai import OpenAIEmbeddings  # noqa: E402
from sklearn.manifold import TSNE  # noqa: E402
from supabase import create_client  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
load_dotenv(ROOT / ".env")


def _label(msg: str) -> str:
    m = (msg or "").lower()
    if "nit" in m or "legal" in m or "razón" in m or "razon" in m:
        return "legal/NIT"
    if "contacto" in m or "teléfono" in m or "telefono" in m or "correo" in m:
        return "contacto"
    if "junta" in m or "directiva" in m:
        return "gobierno"
    if "sostenib" in m or "ambient" in m or "certific" in m:
        return "sostenibilidad"
    if "línea" in m or "linea" in m or "negocio" in m or "caña" in m or "cana" in m:
        return "negocio"
    return "otros"


def main() -> int:
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()
    if not url or not key:
        print("[XX] Faltan SUPABASE_URL o SUPABASE_KEY en .env")
        return 1

    client = create_client(url, key)
    rows = (
        client.table("conversation_logs")
        .select("session_id, transcript, user_message, channel")
        .order("created_at", desc=True)
        .limit(500)
        .execute()
        .data
    )
    n = len(rows or [])
    print(f"Conversaciones cargadas: {n}")
    if n < 5:
        print("[XX] Pocas filas. Ejecuta: python scripts/seed_conversation_logs.py --api http://127.0.0.1:8000")
        return 1

    texts = [r.get("transcript") or r.get("user_message", "") for r in rows]
    labels = [_label(r.get("user_message", "")) for r in rows]

    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    vectors = np.array(OpenAIEmbeddings(model=model).embed_documents(texts))
    print("Embeddings shape:", vectors.shape)

    perplexity = min(30, max(5, len(texts) // 3))
    xy = TSNE(n_components=2, perplexity=perplexity, random_state=42).fit_transform(vectors)

    palette = {
        "legal/NIT": "#1b5e20",
        "contacto": "#2e7d32",
        "gobierno": "#f57c00",
        "sostenibilidad": "#0288d1",
        "negocio": "#6a1b9a",
        "otros": "#757575",
    }

    plt.figure(figsize=(11, 8))
    for lab in sorted(set(labels)):
        mask = np.array(labels) == lab
        plt.scatter(
            xy[mask, 0],
            xy[mask, 1],
            label=f"{lab} ({mask.sum()})",
            alpha=0.75,
            c=palette.get(lab, "#333"),
        )
    plt.legend(title="Intencion (heuristica)")
    plt.title("t-SNE - conversaciones del asistente Riopaila")
    plt.xlabel("t-SNE 1")
    plt.ylabel("t-SNE 2")
    plt.tight_layout()

    out = ROOT / "docs" / "tsne_conversaciones.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, dpi=150)
    print(f"[OK] Guardado: {out}")

    for lab in sorted(set(labels)):
        cnt = sum(1 for x in labels if x == lab)
        print(f"  - {lab}: {cnt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
