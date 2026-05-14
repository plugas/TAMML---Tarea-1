"""Rutas centralizadas del paquete riopaila_rag."""

from pathlib import Path

# Raíz del proyecto (tres niveles arriba de este archivo: src/riopaila_rag/paths.py)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Directorio de assets (imágenes, hero carousel, logos)
ASSETS_DIR = Path(__file__).resolve().parent / "assets"

# Base de conocimiento consolidada
DATA_DIR = ROOT_DIR / "data" / "knowledge"
PATH_CONSOLIDADO = DATA_DIR / "riopaila_castilla_clean.md"

# Lista vacía: sin fusión automática de insumos
ARCHIVOS_INSUMO_CONSOLIDADO: tuple[str, ...] = ()
