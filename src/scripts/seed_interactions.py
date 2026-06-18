"""
seed_interactions.py — Puebla el historial de interacciones de OpenFang con preguntas
representativas de varias intenciones, para luego analizarlas con t-SNE.

Envía cada pregunta al agente `riopaila-faq` vía el CLI `openfang message` (que persiste
la conversación en los archivos JSONL de sesión que lee el análisis). Además guarda un mapa
pregunta→intención en data/analysis/intent_labels.json para interpretar los clústeres.

En producción este paso NO es necesario (el historial lo generan los usuarios reales); aquí
solo siembra datos variados para demostrar el análisis.

Uso:
    python src/scripts/seed_interactions.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "data" / "analysis"
AGENT_NAME = "riopaila-faq"

# 8 intenciones × 6 formulaciones = 48 preguntas
INTENTS: dict[str, list[str]] = {
    "contacto": [
        "¿Cuál es el correo de la línea ética de Riopaila Castilla?",
        "¿Cómo contacto al área de proveedores?",
        "¿Cuál es la página web oficial de la empresa?",
        "Dame el correo de la oficina de cumplimiento.",
        "¿A qué correo escribo para comprar miel?",
        "¿Cómo me comunico con Riopaila Castilla?",
    ],
    "productos": [
        "¿Qué productos fabrica Riopaila Castilla?",
        "¿Producen etanol o alcohol carburante?",
        "¿Qué tipos de azúcar venden?",
        "¿Riopaila genera energía eléctrica?",
        "¿Qué derivados de la caña ofrecen?",
        "¿Tienen línea de aceite de palma?",
    ],
    "certificaciones": [
        "¿Qué certificaciones ISO tiene la empresa?",
        "¿Riopaila Castilla está certificada en calidad?",
        "¿Tienen certificación ambiental?",
        "¿El producto es libre de gluten?",
        "¿Cuentan con certificación vegana o non-GMO?",
        "¿Qué acreditaciones tiene su laboratorio?",
    ],
    "historia": [
        "¿En qué año fue fundada Riopaila Castilla?",
        "¿Quién fundó la empresa?",
        "Cuéntame la historia de Riopaila Castilla.",
        "¿Cuándo ocurrió la fusión que formó la empresa?",
        "¿Cómo evolucionó la compañía desde sus inicios?",
        "¿Qué origen tiene el ingenio Riopaila?",
    ],
    "sostenibilidad": [
        "¿Qué iniciativas de sostenibilidad tiene la empresa?",
        "¿Desde cuándo publican informe de sostenibilidad?",
        "¿Qué hace la Fundación Caicedo González Riopaila Castilla?",
        "¿Cómo aporta Riopaila al medio ambiente?",
        "¿Tienen prácticas de agricultura sostenible?",
        "¿Bajo qué estándar reportan su gestión sostenible?",
    ],
    "cifras": [
        "¿Cuántos empleados tiene Riopaila Castilla?",
        "¿A cuántos países llegan sus productos?",
        "¿A cuántos hogares llega la empresa?",
        "¿Cuánta energía cogeneran?",
        "¿Cuántos aliados tiene en su cadena de abastecimiento?",
        "¿Cuántos vehículos oxigena su etanol?",
    ],
    "ubicacion": [
        "¿Dónde queda la planta Riopaila?",
        "¿En qué ciudad están las oficinas administrativas?",
        "¿Dónde está la planta Castilla?",
        "¿En qué regiones opera la empresa?",
        "¿Cuál es el domicilio principal de Riopaila Castilla?",
        "¿Tienen operaciones en el Vichada?",
    ],
    "empleo": [
        "¿Cómo puedo trabajar en Riopaila Castilla?",
        "¿Dónde publican las vacantes?",
        "¿Tienen ofertas de empleo?",
        "¿Cómo aplico a un trabajo en la empresa?",
        "¿Cada cuánto publican vacantes?",
        "¿Dónde encuentro el portal de empleo?",
    ],
}


def find_openfang() -> str:
    exe = shutil.which("openfang")
    if exe:
        return exe
    default = Path.home() / ".openfang" / "bin" / (
        "openfang.exe" if os.name == "nt" else "openfang"
    )
    if default.exists():
        return str(default)
    raise SystemExit("No se encontró el binario 'openfang'.")


def resolve_agent_uuid(of: str, name: str) -> str:
    out = subprocess.run([of, "agent", "list"], capture_output=True, text=True,
                         encoding="utf-8").stdout
    for line in out.splitlines():
        if name in line:
            import re
            m = re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", line)
            if m:
                return m.group(0)
    raise SystemExit(f"No se encontró el agente '{name}' en ejecución.")


def main() -> None:
    of = find_openfang()
    uuid = resolve_agent_uuid(of, AGENT_NAME)
    print(f"Agente {AGENT_NAME} = {uuid}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    labels: dict[str, str] = {}
    n, total = 0, sum(len(v) for v in INTENTS.values())

    for intent, questions in INTENTS.items():
        for q in questions:
            labels[q] = intent
            n += 1
            subprocess.run([of, "message", uuid, q], capture_output=True,
                           text=True, encoding="utf-8")
            print(f"  [{n}/{total}] ({intent}) {q}")
            time.sleep(0.2)

    (OUT_DIR / "intent_labels.json").write_text(
        json.dumps(labels, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Listo. {n} interacciones sembradas. Etiquetas en {OUT_DIR/'intent_labels.json'}")


if __name__ == "__main__":
    main()
