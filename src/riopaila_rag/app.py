"""
Asistente Virtual Riopaila Castillo — Streamlit (tema claro, paleta institucional verde + terracota + burdeos).
Ejecutar: streamlit run src/riopaila_rag/app.py

Núcleo Módulo 1 (Q&A sin RAG vectorial): base consolidada + chunking LangChain + Groq en Resumen, FAQ y Q&A.
GROQ_API_KEY: entorno o .streamlit/secrets.toml
Opcional: `KB_MAX_CONTEXT_CHARS` (por defecto 12_000) y `KB_MAX_CONTEXT_CHARS_TEMATICO` (propósito/pie/líneas; por defecto ~5_500) para ajustar uso de TPM en Groq. Si ves error 429, espera ~1 min o baja esos valores.
"""

from __future__ import annotations

from typing import Literal

import base64
import html
import io
import json
import os
import re
import secrets
from datetime import datetime
from urllib.parse import quote, unquote

import streamlit as st
import streamlit.components.v1 as components

from riopaila_rag.kb import (
    contexto_para_prompt,
    estadisticas_base,
    exportar_muestra_chunks,
    invocar_faq,
    invocar_linea_negocio,
    invocar_mensaje_cierre_resumen,
    invocar_proposito_tarjeta_resumen,
    invocar_qa,
    invocar_resumen,
)
from riopaila_rag.paths import PATH_CONSOLIDADO

# --- Paleta institucional Riopaila (verde + terracota + burdeos) ---
C_BG = "#f5f7f9"
C_WHITE = "#ffffff"
C_GREEN = "#1b5e20"
C_GREEN_SOFT = "#e8f5e9"
# Terracota / naranja quemado — sustituye el azul anterior (FAQ, acentos, ilustraciones).
C_ORANGE = "#D9732A"
C_ORANGE_SOFT = "#fdf0e6"
C_ORANGE_SUB = "#B85A1E"
C_ORANGE_HOVER = "#C45F20"
C_ORANGE_MIST = "#f5d0b8"
# Burdeos / rojo vino — sustituye el amarillo anterior (Q&A).
C_BURGUNDY = "#8B2332"
C_BURGUNDY_SOFT = "#fcecec"
C_BURGUNDY_SUB = "#6B1A28"
C_BURGUNDY_HOVER = "#6B1A28"
C_BURGUNDY_MIST = "#e8b4b9"
C_BURGUNDY_FILL = "#fff5f7"
# Alias para clases CSS históricas (feat-head-blue, feat-btn--yellow, etc.)
C_BLUE = C_ORANGE
C_BLUE_SOFT = C_ORANGE_SOFT
C_YELLOW = C_BURGUNDY
C_YELLOW_SOFT = C_BURGUNDY_SOFT
C_TEXT = "#263238"
C_TEXT_MUTED = "#546e7a"
# FAQ — terracota / melocotón (tarjeta del inicio + pestaña FAQ, misma línea cromática)
C_FAQ_PRIMARY = "#9a3412"
C_FAQ_PRIMARY_MID = C_ORANGE
C_FAQ_SOFT = "#FEF5EF"
C_FAQ_SIDEBAR = C_WHITE
C_FAQ_SIDEBAR_BORDER = "#efe0d6"
C_FAQ_CALLOUT_BORDER = "#e5c6a8"
C_FAQ_ACCENT = C_ORANGE
C_FAQ_MIST = "#fffaf6"
C_FAQ_BTN_HOVER = C_ORANGE_HOVER
# Tintes suaves en sombras (alineado a C_ORANGE #D9732A)
C_FAQ_PRIMARY_RGB = "217, 115, 42"

_DIR = os.path.dirname(os.path.abspath(__file__))
HERO_IMAGE = os.path.join(_DIR, "assets", "hero_riopaila.png")
# Imágenes del carrusel del hero (orden alfabético). Si está vacío, se usa solo HERO_IMAGE.
HERO_CAROUSEL_DIR = os.path.join(_DIR, "assets", "hero_carousel")
LOGO_IMAGE = os.path.join(_DIR, "assets", "logo_riopaila.png")
LOGOTIPO_CARD_IMAGE = os.path.join(_DIR, "assets", "logotipo_riopaila.png")
_LOGOTIPO_CARD_CACHE: tuple[float | None, str | None] = (None, None)

# Enlaces oficiales (redes Riopaila Castillo)
SOCIAL_LINKEDIN = (
    "https://www.linkedin.com/company/riopaila-castilla-s.-a.?originalSubdomain=co"
)
SOCIAL_INSTAGRAM = "https://www.instagram.com/riopailacastilla/"
SOCIAL_YOUTUBE = "https://www.youtube.com/@RiopailaCastilla/videos"
SOCIAL_FACEBOOK = "https://www.facebook.com/riopailacastilla/"

MENU_NAV = [
    ("Inicio", "Inicio", "home"),
    ("Resumen", "Resumen", "doc"),
    ("FAQ (Preguntas Frecuentes)", "FAQ", "faq"),
    ("Q&A (Haz tu pregunta)", "Q&A", "chat"),
    ("Agente (RAG + Tools)", "Agente", "agent"),
]

PAGINAS_VALIDAS = {pid for _, pid, _ in MENU_NAV}

NAV_MATERIAL_ICON: dict[str, str] = {
    "home": ":material/home:",
    "doc": ":material/description:",
    "faq": ":material/help:",
    "chat": ":material/forum:",
    "agent": ":material/smart_toy:",
}

PLACEHOLDER_Q = "¿Cuál es la historia de Riopaila Castillo?"
PLACEHOLDER_A = (
    "Riopaila Castillo es una empresa colombiana con origen en el Valle del Cauca, "
    "con más de un siglo de trayectoria desde 1918, ligada al cultivo de caña de azúcar "
    "y a la transformación industrial. Hoy articula negocios de alimentos, energías "
    "renovables y biocombustibles, con énfasis en sostenibilidad y el territorio."
)

# Atajos Q&A: (etiqueta visible, texto al enviar, icono Material del botón)
QA_QUICK_TOPICS: list[tuple[str, str, str]] = [
    ("Productos y servicios", "¿Qué productos y servicios ofrece Riopaila Castillo?", ":material/inventory_2:"),
    ("Sostenibilidad", "¿Qué hace Riopaila Castillo en sostenibilidad y medio ambiente?", ":material/eco:"),
    ("Nuestras operaciones", "¿Dónde y cómo opera Riopaila Castillo?", ":material/factory:"),
    ("Noticias", "¿Dónde encuentro noticias e información oficial de Riopaila Castillo?", ":material/newspaper:"),
]

# Panel izquierdo Q&A: (pregunta al pulsar, icono Material)
QA_EJEMPLO_PREGUNTAS: list[tuple[str, str]] = [
    ("¿Cuál es la historia de Riopaila Castillo?", ":material/factory:"),
    ("¿Qué productos ofrece Riopaila Castillo?", ":material/inventory_2:"),
    ("¿Dónde están ubicadas sus operaciones?", ":material/location_on:"),
    ("¿Qué iniciativas de sostenibilidad tiene la empresa?", ":material/eco:"),
    ("¿Cómo puedo contactar a la empresa?", ":material/call:"),
]

# Tarjetas sugeridas del Agente (mismo patrón que Q&A pero adaptado al RAG)
AGENTE_QUICK_TOPICS: list[tuple[str, str, str]] = [
    ("Cifras clave", "¿Cuántos empleados tiene Riopaila Castilla y cuál es su capacidad de producción?", ":material/insights:"),
    ("Datos de contacto", "¿Cuáles son los canales de contacto oficiales de la empresa?", ":material/contact_phone:"),
    ("Certificaciones", "¿Qué certificaciones y normas tiene Riopaila Castilla?", ":material/verified:"),
    ("Sostenibilidad", "¿Qué metas e iniciativas de sostenibilidad reporta la empresa?", ":material/eco:"),
]

# Panel izquierdo Agente: (pregunta, icono)
AGENTE_EJEMPLO_PREGUNTAS: list[tuple[str, str]] = [
    ("¿Cuál es el NIT de Riopaila Castilla?", ":material/badge:"),
    ("Cuéntame la historia de la empresa", ":material/history_edu:"),
    ("¿Cuáles son las líneas de negocio?", ":material/category:"),
    ("¿Qué reporta el último informe de sostenibilidad?", ":material/description:"),
    ("¿Quiénes integran la Junta Directiva?", ":material/groups:"),
]

# Módulo 1 — al menos 20 preguntas de prueba (informe / demo); cargan el campo Q&A al pulsar.
MODULO1_PREGUNTAS_PRUEBA: tuple[str, ...] = (
    "¿Cuál es la historia y el origen de Riopaila Castillo?",
    "¿Qué productos y servicios ofrece la empresa hoy?",
    "¿En qué regiones o municipios tiene presencia operativa?",
    "¿Qué papel juega la caña de azúcar en su modelo de negocio?",
    "¿Qué es la cogeneración y cómo la relaciona la empresa con su proceso?",
    "¿Qué líneas de negocio aparecen en la información pública de la compañía?",
    "¿Qué dice la empresa sobre sostenibilidad o medio ambiente?",
    "¿Dónde puede un ciudadano consultar informes o memorias de gestión?",
    "¿Existen reportes de sostenibilidad o ESG mencionados en las fuentes?",
    "¿Qué canales digitales oficiales tiene la empresa (web, redes)?",
    "¿Qué tipo de contenidos publica la empresa en redes sociales según la documentación?",
    "¿Qué vínculo tiene la marca con el Valle del Cauca?",
    "¿Qué productos derivados de la caña se mencionan (si aparecen en el contexto)?",
    "¿La empresa habla de biocombustibles o etanol en sus textos?",
    "¿Qué información hay sobre energías renovables?",
    "¿Qué mensaje de propósito o misión se puede inferir del contexto?",
    "¿Cómo recomienda la empresa verificar información oficial frente a rumores?",
    "¿Qué datos de contacto o rutas de atención aparecen en la base consolidada?",
    "¿Qué hitos o fechas relevantes de trayectoria se citan?",
    "¿Qué limitaciones tiene este asistente si una respuesta no está en el contexto?",
)

# Las 20 preguntas Módulo 1 están debajo de la tarjeta; no pueden escribir `qa_pregunta`
# después de instanciar el text_input. Se usa esta cola y se aplica al inicio de `pagina_qa`.
_QA_M1_PREFILL_KEY = "_qa_m1_prefill"

# Barra superior Q&A (mockup #004d2c)
C_QA_HEADER_BAR = "#004d2c"
C_QA_HEADER_BAR_TOP = "#0a4d30"

# Iconos cabecera e ilustraciones centrales: Material Symbols (Google).
_FEAT = {
    "icon_doc": (
        '<span class="material-symbols-outlined feat-head-material" aria-hidden="true">description</span>'
    ),
    "icon_faq": (
        '<span class="material-symbols-outlined feat-head-material" aria-hidden="true">help</span>'
    ),
    "icon_qa": (
        '<span class="material-symbols-outlined feat-head-material" aria-hidden="true">forum</span>'
    ),
    "illo_resumen": (
        '<span class="material-symbols-outlined feat-illo-material feat-illo-material--green" '
        'aria-hidden="true">description</span>'
    ),
    "illo_faq": (
        '<span class="material-symbols-outlined feat-illo-material feat-illo-material--faq" '
        'aria-hidden="true">help</span>'
    ),
    "illo_qa": (
        '<span class="material-symbols-outlined feat-illo-material feat-illo-material--burgundy" '
        'aria-hidden="true">forum</span>'
    ),
    "icon_agent": (
        '<span class="material-symbols-outlined feat-head-material" aria-hidden="true">smart_toy</span>'
    ),
    "illo_agent": (
        '<span class="material-symbols-outlined feat-illo-material feat-illo-material--agent" '
        'aria-hidden="true">smart_toy</span>'
    ),
}


def _collect_hero_images() -> list[str]:
    """Rutas del hero: primero `assets/hero_carousel/`, si está vacío `assets/*Banner-home*`."""
    ex = (".png", ".jpg", ".jpeg", ".webp")
    paths: list[str] = []
    if os.path.isdir(HERO_CAROUSEL_DIR):
        for name in sorted(os.listdir(HERO_CAROUSEL_DIR)):
            if name.lower().endswith(ex):
                paths.append(os.path.join(HERO_CAROUSEL_DIR, name))
    if paths:
        return paths

    assets_dir = os.path.join(_DIR, "assets")
    if os.path.isdir(assets_dir):
        for name in sorted(os.listdir(assets_dir)):
            low = name.lower()
            if low.endswith(ex) and "banner-home" in low.replace("_", "-"):
                paths.append(os.path.join(assets_dir, name))
    if paths:
        return paths

    if os.path.isfile(HERO_IMAGE):
        paths.append(HERO_IMAGE)
    return paths


def _image_file_to_data_uri(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    mime = "image/png"
    if ext in (".jpg", ".jpeg"):
        mime = "image/jpeg"
    elif ext == ".webp":
        mime = "image/webp"
    with open(path, "rb") as f:
        b64 = base64.standard_b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _render_hero_unificado(
    image_paths: list[str],
    *,
    show_cap: bool = True,
    cap: str | None = None,
    title_txt: str | None = None,
    sub: str | None = None,
    title_color: str | None = None,
    show_title_emoji: bool = True,
    show_text_overlay: bool = True,
    hero_layout: Literal["standard", "faq_banner", "qa_badge"] = "standard",
    badge_label: str | None = None,
) -> None:
    """Banner único: carrusel de imagen(es). Variantes según página (Inicio, FAQ, Q&A)."""
    if not image_paths:
        st.warning(
            "Añade imágenes en `assets/hero_carousel/` o en `assets/` con nombre tipo "
            "`01-Banner-home.jpg` … `07-Banner-home.jpg`, o el archivo `assets/hero_riopaila.png`."
        )
        return

    uris = [_image_file_to_data_uri(p) for p in image_paths]
    slides_json = json.dumps(uris)
    interval_ms = 5000
    cap_raw = cap if cap is not None else "Bienvenido al Asistente Virtual"
    title_raw = title_txt if title_txt is not None else "Riopaila Castillo"
    sub_raw = sub if sub is not None else (
        "Tu fuente de información sobre nuestra empresa, productos, "
        "servicios y sostenibilidad."
    )
    tc = title_color or C_GREEN
    cap_esc = html.escape(cap_raw)
    title_esc = html.escape(title_raw)
    sub_esc = html.escape(sub_raw)
    layout = hero_layout if hero_layout in ("standard", "faq_banner", "qa_badge") else "standard"
    root_mod = f" hero-unified--{layout}"

    if layout == "qa_badge":
        badge_raw = (badge_label or "Q&A — Preguntas y respuestas").strip()
        badge_esc = html.escape(badge_raw)
        hero_copy_block = f"""    <div class="hero-corner-badge" aria-label="{badge_esc}">{badge_esc}</div>"""
        scrim_class = "hero-scrim hero-scrim--qa-badge"
    elif layout == "faq_banner" and show_text_overlay:
        cap_html = f'<p class="hero-cap hero-cap--faq">{cap_esc}</p>' if show_cap else ""
        emoji = " 🌿" if show_title_emoji else ""
        hero_copy_block = f"""    <div class="hero-copy hero-copy--faq">
      {cap_html}
      <h1 class="hero-title hero-title--faq">{title_esc}{emoji}</h1>
      <p class="hero-sub hero-sub--faq">{sub_esc}</p>
    </div>"""
        scrim_class = "hero-scrim hero-scrim--faq-banner"
    elif show_text_overlay:
        cap_html = f'<p class="hero-cap">{cap_esc}</p>' if show_cap else ""
        emoji = " 🌿" if show_title_emoji else ""
        hero_copy_block = f"""    <div class="hero-copy">
      {cap_html}
      <h1 class="hero-title">{title_esc}{emoji}</h1>
      <p class="hero-sub">{sub_esc}</p>
    </div>"""
        scrim_class = "hero-scrim"
    else:
        badge_raw = (badge_label or "Q&A — Preguntas y respuestas").strip()
        badge_esc = html.escape(badge_raw)
        hero_copy_block = f"""    <div class="hero-corner-badge" aria-label="{badge_esc}">{badge_esc}</div>"""
        scrim_class = "hero-scrim hero-scrim--qa-badge"
        root_mod = " hero-unified--qa_badge"
    if len(uris) > 1:
        carousel_js = f"""
    let idx = 0;
    setInterval(function () {{
      img.style.opacity = "0";
      setTimeout(function () {{
        idx = (idx + 1) % slides.length;
        img.src = slides[idx];
        img.style.opacity = "1";
      }}, 500);
    }}, {interval_ms});
"""
    else:
        carousel_js = ""

    hero_html = f"""
<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap" rel="stylesheet" />
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: transparent; font-family: "Plus Jakarta Sans", "Segoe UI", system-ui, sans-serif; }}
  .hero-unified {{
    position: relative;
    width: 100%;
    min-height: 176px;
    max-height: 248px;
    aspect-ratio: 4 / 1;
    border-radius: 20px;
    overflow: hidden;
    box-shadow: none;
    border: 1px solid rgba(0, 0, 0, 0.06);
  }}
  .hero-bg {{
    position: absolute;
    inset: 0;
    z-index: 0;
  }}
  .hero-bg img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: 82% center;
    display: block;
    transition: opacity 0.5s ease;
    opacity: 1;
  }}
  .hero-scrim {{
    position: absolute;
    inset: 0;
    z-index: 1;
    pointer-events: none;
    background: linear-gradient(
      90deg,
      rgba(255,255,255,0.99) 0%,
      rgba(255,255,255,0.97) 16%,
      rgba(245,247,249,0.92) 32%,
      rgba(245,247,249,0.75) 48%,
      rgba(245,247,249,0.38) 64%,
      rgba(245,247,249,0.12) 78%,
      rgba(245,247,249,0.03) 90%,
      transparent 100%
    );
  }}
  .hero-copy {{
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 2;
    max-width: min(58%, 520px);
    padding: clamp(1.1rem, 3.2vw, 1.85rem) clamp(1.15rem, 3.2vw, 2.35rem);
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 0.35rem;
  }}
  .hero-cap {{
    font-size: clamp(0.95rem, 1.65vw, 1.12rem);
    font-weight: 700;
    letter-spacing: 0.03em;
    text-transform: none;
    color: {C_TEXT};
    margin: 0 0 0.15rem 0;
  }}
  .hero-title {{
    font-size: clamp(1.95rem, 3.8vw, 2.75rem);
    font-weight: 800;
    line-height: 1.1;
    color: {tc};
    margin: 0;
    letter-spacing: -0.02em;
    text-shadow: 0 2px 0 rgba(255,255,255,1), 0 0 28px rgba(255,255,255,0.95);
  }}
  .hero-sub {{
    font-size: clamp(1.02rem, 1.55vw, 1.18rem);
    line-height: 1.45;
    font-weight: 500;
    color: {C_TEXT};
    margin: 0.4rem 0 0 0;
    max-width: 38rem;
    text-shadow: 0 1px 0 rgba(255,255,255,0.95), 0 0 12px rgba(255,255,255,0.7);
  }}
  .hero-scrim--photo-only {{
    background: linear-gradient(180deg, rgba(0, 0, 0, 0.14) 0%, transparent 42%) !important;
  }}
  /* FAQ: franja blanca a la izquierda + gradiente suave hacia la foto (mockup tipo banner institucional) */
  .hero-scrim--faq-banner {{
    background: linear-gradient(
      90deg,
      #ffffff 0%,
      #ffffff 34%,
      rgba(255, 255, 255, 0.94) 46%,
      rgba(255, 255, 255, 0.62) 58%,
      rgba(255, 255, 255, 0.22) 72%,
      rgba(255, 255, 255, 0.05) 84%,
      transparent 100%
    ) !important;
  }}
  .hero-copy--faq {{
    max-width: min(56%, 520px);
    padding: clamp(1rem, 3vw, 1.65rem) clamp(1.1rem, 3vw, 2rem);
    justify-content: center;
  }}
  .hero-title--faq {{
    color: {tc} !important;
    font-size: clamp(1.65rem, 3.2vw, 2.35rem) !important;
    text-shadow: none !important;
    font-weight: 800 !important;
  }}
  .hero-sub--faq {{
    color: #455a64 !important;
    text-shadow: none !important;
    font-size: clamp(0.98rem, 1.45vw, 1.08rem) !important;
    font-weight: 500 !important;
    margin-top: 0.35rem !important;
  }}
  .hero-cap--faq {{
    color: #546e7a !important;
    text-shadow: none !important;
  }}
  /* Q&A: foto a pantalla + etiqueta blanca abajo a la izquierda */
  .hero-scrim--qa-badge {{
    background:
      linear-gradient(180deg, rgba(0, 0, 0, 0.1) 0%, transparent 40%),
      linear-gradient(0deg, rgba(0, 0, 0, 0.22) 0%, transparent 52%) !important;
  }}
  .hero-unified--qa_badge .hero-bg img {{
    object-position: center center;
  }}
  .hero-corner-badge {{
    position: absolute;
    left: clamp(14px, 2.4vw, 22px);
    bottom: clamp(14px, 2.4vw, 20px);
    z-index: 3;
    background: #ffffff;
    padding: 10px 18px;
    border-radius: 12px;
    font-size: clamp(0.78rem, 1.25vw, 0.9rem);
    font-weight: 700;
    letter-spacing: 0.02em;
    color: {C_GREEN};
    box-shadow: none;
    line-height: 1.35;
    max-width: calc(100% - 28px);
  }}
</style></head>
<body>
  <div class="hero-unified{root_mod}">
    <div class="hero-bg">
      <img id="heroSlide" alt="Riopaila Castillo" />
    </div>
    <div class="{scrim_class}" aria-hidden="true"></div>
{hero_copy_block}
  </div>
  <script>
    const slides = {slides_json};
    const img = document.getElementById("heroSlide");
    img.src = slides[0];
    {carousel_js}
  </script>
</body></html>
"""
    components.html(hero_html, height=270, scrolling=False)


def _render_qa_header_bar() -> None:
    """Barra superior verde del mockup: icono + títulos a la izquierda, marca a la derecha."""
    logo_uri = _image_file_to_data_uri(LOGO_IMAGE) if os.path.isfile(LOGO_IMAGE) else ""
    brand = (
        f'<div class="qa-header-brand"><img src="{html.escape(logo_uri, quote=True)}" alt="Riopaila Castillo" /></div>'
        if logo_uri
        else (
            '<div class="qa-header-brand qa-header-brand--text">'
            '<span class="qa-header-wordmark">RIOPAILA CASTILLO</span>'
            '<span class="qa-header-tag">Compromiso desde 1918</span>'
            "</div>"
        )
    )
    st.markdown(
        f"""
        <div class="qa-top-bar" role="banner">
          <div class="qa-top-bar-inner">
            <div class="qa-header-left">
              <span class="qa-header-leaf material-symbols-outlined" aria-hidden="true">eco</span>
              <div class="qa-header-titles">
                <p class="qa-header-title">Asistente Virtual de Riopaila Castillo</p>
                <p class="qa-header-sub">Tu fuente de información sobre nuestra empresa</p>
              </div>
            </div>
            {brand}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def inyectar_estilos_globales() -> None:
    """Forzar UI clara, colores del mockup y menú lateral estilizado."""
    st.markdown(
        f"""
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />
        <style>
            :root {{
                --rc-font: "Plus Jakarta Sans", "Segoe UI", system-ui, -apple-system, sans-serif;
                --rc-radius-sm: 10px;
                --rc-radius-md: 14px;
                --rc-radius-lg: 20px;
                --rc-line: rgba(0, 0, 0, 0.06);
                --rc-line-green: rgba(27, 94, 32, 0.12);
                --rc-shadow-soft: 0 4px 24px rgba(27, 94, 32, 0.05), 0 1px 2px rgba(0, 0, 0, 0.04);
                --rc-shadow-lift: 0 14px 44px rgba(27, 94, 32, 0.09), 0 4px 14px rgba(0, 0, 0, 0.05);
            }}
            html, body, .stApp {{
                font-family: var(--rc-font) !important;
                background: linear-gradient(168deg, #f9fbfc 0%, {C_BG} 42%, #eef2f5 100%) fixed !important;
                color: {C_TEXT} !important;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
                text-rendering: optimizeLegibility;
            }}
            /* No usar .stApp * {{ font-family: inherit }}: rompe iconos :material/ de Streamlit
               (el span del icono hereda Plus Jakarta y muestra “send”, “keyboard_double…”). */
            .material-symbols-outlined,
            .feat-head-material,
            .feat-illo-material {{
                font-family: "Material Symbols Outlined" !important;
            }}
            [data-testid="stAppViewContainer"], [data-testid="stHeader"],
            [data-testid="stMainBlockContainer"] {{
                background: transparent !important;
            }}
            [data-testid="stMainBlockContainer"] {{
                padding-top: clamp(1.75rem, 4vw, 2.5rem);
                padding-bottom: clamp(2rem, 5vw, 3rem);
                padding-left: clamp(0.75rem, 2vw, 1.25rem);
                padding-right: clamp(0.75rem, 2vw, 1.25rem);
                max-width: 1180px;
            }}

            /* Carrusel hero (components.html → iframe): sin sombra en el marco del host */
            iframe.stIFrame,
            [data-testid="stIFrame"] {{
                box-shadow: none !important;
            }}

            /* Separadores y ritmo en contenido principal */
            [data-testid="stMain"] hr {{
                margin: 2rem 0 1.35rem 0 !important;
                border: none !important;
                height: 1px !important;
                background: linear-gradient(
                    90deg,
                    transparent 0%,
                    var(--rc-line) 15%,
                    var(--rc-line) 85%,
                    transparent 100%
                ) !important;
            }}

            /* Sidebar gris claro (mockup menú) */
            [data-testid="stSidebar"] {{
                background: linear-gradient(180deg, #fafcfd 0%, #f4f6f8 100%) !important;
                border-right: 1px solid rgba(0, 0, 0, 0.06) !important;
                box-shadow: 4px 0 24px rgba(0, 0, 0, 0.03);
            }}
            [data-testid="stSidebar"] > div:first-child {{
                padding-top: 1rem !important;
            }}
            [data-testid="stSidebar"] p,
            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] .stMarkdown p {{
                color: {C_TEXT} !important;
            }}

            /* Menú lateral RC: filas con botón — alineación izquierda + hover con contraste */
            [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.stButton) {{
                text-align: left !important;
            }}
            [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.stButton) .stButton {{
                width: 100% !important;
                display: block !important;
            }}
            [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.stButton) .stButton > div {{
                width: 100% !important;
                display: flex !important;
                justify-content: flex-start !important;
                align-items: stretch !important;
            }}
            [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.stButton) .stButton button {{
                justify-content: flex-start !important;
                align-items: center !important;
                text-align: left !important;
                font-weight: 600 !important;
                font-size: 0.875rem !important;
                letter-spacing: 0.01em !important;
                line-height: 1.28 !important;
                width: 100% !important;
                max-width: 100% !important;
                border-radius: var(--rc-radius-md) !important;
                padding: 11px 15px !important;
                margin: 0 !important;
                min-height: 44px !important;
                background: transparent !important;
                border: 1px solid transparent !important;
                color: #263238 !important;
                box-shadow: none !important;
                transition: background 0.18s ease, color 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease !important;
            }}
            /* Contenido interno del botón (icono Material + texto) */
            [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.stButton) .stButton button > div {{
                display: flex !important;
                flex-direction: row !important;
                justify-content: flex-start !important;
                align-items: center !important;
                gap: 12px !important;
                width: 100% !important;
                text-align: left !important;
                margin: 0 !important;
            }}
            [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.stButton) .stButton button > div > * {{
                margin: 0 !important;
                text-align: left !important;
            }}
            [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.stButton) .stButton button [data-testid="stMarkdownContainer"],
            [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.stButton) .stButton button [data-testid="stMarkdownContainer"] p {{
                text-align: left !important;
                justify-content: flex-start !important;
            }}
            [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.stButton) .stButton button:hover {{
                background: rgba(27, 94, 32, 0.12) !important;
                border-color: rgba(27, 94, 32, 0.08) !important;
                color: #145523 !important;
                box-shadow: none !important;
            }}
            [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.stButton) .stButton button:hover *,
            [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.stButton) .stButton button:hover span {{
                color: #145523 !important;
            }}
            [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.stButton) .stButton button:focus-visible {{
                background: rgba(27, 94, 32, 0.12) !important;
                border-color: rgba(27, 94, 32, 0.18) !important;
                color: #145523 !important;
                outline: none !important;
                box-shadow: 0 0 0 2px rgba(27, 94, 32, 0.22) !important;
            }}
            [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.stButton) .stButton button:focus-visible *,
            [data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.stButton) .stButton button:focus-visible span {{
                color: #145523 !important;
            }}
            [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
                margin: 0;
            }}
            [data-testid="stMain"] h1, [data-testid="stMain"] h2, [data-testid="stMain"] h3 {{
                color: {C_GREEN} !important;
                letter-spacing: -0.02em;
            }}
            [data-testid="stMain"] h1, [data-testid="stMain"] h2 {{
                font-weight: 800 !important;
            }}
            [data-testid="stMain"] h3 {{
                font-weight: 700 !important;
            }}
            [data-testid="stMain"] p, [data-testid="stMain"] span, [data-testid="stMain"] label, [data-testid="stMain"] .stMarkdown {{
                color: {C_TEXT} !important;
            }}
            .stCaption, [data-testid="stCaptionContainer"] {{
                color: {C_TEXT_MUTED} !important;
            }}

            /* Widgets claros */
            .stTextInput input, .stTextArea textarea {{
                background-color: {C_WHITE} !important;
                color: {C_TEXT} !important;
                border-radius: var(--rc-radius-md) !important;
            }}

            .card {{
                background: {C_WHITE};
                border-radius: var(--rc-radius-md);
                box-shadow: var(--rc-shadow-soft);
                margin-bottom: 0;
                overflow: hidden;
                border: 1px solid var(--rc-line);
            }}
            .card-body-pad {{
                padding: 18px 20px 20px;
            }}
            .feat-head {{
                margin: 0;
                padding: 0;
            }}
            .feat-head-inner {{
                display: flex;
                align-items: center;
                gap: 16px;
                padding: 16px 18px;
            }}
            .feat-head-inner .feat-head-material {{
                font-family: "Material Symbols Outlined";
                font-weight: normal;
                font-style: normal;
                font-size: 40px;
                line-height: 1;
                width: 44px;
                height: 44px;
                min-width: 44px;
                flex-shrink: 0;
                display: flex;
                align-items: center;
                justify-content: center;
                font-variation-settings: "FILL" 0, "wght" 400, "GRAD" 0, "opsz" 40;
                -webkit-font-smoothing: antialiased;
            }}
            .feat-head-green .feat-head-material {{
                color: {C_GREEN} !important;
            }}
            .feat-head-blue .feat-head-material {{
                color: {C_FAQ_PRIMARY_MID} !important;
            }}
            .feat-head-yellow .feat-head-material {{
                color: {C_BURGUNDY} !important;
            }}
            /* Cabecera tarjetas funcionalidades: misma altura en las 3 (FAQ no queda más baja) */
            .feat-card-triple .feat-head-inner {{
                min-height: 104px;
                box-sizing: border-box;
                align-items: center;
            }}
            .feat-card-triple .feat-head-inner > div:last-child {{
                min-height: 3.65rem;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }}
            .feat-card-triple .feat-head-sub {{
                min-height: 2.45rem;
            }}
            .feat-head-title {{
                margin: 0;
                font-size: 1.05rem;
                font-weight: 700;
                letter-spacing: -0.015em;
            }}
            .feat-head-sub {{
                margin: 6px 0 0 0;
                font-size: 0.8125rem;
                font-weight: 500;
                line-height: 1.4;
            }}
            .feat-head-green {{ background: {C_GREEN_SOFT}; }}
            .feat-head-green .feat-head-title {{ color: {C_GREEN}; }}
            .feat-head-green .feat-head-sub {{ color: #2e7d32; }}
            .feat-head-blue {{ background: {C_FAQ_SOFT}; }}
            .feat-head-blue .feat-head-title {{ color: {C_FAQ_PRIMARY}; }}
            .feat-head-blue .feat-head-sub {{ color: #546e7a; }}
            .feat-head-yellow {{ background: {C_YELLOW_SOFT}; }}
            .feat-head-yellow .feat-head-title {{ color: {C_BURGUNDY}; }}
            .feat-head-yellow .feat-head-sub {{ color: {C_BURGUNDY_SUB}; }}
            .feat-head-agent {{
                background: linear-gradient(135deg, {C_GREEN_SOFT} 0%, {C_ORANGE_SOFT} 100%);
            }}
            .feat-head-agent .feat-head-title {{ color: {C_GREEN}; }}
            .feat-head-agent .feat-head-sub {{ color: {C_ORANGE_SUB}; }}
            .feat-head-agent .feat-head-material {{ color: {C_GREEN}; }}

            .feat-body-white {{
                background: {C_WHITE};
                padding: 22px 18px 24px;
                text-align: center;
            }}
            .feat-illo {{
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100px;
                margin-bottom: 14px;
            }}
            .feat-illo-material {{
                font-family: "Material Symbols Outlined";
                font-weight: normal;
                font-style: normal;
                font-size: 80px;
                line-height: 1;
                font-variation-settings: "FILL" 0, "wght" 300, "GRAD" 0, "opsz" 80;
                -webkit-font-smoothing: antialiased;
                user-select: none;
            }}
            /* Mayor especificidad que [data-testid="stMain"] span (color: C_TEXT) */
            [data-testid="stMain"] .feat-illo-material.feat-illo-material--green {{
                color: {C_GREEN} !important;
            }}
            [data-testid="stMain"] .feat-illo-material.feat-illo-material--orange {{
                color: {C_ORANGE} !important;
            }}
            [data-testid="stMain"] .feat-illo-material.feat-illo-material--faq {{
                color: {C_FAQ_PRIMARY_MID} !important;
            }}
            [data-testid="stMain"] .feat-illo-material.feat-illo-material--burgundy {{
                color: {C_BURGUNDY} !important;
            }}
            [data-testid="stMain"] .feat-illo-material.feat-illo-material--agent {{
                color: {C_ORANGE} !important;
            }}
            .feat-desc {{
                margin: 0;
                font-size: 0.9rem;
                line-height: 1.55;
                color: #455a64;
                text-align: center;
                letter-spacing: 0.01em;
            }}

            /* Contenedor blanco: título + 3 tarjetas (misma altura, botones alineados) */
            .feat-shell {{
                background: linear-gradient(180deg, #ffffff 0%, #fafbfc 100%);
                border-radius: var(--rc-radius-lg);
                box-shadow: var(--rc-shadow-soft), 0 0 0 1px var(--rc-line-green);
                border: 1px solid var(--rc-line-green);
                padding: 28px 26px 32px;
                margin-bottom: 1.75rem;
            }}
            .feat-shell-title {{
                color: {C_GREEN};
                font-size: 1.35rem;
                font-weight: 800;
                margin: 0 0 24px 0;
                letter-spacing: -0.035em;
                line-height: 1.2;
                display: flex;
                align-items: center;
                gap: 14px;
                flex-wrap: wrap;
            }}
            .feat-shell-title::before {{
                content: "";
                width: 4px;
                height: 1.25em;
                border-radius: 3px;
                background: linear-gradient(180deg, {C_GREEN}, #2e7d32);
                flex-shrink: 0;
            }}
            .feat-grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 18px;
                align-items: stretch;
            }}
            @media (max-width: 1200px) {{
                .feat-grid {{ grid-template-columns: repeat(2, 1fr); }}
            }}
            @media (max-width: 700px) {{
                .feat-grid {{ grid-template-columns: 1fr; }}
            }}
            .feat-col {{
                display: flex;
                min-width: 0;
            }}
            .feat-card-triple {{
                flex: 1;
                display: flex;
                flex-direction: column;
                margin-bottom: 0 !important;
                height: 100%;
                min-height: 100%;
                box-shadow: 0 2px 12px rgba(0,0,0,0.06) !important;
                transition: box-shadow 0.22s ease, border-color 0.22s ease, transform 0.2s ease;
            }}
            .feat-card-triple:hover {{
                box-shadow: var(--rc-shadow-lift) !important;
                border-color: var(--rc-line-green) !important;
                transform: translateY(-2px);
            }}
            .feat-card-triple .feat-body-grow .feat-desc {{
                flex: 1 0 auto;
            }}
            .feat-illo-fixed {{
                display: flex;
                justify-content: center;
                align-items: center;
                height: 118px;
                min-height: 118px;
                max-height: 118px;
                margin-bottom: 12px;
            }}
            .feat-card-footer {{
                padding: 6px 16px 18px;
                margin-top: auto;
            }}
            .feat-btn {{
                display: block;
                width: 100%;
                box-sizing: border-box;
                text-align: center;
                padding: 12px 16px;
                border-radius: var(--rc-radius-md);
                font-weight: 600;
                font-size: 0.875rem;
                letter-spacing: 0.02em;
                text-decoration: none !important;
                border: none;
                cursor: pointer;
                transition: background-color 0.2s ease, filter 0.2s ease, transform 0.15s ease;
            }}
            .feat-btn--green {{
                background: {C_GREEN};
                color: #ffffff;
            }}
            .feat-btn--green:hover {{
                background: #145214;
                filter: brightness(1.06);
            }}
            .feat-btn--blue {{
                background: {C_FAQ_PRIMARY};
                color: #ffffff;
            }}
            .feat-btn--blue:hover {{
                background: {C_FAQ_BTN_HOVER};
                filter: brightness(1.06);
            }}
            .feat-btn--yellow {{
                background: {C_YELLOW};
                color: #ffffff;
            }}
            .feat-btn--yellow:hover {{
                background: {C_BURGUNDY_HOVER};
                filter: brightness(1.06);
                color: #ffffff;
            }}
            .feat-btn--agent {{
                background: linear-gradient(135deg, {C_GREEN} 0%, {C_ORANGE} 100%);
                color: #ffffff;
            }}
            .feat-btn--agent:hover {{
                background: linear-gradient(135deg, #145214 0%, {C_ORANGE_HOVER} 100%);
                filter: brightness(1.05);
                color: #ffffff;
            }}
            /* Texto de los enlaces-boton (Streamlit envuelve con span y .main span usa !important) */
            a.feat-btn.feat-btn--green,
            a.feat-btn.feat-btn--green:visited,
            a.feat-btn.feat-btn--green:hover,
            a.feat-btn.feat-btn--green *,
            a.feat-btn.feat-btn--green:visited *,
            a.feat-btn.feat-btn--green:hover * {{
                color: #ffffff !important;
            }}
            a.feat-btn.feat-btn--blue,
            a.feat-btn.feat-btn--blue:visited,
            a.feat-btn.feat-btn--blue:hover,
            a.feat-btn.feat-btn--blue *,
            a.feat-btn.feat-btn--blue:visited *,
            a.feat-btn.feat-btn--blue:hover * {{
                color: #ffffff !important;
            }}
            a.feat-btn.feat-btn--yellow,
            a.feat-btn.feat-btn--yellow:visited,
            a.feat-btn.feat-btn--yellow:hover,
            a.feat-btn.feat-btn--yellow *,
            a.feat-btn.feat-btn--yellow:visited *,
            a.feat-btn.feat-btn--yellow:hover * {{
                color: #ffffff !important;
            }}
            a.feat-btn.feat-btn--agent,
            a.feat-btn.feat-btn--agent:visited,
            a.feat-btn.feat-btn--agent:hover,
            a.feat-btn.feat-btn--agent *,
            a.feat-btn.feat-btn--agent:visited *,
            a.feat-btn.feat-btn--agent:hover * {{
                color: #ffffff !important;
            }}
            .card-body {{
                margin: 0;
                font-size: 0.95rem;
                line-height: 1.55;
                color: {C_TEXT};
            }}
            .card-answer {{
                border: 1px solid var(--rc-line);
                border-radius: var(--rc-radius-md);
                background: linear-gradient(180deg, #ffffff 0%, #fafafa 100%);
                box-shadow: var(--rc-shadow-soft);
            }}
            .answer-card-header {{
                display: flex;
                align-items: flex-start;
                gap: 12px;
                margin-bottom: 14px;
            }}
            .answer-card-logo {{
                width: 48px;
                height: 48px;
                min-width: 48px;
                object-fit: contain;
                flex-shrink: 0;
                display: block;
            }}
            .answer-card-header .answer-q {{
                margin: 0;
                flex: 1;
                padding-top: 2px;
            }}
            .answer-q {{
                margin: 0 0 10px 0;
                font-weight: 700;
                color: {C_TEXT};
                font-size: 1rem;
            }}
            .answer-card-meta {{
                margin-top: 14px;
                padding-top: 12px;
                border-top: 1px solid #e8e8e8;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 0.82rem;
                color: {C_TEXT_MUTED};
            }}
            .answer-card-meta-copy {{
                color: #1565c0;
                font-weight: 500;
            }}

            /* Compositor Q&A: un solo recuadro blanco (fila input); cabecera es texto plano */
            .qa-composer-surface-anchor {{
                display: none !important;
                height: 0 !important;
                width: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
                overflow: hidden !important;
            }}
            /* Espacio entre cabecera (texto) y la tarjeta del input */
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) > div[data-testid="stVerticalBlock"] {{
                gap: 12px !important;
            }}
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stMarkdown"]:has(.qa-composer-head) {{
                margin-bottom: 0 !important;
            }}
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) {{
                background: linear-gradient(180deg, #ffffff 0%, #fdfcfd 100%) !important;
                border: 1px solid rgba(139, 35, 50, 0.1) !important;
                border-radius: 18px !important;
                box-shadow:
                    0 1px 0 rgba(255, 255, 255, 0.9) inset,
                    0 10px 36px rgba(139, 35, 50, 0.08),
                    0 2px 8px rgba(0, 0, 0, 0.04) !important;
                padding: 18px 20px 20px !important;
            }}
            /* Solo un recuadro blanco: la fila input+Enviar (la cabecera es texto sin caja) */
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) {{
                align-items: center !important;
                align-content: center !important;
                gap: 10px !important;
                background: {C_WHITE} !important;
                border: 1px solid rgba(139, 35, 50, 0.14) !important;
                border-radius: 14px !important;
                box-shadow:
                    0 1px 0 rgba(255, 255, 255, 0.95) inset,
                    0 8px 28px rgba(139, 35, 50, 0.1) !important;
                padding: 12px 12px 12px 16px !important;
                margin-top: 20px !important;
                margin-bottom: 0 !important;
            }}
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) > div[data-testid="stColumn"]:first-child [data-testid="stVerticalBlock"],
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) [data-testid="stElementContainer"],
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) [data-testid="stTextInput"],
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) [data-testid="stTextInput"] > div {{
                background: transparent !important;
                background-color: transparent !important;
                border: none !important;
                box-shadow: none !important;
            }}
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) [data-testid="stTextInput"] input {{
                border: none !important;
                outline: none !important;
                box-shadow: none !important;
                background: transparent !important;
                background-color: transparent !important;
                border-radius: 0 !important;
                min-height: 40px !important;
            }}
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) div[data-baseweb="input"] {{
                background: transparent !important;
                background-color: transparent !important;
                border: none !important;
                border-radius: 0 !important;
                box-shadow: none !important;
            }}
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) .stTextInput {{
                background: transparent !important;
                background-color: transparent !important;
                border: none !important;
                box-shadow: none !important;
            }}
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) > div[data-testid="stColumn"],
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] {{
                background: transparent !important;
                background-color: transparent !important;
                border: none !important;
                box-shadow: none !important;
            }}
            /* Base Web / Streamlit: quitar “segunda caja” bajo el input (fieldset, raíz del widget) */
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) [data-testid="stTextInput"] fieldset,
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) .stTextInput fieldset {{
                border: none !important;
                margin: 0 !important;
                padding: 0 !important;
                background: transparent !important;
                background-color: transparent !important;
                box-shadow: none !important;
            }}
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) [data-testid="stTextInput"] > div > div {{
                background: transparent !important;
                background-color: transparent !important;
                border: none !important;
                box-shadow: none !important;
            }}
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) [data-testid="stTextInput"] {{
                margin: 0 !important;
                margin-bottom: 0 !important;
            }}
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) > div[data-testid="stColumn"] {{
                display: flex !important;
                flex-direction: column !important;
                justify-content: center !important;
            }}
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) .stButton {{
                margin-top: 0 !important;
                margin-bottom: 0 !important;
            }}
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) .stButton > button {{
                min-height: unset !important;
                height: 44px !important;
                max-height: 44px !important;
                min-width: 7.5rem !important;
                border-radius: var(--rc-radius-md) !important;
                margin: 0 !important;
                padding: 0 18px !important;
                display: inline-flex !important;
                flex-direction: row !important;
                flex-wrap: nowrap !important;
                align-items: center !important;
                align-self: center !important;
                justify-content: center !important;
                gap: 0.45rem !important;
                color: {C_WHITE} !important;
                font-weight: 600 !important;
                white-space: nowrap !important;
                box-sizing: border-box !important;
                line-height: 1.15 !important;
                box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.22) !important;
            }}
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) .stButton > button p {{
                color: {C_WHITE} !important;
                margin: 0 !important;
                line-height: 1.15 !important;
                display: inline-flex !important;
                align-items: center !important;
                font-size: 0.93rem !important;
                letter-spacing: 0.02em !important;
            }}
            /* Icono send (avión): trazo blanco contorno, alineado con “Enviar” */
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) .stButton > button span {{
                color: #ffffff !important;
                margin: 0 !important;
                line-height: 1 !important;
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                font-family: "Material Symbols Rounded" !important;
                font-size: 1.18rem !important;
                font-weight: normal !important;
                font-variation-settings: "FILL" 0, "wght" 400, "GRAD" 0, "opsz" 28 !important;
                -webkit-font-smoothing: antialiased;
            }}
            .qa-composer-heading {{
                color: {C_GREEN} !important;
                font-size: 1.12rem !important;
                font-weight: 700 !important;
                margin: 0 0 14px 0 !important;
                letter-spacing: -0.02em !important;
                line-height: 1.3 !important;
            }}
            /* Cabecera Q&A: sin recuadro (el único bloque con borde es la fila del input) */
            .qa-composer-head {{
                margin: 0;
                padding: 0;
                background: none !important;
                border: none !important;
                box-shadow: none !important;
            }}
            .qa-composer-title {{
                margin: 0 0 6px 0 !important;
                padding: 0 !important;
                font-size: 1.22rem !important;
                font-weight: 800 !important;
                letter-spacing: -0.03em !important;
                line-height: 1.22 !important;
                color: {C_GREEN} !important;
            }}
            .qa-composer-sub {{
                margin: 0 !important;
                padding: 0 !important;
                font-size: 0.88rem !important;
                line-height: 1.48 !important;
                color: #455a64 !important;
                font-weight: 500;
            }}
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) h3,
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) .qa-composer-heading,
            [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) .qa-composer-title {{
                color: {C_GREEN} !important;
            }}
            [data-testid="stMainBlockContainer"] .qa-composer-foot,
            [data-testid="stMainBlockContainer"] .qa-composer-foot p {{
                color: {C_TEXT_MUTED} !important;
                font-size: 0.82rem !important;
                margin: 14px 0 0 0 !important;
                line-height: 1.5 !important;
                padding: 14px 0 0 0 !important;
                background: transparent !important;
                background-color: transparent !important;
                border: none !important;
                border-radius: 0 !important;
                border-left: none !important;
                box-shadow: none !important;
                border-top: 1px solid var(--rc-line) !important;
            }}
            .qa-bloque-inicio-spacer {{
                height: 2rem;
                margin: 0;
                padding: 0;
            }}

            /* ----- Pestaña Q&A: conversación + temas sugeridos (mockup verde) ----- */
            #qa-page-mount {{
                display: none !important;
            }}
            html:has(#qa-page-mount),
            html:has(#qa-page-mount) body,
            html:has(#qa-page-mount) .stApp {{
                background: #eef2f0 !important;
            }}
            /* Q&A: la columna del compositor no es tarjeta (la tarjeta es st.container aparte) */
            html:has(#qa-page-mount) [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) {{
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
                padding: 0 !important;
            }}
            html:has(#qa-page-mount) [data-testid="stMainBlockContainer"] div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) > div[data-testid="stVerticalBlock"] {{
                gap: 18px !important;
            }}
            /* Tarjeta única (columna derecha): barra verde + chat gris + temas + input */
            .qa-unified-card-root,
            .qa-chat-gray-root {{
                display: none !important;
            }}
            html:has(#qa-page-mount) div:has(> [data-testid="stVerticalBlock"]:has(.qa-unified-card-root)) {{
                border: none !important;
                box-shadow: none !important;
                background: transparent !important;
                padding: 0 !important;
            }}
            html:has(#qa-page-mount) div:has(> [data-testid="stVerticalBlock"]:has(.qa-chat-gray-root)) {{
                border: none !important;
                box-shadow: none !important;
                background: transparent !important;
                padding: 0 !important;
            }}
            html:has(#qa-page-mount) div[class*="st-key-qa_unified_card"] [data-testid="stVerticalBlock"]:has(.qa-unified-card-root),
            html:has(#qa-page-mount) div[data-testid="stVerticalBlock"][class*="st-key-qa_unified_card"]:has(.qa-unified-card-root) {{
                background: #ffffff !important;
                border: 1px solid rgba(0, 0, 0, 0.08) !important;
                border-radius: 16px !important;
                box-shadow:
                    0 14px 44px rgba(0, 50, 30, 0.08),
                    0 2px 10px rgba(0, 0, 0, 0.04) !important;
                padding: 0 !important;
                margin: 0 !important;
                overflow: hidden !important;
                width: 100% !important;
                box-sizing: border-box !important;
                gap: 0 !important;
                display: flex !important;
                flex-direction: column !important;
                align-items: stretch !important;
                min-height: 0 !important;
            }}
            html:has(#qa-page-mount) div[class*="st-key-qa_unified_card"] [data-testid="stVerticalBlock"]:has(.qa-unified-card-root) > div[data-testid="stElementContainer"]:has(.qa-top-bar),
            html:has(#qa-page-mount) div[data-testid="stVerticalBlock"][class*="st-key-qa_unified_card"]:has(.qa-unified-card-root) > div[data-testid="stElementContainer"]:has(.qa-top-bar) {{
                flex-shrink: 0 !important;
            }}
            html:has(#qa-page-mount) div[class*="st-key-qa_unified_card"] [data-testid="stVerticalBlock"]:has(.qa-unified-card-root) > div[data-testid="stVerticalBlock"][class*="st-key-qa_chat_inset"],
            html:has(#qa-page-mount) div[data-testid="stVerticalBlock"][class*="st-key-qa_unified_card"]:has(.qa-unified-card-root) > div[data-testid="stVerticalBlock"][class*="st-key-qa_chat_inset"] {{
                flex: 1 1 auto !important;
                min-height: 0 !important;
                max-height: none !important;
            }}
            html:has(#qa-page-mount) div[class*="st-key-qa_unified_card"],
            html:has(#qa-page-mount) div.st-key-qa_unified_card {{
                border: none !important;
                box-shadow: none !important;
                background: transparent !important;
                padding: 0 !important;
                margin-bottom: 1.25rem !important;
            }}
            /* Zona gris: altura mínima según viewport + techo para que el historial no alargue la tarjeta (scroll en .qa-chat-scroll-viewport) */
            html:has(#qa-page-mount) [data-testid="stVerticalBlock"][class*="st-key-qa_chat_inset"] {{
                border: none !important;
                box-shadow: none !important;
                background: #eef2f0 !important;
                padding: clamp(14px, 2vw, 20px) clamp(14px, 2vw, 22px) 52px !important;
                margin: 0 !important;
                border-radius: 0 0 14px 14px !important;
                gap: 16px !important;
                box-sizing: border-box !important;
                overflow-x: hidden !important;
                overflow-y: hidden !important;
                display: flex !important;
                flex-direction: column !important;
                min-height: max(min(58vh, 560px), calc(100svh - 500px)) !important;
                max-height: min(calc(100svh - 200px), 1080px) !important;
            }}
            html:has(#qa-page-mount) div[class*="st-key-qa_unified_card"] [data-testid="stVerticalBlock"][class*="st-key-qa_chat_inset"] > div[data-testid="stLayoutWrapper"]:first-of-type,
            html:has(#qa-page-mount) div[data-testid="stVerticalBlock"][class*="st-key-qa_unified_card"]:has(.qa-unified-card-root) > div[data-testid="stVerticalBlock"][class*="st-key-qa_chat_inset"] > div[data-testid="stLayoutWrapper"]:first-of-type {{
                flex: 1 1 auto !important;
                min-height: 0 !important;
                display: flex !important;
                flex-direction: column !important;
            }}
            html:has(#qa-page-mount) div[class*="st-key-qa_unified_card"] [data-testid="stVerticalBlock"][class*="st-key-qa_chat_inset"] > div[data-testid="stLayoutWrapper"]:first-of-type [data-testid="stHorizontalBlock"],
            html:has(#qa-page-mount) div[data-testid="stVerticalBlock"][class*="st-key-qa_unified_card"]:has(.qa-unified-card-root) > div[data-testid="stVerticalBlock"][class*="st-key-qa_chat_inset"] > div[data-testid="stLayoutWrapper"]:first-of-type [data-testid="stHorizontalBlock"] {{
                align-items: stretch !important;
                flex: 1 1 auto !important;
                min-height: 0 !important;
                max-height: 100% !important;
                display: flex !important;
                flex-direction: row !important;
                overflow-x: hidden !important;
                overflow-y: hidden !important;
            }}
            html:has(#qa-page-mount) div[class*="st-key-qa_unified_card"] [data-testid="stVerticalBlock"][class*="st-key-qa_chat_inset"] > div[data-testid="stLayoutWrapper"]:first-of-type [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
            html:has(#qa-page-mount) div[data-testid="stVerticalBlock"][class*="st-key-qa_unified_card"]:has(.qa-unified-card-root) > div[data-testid="stVerticalBlock"][class*="st-key-qa_chat_inset"] > div[data-testid="stLayoutWrapper"]:first-of-type [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {{
                min-height: 0 !important;
                align-self: stretch !important;
            }}
            /* Solo columna izquierda (ejemplos + Módulo 1): no puede crecer fuera de la tarjeta */
            html:has(#qa-page-mount) div[class*="st-key-qa_unified_card"] [data-testid="stVerticalBlock"][class*="st-key-qa_chat_inset"] > div[data-testid="stLayoutWrapper"]:first-of-type [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:has(.qa-ejemplos-stack),
            html:has(#qa-page-mount) div[data-testid="stVerticalBlock"][class*="st-key-qa_unified_card"]:has(.qa-unified-card-root) > div[data-testid="stVerticalBlock"][class*="st-key-qa_chat_inset"] > div[data-testid="stLayoutWrapper"]:first-of-type [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:has(.qa-ejemplos-stack) {{
                max-height: 100% !important;
                overflow: hidden !important;
                display: flex !important;
                flex-direction: column !important;
            }}
            html:has(#qa-page-mount) div[class*="st-key-qa_unified_card"] [data-testid="stVerticalBlock"]:has(.qa-chat-gray-root) {{
                /* misma celda que .st-key-qa_chat_inset; regla de respaldo */
                background: #eef2f0 !important;
                border-radius: 0 0 14px 14px !important;
                box-sizing: border-box !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[class*="st-key-qa_unified_card"] [data-testid="stVerticalBlock"]:has(.qa-unified-card-root) .qa-top-bar {{
                border-radius: 16px 16px 0 0 !important;
                margin: 0 !important;
                box-shadow: none !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[class*="st-key-qa_unified_card"] [data-testid="stVerticalBlock"]:has(.qa-unified-card-root) .qa-top-bar-inner {{
                max-width: none !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-top-bar {{
                background: linear-gradient(180deg, {C_QA_HEADER_BAR_TOP} 0%, {C_QA_HEADER_BAR} 52%, #002814 100%);
                color: #fff !important;
                border-radius: 16px;
                margin: 0;
                padding: 14px 18px 16px;
                box-shadow: none;
                position: relative;
                z-index: 2;
                width: 100%;
                box-sizing: border-box;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-top-bar-inner {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 16px;
                flex-wrap: wrap;
                max-width: 1180px;
                margin: 0 auto;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-header-left {{
                display: flex;
                align-items: center;
                gap: 14px;
                min-width: 0;
                flex: 1 1 280px;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-header-leaf {{
                font-family: "Material Symbols Outlined" !important;
                font-size: 36px !important;
                font-weight: 400 !important;
                color: #fff !important;
                line-height: 1;
                flex-shrink: 0;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-header-titles {{
                min-width: 0;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-header-title {{
                margin: 0 !important;
                font-size: clamp(1rem, 2.2vw, 1.38rem) !important;
                font-weight: 800 !important;
                letter-spacing: -0.02em !important;
                line-height: 1.2 !important;
                color: #fff !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-header-sub {{
                margin: 5px 0 0 0 !important;
                font-size: clamp(0.82rem, 1.5vw, 0.96rem) !important;
                font-weight: 500 !important;
                line-height: 1.35 !important;
                color: rgba(255, 255, 255, 0.95) !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-header-brand img {{
                max-height: 52px;
                width: auto;
                display: block;
                filter: brightness(0) invert(1);
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-header-brand--text {{
                text-align: right;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-header-wordmark {{
                display: block;
                font-weight: 800;
                font-size: 0.82rem;
                letter-spacing: 0.06em;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-header-tag {{
                display: block;
                font-size: 0.72rem;
                opacity: 0.92;
                margin-top: 3px;
                letter-spacing: 0.02em;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-after-hero-spacer {{
                height: 4px;
                margin-bottom: 14px;
            }}
            /* Columna ejemplos: scroll vertical dentro del alto de la fila (evita desborde al abrir las 20 preguntas) */
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stColumn"]:has(.qa-ejemplos-stack) > div[data-testid="stVerticalBlock"] {{
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
                border-radius: 0 !important;
                padding: 0 !important;
                min-height: 0 !important;
                max-height: 100% !important;
                flex: 1 1 auto !important;
                display: flex !important;
                flex-direction: column !important;
                overflow-x: hidden !important;
                overflow-y: auto !important;
                overscroll-behavior: contain !important;
                scrollbar-width: thin !important;
                scrollbar-color: rgba(27, 94, 32, 0.28) transparent !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stColumn"]:has(.qa-ejemplos-stack) > div[data-testid="stVerticalBlock"]::-webkit-scrollbar {{
                width: 8px !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stColumn"]:has(.qa-ejemplos-stack) > div[data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb {{
                background: rgba(27, 94, 32, 0.26) !important;
                border-radius: 8px !important;
            }}
            /* Columna derecha (chat): ocupa toda la altura de la fila ejemplos|chat */
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stColumn"]:has(.qa-chat-stream-root) {{
                align-self: stretch !important;
                display: flex !important;
                flex-direction: column !important;
                min-height: 0 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stColumn"]:has(.qa-chat-stream-root) > div[data-testid="stVerticalBlock"] {{
                flex: 1 1 auto !important;
                width: 100% !important;
                min-height: 0 !important;
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
                border-radius: 0 !important;
                padding: 0 !important;
                display: flex !important;
                flex-direction: column !important;
                overflow-x: hidden !important;
                overflow-y: hidden !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stColumn"]:has(.qa-chat-stream-root) > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] ~ div[data-testid="stLayoutWrapper"] {{
                flex: 1 1 auto !important;
                min-height: 0 !important;
                display: flex !important;
                flex-direction: column !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stColumn"]:has(.qa-chat-stream-root) > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] ~ div[data-testid="stLayoutWrapper"] > div[data-testid="stHorizontalBlock"] {{
                flex: 1 1 auto !important;
                min-height: 0 !important;
                max-height: 100% !important;
                overflow: hidden !important;
                align-items: stretch !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stColumn"]:has(.qa-chat-stream-root) > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] ~ div[data-testid="stLayoutWrapper"] > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {{
                min-height: 0 !important;
                max-height: 100% !important;
                overflow: hidden !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stColumn"]:has(.qa-chat-stream-root) > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] ~ div[data-testid="stLayoutWrapper"] > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] {{
                display: flex !important;
                flex-direction: column !important;
                flex: 1 1 auto !important;
                min-height: 0 !important;
                overflow-x: hidden !important;
                overflow-y: hidden !important;
                gap: 10px !important;
                padding-bottom: 28px !important;
                box-sizing: border-box !important;
            }}
            /* Solo el panel principal de mensajes (no la fila de 4 temas rápidos ni el compositor) */
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stColumn"]:has(.qa-chat-stream-root) > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] ~ div[data-testid="stLayoutWrapper"] > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] > div:has(.qa-chat-transcript-shell) {{
                flex: 1 1 0% !important;
                min-height: 0 !important;
                overflow: hidden !important;
            }}
            /* Altura explícita: el DOM tiene ElementContainer (marcador) antes del LayoutWrapper; sin esto el markdown crece y rompe el flex */
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stColumn"]:has(.qa-chat-stream-root) [data-testid="stElementContainer"]:has(.qa-chat-transcript-shell) {{
                flex: 1 1 0% !important;
                min-height: 0 !important;
                max-height: 100% !important;
                overflow: hidden !important;
                align-self: stretch !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-transcript-shell {{
                box-sizing: border-box !important;
                width: 100% !important;
                flex: 1 1 0% !important;
                min-height: 160px !important;
                height: clamp(200px, calc(100svh - 540px), 720px) !important;
                max-height: min(calc(100svh - 540px), 720px) !important;
                display: flex !important;
                flex-direction: column !important;
                overflow: hidden !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-scroll-viewport {{
                box-sizing: border-box !important;
                width: 100% !important;
                flex: 1 1 auto !important;
                min-height: 0 !important;
                overflow-x: hidden !important;
                overflow-y: auto !important;
                -webkit-overflow-scrolling: touch !important;
                overscroll-behavior: contain !important;
                scrollbar-gutter: stable !important;
                scrollbar-width: thin !important;
                scrollbar-color: rgba(27, 94, 32, 0.35) transparent !important;
                padding: 12px 14px 14px 12px !important;
                margin: 0 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-scroll-viewport::-webkit-scrollbar {{
                width: 8px !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-scroll-viewport::-webkit-scrollbar-track {{
                background: transparent !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-scroll-viewport::-webkit-scrollbar-thumb {{
                background: rgba(27, 94, 32, 0.28) !important;
                border-radius: 8px !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-scroll-viewport::-webkit-scrollbar-thumb:hover {{
                background: rgba(27, 94, 32, 0.42) !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stMarkdownContainer"]:has(.qa-chat-transcript-shell),
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stMarkdown"]:has(.qa-chat-transcript-shell) {{
                min-height: 0 !important;
                overflow: hidden !important;
            }}
            /* Temas rápidos, compositor y limpiar no deben comprimirse */
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stColumn"]:has(.qa-chat-stream-root) > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] ~ div[data-testid="stLayoutWrapper"] > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] > div:not(:has(.qa-chat-transcript-shell)) {{
                flex-shrink: 0 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stColumn"]:has(.qa-ejemplos-stack) {{
                align-self: stretch !important;
                border-right: 1px solid rgba(27, 94, 32, 0.14) !important;
                padding-right: 14px !important;
                margin-right: 8px !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-ejemplos-only-heading {{
                font-size: 0.95rem !important;
                font-weight: 800 !important;
                color: {C_GREEN} !important;
                margin: 0 0 14px 0 !important;
                line-height: 1.3 !important;
                flex-shrink: 0 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stColumn"]:has(.qa-ejemplos-stack) [class*="st-key-qa_ejemplo_"] {{
                margin-bottom: 10px !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stColumn"]:has(.qa-ejemplos-stack) [class*="st-key-qa_ejemplo_"]:last-child {{
                margin-bottom: 0 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) [class*="st-key-qa_ejemplo_"] .stButton > button[kind="secondary"] {{
                background: {C_WHITE} !important;
                border: 1px solid #e0e0e0 !important;
                border-radius: 10px !important;
                color: {C_TEXT} !important;
                min-height: 72px !important;
                padding: 14px 14px !important;
                text-align: left !important;
                justify-content: flex-start !important;
                font-weight: 500 !important;
                font-size: 0.84rem !important;
                line-height: 1.38 !important;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
                flex-direction: row !important;
                align-items: center !important;
                gap: 12px !important;
                white-space: normal !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) [class*="st-key-qa_ejemplo_"] .stButton > button[kind="secondary"] p {{
                color: {C_TEXT} !important;
                text-align: left !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) [class*="st-key-qa_ejemplo_"] .stButton > button[kind="secondary"]:hover {{
                background: #f1f8f4 !important;
                border-color: rgba(27, 94, 32, 0.35) !important;
            }}
            /* 20 preguntas Módulo 1 (debajo de la tarjeta Q&A): sin tope — crece con la página */
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[class*="st-key-qa_m1_below_card"] [data-testid="stExpander"] div[data-testid="stVerticalBlock"] {{
                max-height: none !important;
                min-height: 0 !important;
                overflow-y: visible !important;
                overflow-x: hidden !important;
                box-sizing: border-box !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[class*="st-key-qa_m1_below_card"] [data-testid="stExpander"] details > div:last-child {{
                max-height: none !important;
                min-height: 0 !important;
                overflow-y: visible !important;
                overflow-x: hidden !important;
            }}
            /* Lista Módulo 1: compacta, alineada a la izquierda, sin bloques “pesados” */
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[class*="st-key-qa_m1_below_card"] [data-testid="stExpander"] {{
                border: 1px solid rgba(27, 94, 32, 0.14) !important;
                border-radius: 12px !important;
                background: linear-gradient(180deg, #fafcfb 0%, #f3f7f4 100%) !important;
                box-shadow: 0 1px 3px rgba(0, 50, 30, 0.06) !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[class*="st-key-qa_m1_below_card"] [data-testid="stExpander"] summary {{
                padding: 12px 14px !important;
                font-weight: 700 !important;
                font-size: 0.92rem !important;
                color: {C_GREEN} !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[class*="st-key-qa_m1_below_card"] [data-testid="stExpander"] div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:has(.stButton) {{
                margin-bottom: 5px !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[class*="st-key-qa_m1_below_card"] [data-testid="stExpander"] div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:last-child {{
                margin-bottom: 2px !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[class*="st-key-qa_m1_below_card"] .stButton {{
                width: 100% !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[class*="st-key-qa_m1_below_card"] .stButton > button[kind="secondary"] {{
                width: 100% !important;
                min-height: 0 !important;
                height: auto !important;
                padding: 9px 12px 9px 14px !important;
                justify-content: flex-start !important;
                align-items: flex-start !important;
                text-align: left !important;
                border-radius: 8px !important;
                border: 1px solid rgba(27, 94, 32, 0.1) !important;
                background: #ffffff !important;
                box-shadow: none !important;
                font-weight: 500 !important;
                font-size: 0.8125rem !important;
                line-height: 1.42 !important;
                white-space: normal !important;
                word-break: break-word !important;
                color: {C_TEXT} !important;
                transition: background 0.15s ease, border-color 0.15s ease !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[class*="st-key-qa_m1_below_card"] .stButton > button[kind="secondary"] p {{
                text-align: left !important;
                margin: 0 !important;
                width: 100% !important;
                white-space: normal !important;
                word-break: break-word !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[class*="st-key-qa_m1_below_card"] .stButton > button[kind="secondary"]:hover {{
                background: #eef6ef !important;
                border-color: rgba(27, 94, 32, 0.28) !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[class*="st-key-qa_m1_below_card"] [data-testid="stExpander"] .stCaption {{
                font-size: 0.78rem !important;
                line-height: 1.45 !important;
                color: {C_TEXT_MUTED} !important;
                margin-bottom: 10px !important;
                padding: 0 2px !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-m1-below-spacer {{
                display: block !important;
                margin-top: 1.35rem !important;
                height: 0 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-wrap {{
                width: 100%;
                max-width: 100%;
                margin: 0;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-scroll-viewport .qa-chat-wrap:last-child .qa-chat-row {{
                margin-bottom: 6px !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-row {{
                display: flex;
                align-items: flex-end;
                gap: 12px;
                margin-bottom: 14px;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-row--user {{
                flex-direction: row-reverse;
                justify-content: flex-start;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-row--bot {{
                flex-direction: row;
                justify-content: flex-start;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bubble--user {{
                max-width: min(82%, 520px);
                background: #d9eedb !important;
                border: 1px solid rgba(27, 94, 32, 0.22) !important;
                border-radius: 16px 16px 6px 16px !important;
                padding: 14px 16px 12px !important;
                box-shadow: 0 1px 3px rgba(27, 94, 32, 0.08);
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bubble--user p {{
                margin: 0 0 8px 0 !important;
                font-size: 0.95rem !important;
                line-height: 1.45 !important;
                color: #212121 !important;
                font-weight: 500;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-time {{
                font-size: 0.78rem !important;
                color: {C_TEXT_MUTED} !important;
                display: block;
                text-align: right;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-time--bot {{
                margin-top: 12px !important;
                display: block !important;
                text-align: right !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-avatar--user {{
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: {C_QA_HEADER_BAR} !important;
                color: #ffffff !important;
                display: flex !important;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
                box-shadow: 0 2px 8px rgba(27, 94, 32, 0.25);
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-avatar--user span.material-symbols-outlined,
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-avatar--user span {{
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
                font-size: 22px !important;
                font-weight: 400 !important;
                font-variation-settings: "FILL" 1, "wght" 500, "GRAD" 0, "opsz" 24 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bubble--bot {{
                flex: 0 1 auto !important;
                min-width: 0 !important;
                max-width: min(100%, 600px) !important;
                background: {C_WHITE} !important;
                border: 1px solid #e0e0e0 !important;
                border-radius: 16px 16px 16px 6px !important;
                padding: 14px 16px !important;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06) !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bot-body {{
                font-size: 0.95rem !important;
                line-height: 1.58 !important;
                color: #263238 !important;
            }}
            /* Contenido Markdown renderizado en burbuja del bot */
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bot-body.qa-chat-bot-md p {{
                margin: 0 0 0.65em 0 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bot-body.qa-chat-bot-md p:last-child {{
                margin-bottom: 0 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bot-body.qa-chat-bot-md h1,
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bot-body.qa-chat-bot-md h2,
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bot-body.qa-chat-bot-md h3,
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bot-body.qa-chat-bot-md h4 {{
                font-weight: 800 !important;
                margin: 0.95em 0 0.45em 0 !important;
                color: {C_GREEN} !important;
                line-height: 1.28 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bot-body.qa-chat-bot-md h1 {{
                font-size: 1.12rem !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bot-body.qa-chat-bot-md h2 {{
                font-size: 1.06rem !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bot-body.qa-chat-bot-md h3,
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bot-body.qa-chat-bot-md h4 {{
                font-size: 1.02rem !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bot-body.qa-chat-bot-md h1:first-child,
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bot-body.qa-chat-bot-md h2:first-child,
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bot-body.qa-chat-bot-md h3:first-child,
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bot-body.qa-chat-bot-md h4:first-child {{
                margin-top: 0 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bot-body.qa-chat-bot-md ul,
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bot-body.qa-chat-bot-md ol {{
                margin: 0.35em 0 0.75em 0 !important;
                padding-left: 1.35rem !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bot-body.qa-chat-bot-md li {{
                margin: 0.3em 0 !important;
                line-height: 1.5 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bot-body.qa-chat-bot-md li > p {{
                margin: 0.15em 0 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bot-body.qa-chat-bot-md strong {{
                font-weight: 700 !important;
                color: #1b3039 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bot-body.qa-chat-bot-md code {{
                font-family: ui-monospace, "Cascadia Code", "Segoe UI Mono", monospace !important;
                font-size: 0.88em !important;
                background: #eef2f0 !important;
                padding: 0.12em 0.38em !important;
                border-radius: 4px !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bot-body.qa-chat-bot-md blockquote {{
                margin: 0.5em 0 !important;
                padding: 0.35em 0 0.35em 0.85em !important;
                border-left: 3px solid rgba(27, 94, 32, 0.35) !important;
                color: #455a64 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-bot-body.qa-chat-bot-md a {{
                color: #1565c0 !important;
                text-decoration: underline !important;
                text-underline-offset: 2px !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-avatar--bot {{
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: {C_QA_HEADER_BAR} !important;
                display: flex !important;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
                overflow: hidden;
                box-shadow: 0 2px 8px rgba(27, 94, 32, 0.2);
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-avatar--bot img {{
                width: 70%;
                height: 70%;
                object-fit: contain;
                filter: brightness(0) invert(1);
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-chat-avatar--bot span {{
                color: {C_WHITE} !important;
                font-size: 22px !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-empty-hint {{
                text-align: center;
                color: {C_TEXT_MUTED};
                font-size: 0.9rem;
                margin: 12px 12px 12px 12px !important;
                line-height: 1.55;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) .qa-quick-lead {{
                text-align: center !important;
                color: {C_GREEN} !important;
                font-weight: 700 !important;
                font-size: 0.92rem !important;
                letter-spacing: 0.01em !important;
                margin: 2px 0 8px 0 !important;
                padding-top: 0 !important;
            }}
            /* Fila de 4 temas rápidos: menos hueco respecto al compositor */
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stColumn"]:has(.qa-chat-stream-root) div[data-testid="stVerticalBlock"] > div [data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"]:nth-child(4)) {{
                gap: 10px !important;
                margin-bottom: 0 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stColumn"]:has(.qa-chat-stream-root) [class*="st-key-qa_quick_"] .stButton,
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stColumn"]:has(.qa-chat-stream-root) [class*="st-key-qa_quick_"] .stButton > button {{
                width: 100% !important;
                box-sizing: border-box !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) [class*="st-key-qa_quick_"] .stButton > button[kind="secondary"] {{
                background: {C_WHITE} !important;
                color: {C_GREEN} !important;
                border: 1px solid #e0e0e0 !important;
                border-radius: 12px !important;
                min-height: 48px !important;
                height: auto !important;
                white-space: normal !important;
                text-align: left !important;
                font-weight: 600 !important;
                font-size: 0.8rem !important;
                line-height: 1.32 !important;
                padding: 10px 10px !important;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
                flex-direction: row !important;
                gap: 10px !important;
                justify-content: flex-start !important;
                align-items: center !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) [class*="st-key-qa_quick_"] .stButton > button[kind="secondary"] p,
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) [class*="st-key-qa_quick_"] .stButton > button[kind="secondary"] span,
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) [class*="st-key-qa_quick_"] .stButton > button[kind="secondary"] * {{
                color: {C_GREEN} !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) [class*="st-key-qa_quick_"] .stButton > button[kind="secondary"]:hover {{
                background: #f1f8f4 !important;
                border-color: {C_GREEN} !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) [class*="st-key-qa_limpiar"] {{
                display: flex !important;
                justify-content: flex-start !important;
                align-items: center !important;
                flex-shrink: 0 !important;
                margin-top: 8px !important;
                margin-bottom: 12px !important;
                padding-bottom: 0 !important;
                padding-left: 2px !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) [class*="st-key-qa_limpiar"] .stButton > button[kind="secondary"] {{
                background: {C_WHITE} !important;
                border: 1px solid #cfd8dc !important;
                color: #455a64 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) [class*="st-key-qa_limpiar"] .stButton > button[kind="secondary"] p,
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) [class*="st-key-qa_limpiar"] .stButton > button[kind="secondary"] span,
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) [class*="st-key-qa_limpiar"] .stButton > button[kind="secondary"] * {{
                color: #455a64 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stColumn"]:has(.qa-chat-stream-root) div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) {{
                align-items: center !important;
                align-content: center !important;
                gap: 8px !important;
                border: 2px solid {C_GREEN} !important;
                background: {C_WHITE} !important;
                border-radius: 12px !important;
                box-shadow: 0 2px 12px rgba(27, 94, 32, 0.08) !important;
                margin-top: 4px !important;
                margin-bottom: 2px !important;
                padding: 6px 8px 6px 12px !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stColumn"]:has(.qa-chat-stream-root) div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) .stButton > button {{
                border-radius: 10px !important;
                height: 40px !important;
                max-height: 40px !important;
                min-height: 40px !important;
                padding: 0 16px !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stColumn"]:has(.qa-chat-stream-root) div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) [data-testid="stTextInput"] input {{
                min-height: 38px !important;
                height: 38px !important;
                padding: 6px 4px 6px 2px !important;
                line-height: 1.35 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stColumn"]:has(.qa-chat-stream-root) div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) .stTextInput fieldset,
            [data-testid="stAppViewContainer"]:has(#qa-page-mount) div[data-testid="stColumn"]:has(.qa-chat-stream-root) div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) [data-testid="stTextInput"] fieldset {{
                min-height: 0 !important;
                padding-top: 0 !important;
                padding-bottom: 0 !important;
            }}
            /* Misma fila compacta aunque cambie el anidamiento de columnas Streamlit */
            html:has(#qa-page-mount) div[class*="st-key-qa_unified_card"] [data-testid="stVerticalBlock"][class*="st-key-qa_chat_inset"] [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) {{
                align-items: center !important;
                align-content: center !important;
                gap: 8px !important;
                border: 2px solid {C_GREEN} !important;
                background: {C_WHITE} !important;
                border-radius: 12px !important;
                box-shadow: 0 2px 12px rgba(27, 94, 32, 0.08) !important;
                margin-top: 4px !important;
                margin-bottom: 2px !important;
                padding: 6px 8px 6px 12px !important;
            }}
            html:has(#qa-page-mount) div[class*="st-key-qa_unified_card"] [data-testid="stVerticalBlock"][class*="st-key-qa_chat_inset"] [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) .stButton > button {{
                border-radius: 10px !important;
                height: 40px !important;
                max-height: 40px !important;
                min-height: 40px !important;
                padding: 0 16px !important;
            }}
            html:has(#qa-page-mount) div[class*="st-key-qa_unified_card"] [data-testid="stVerticalBlock"][class*="st-key-qa_chat_inset"] [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) [data-testid="stTextInput"] input {{
                min-height: 38px !important;
                height: 38px !important;
                padding: 6px 4px 6px 2px !important;
                line-height: 1.35 !important;
            }}
            html:has(#qa-page-mount) div[class*="st-key-qa_unified_card"] [data-testid="stVerticalBlock"][class*="st-key-qa_chat_inset"] [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) .stTextInput fieldset,
            html:has(#qa-page-mount) div[class*="st-key-qa_unified_card"] [data-testid="stVerticalBlock"][class*="st-key-qa_chat_inset"] [data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) [data-testid="stTextInput"] fieldset {{
                min-height: 0 !important;
                padding-top: 0 !important;
                padding-bottom: 0 !important;
            }}

            /* Inicio: una sola tarjeta verde menta envuelve compositor + respuesta */
            [data-testid="stMainBlockContainer"] div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"]:first-child .qa-composer-surface-anchor):has(> div[data-testid="stColumn"]:nth-child(2)) {{
                background: linear-gradient(180deg, {C_GREEN_SOFT} 0%, #e8f5e9 100%) !important;
                border: 1px solid rgba(27, 94, 32, 0.18) !important;
                border-radius: var(--rc-radius-lg) !important;
                padding: 24px 24px 26px !important;
                box-shadow: var(--rc-shadow-soft) !important;
                gap: 22px !important;
                align-items: stretch !important;
            }}
            [data-testid="stMainBlockContainer"] div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"]:first-child .qa-composer-surface-anchor):has(> div[data-testid="stColumn"]:nth-child(2)) > div[data-testid="stColumn"]:has(.qa-composer-surface-anchor) {{
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
                padding: 0 !important;
            }}

            [data-testid="stSidebar"] [data-testid="stImage"] img {{
                width: 100% !important;
                border-radius: 0;
                box-shadow: none;
                mask-image: none;
                -webkit-mask-image: none;
                object-fit: contain;
            }}

            /* Botón primario: texto/icono en blanco (stMain span/p forzaba gris con !important) */
            [data-testid="stMainBlockContainer"] div.stButton > button[kind="primary"] {{
                background: {C_GREEN} !important;
                color: {C_WHITE} !important;
                border: none !important;
                border-radius: var(--rc-radius-md) !important;
                font-weight: 600 !important;
                letter-spacing: 0.02em !important;
            }}
            [data-testid="stMainBlockContainer"] div.stButton > button[kind="primary"] p,
            [data-testid="stMainBlockContainer"] div.stButton > button[kind="primary"] span,
            [data-testid="stMainBlockContainer"] div.stButton > button[kind="primary"] * {{
                color: {C_WHITE} !important;
            }}

            /* Pie de página: solo línea divisoria + texto (sin caja blanca), todas las páginas */
            [data-testid="stMain"] .app-footer-wrap {{
                margin-top: 2rem;
                width: 100%;
                max-width: 100%;
                box-sizing: border-box;
                padding-top: 1.35rem;
                border: none;
                background-image: linear-gradient(
                    90deg,
                    transparent 0%,
                    var(--rc-line) 12%,
                    var(--rc-line) 88%,
                    transparent 100%
                );
                background-size: 100% 1px;
                background-repeat: no-repeat;
                background-position: 0 0;
            }}
            [data-testid="stMain"] .app-footer-inner {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 1rem 1.5rem;
                flex-wrap: wrap;
                padding: 0;
                background: transparent !important;
                border: none !important;
                border-radius: 0 !important;
                box-shadow: none !important;
            }}
            [data-testid="stMain"] .app-footer-copy {{
                margin: 0;
                padding: 0;
                font-size: 0.875rem;
                line-height: 1.5;
                color: #546e7a !important;
                font-weight: 500;
                letter-spacing: 0.01em;
                flex: 1 1 auto;
                min-width: min(100%, 16rem);
            }}
            @media (max-width: 599px) {{
                [data-testid="stMain"] .app-footer-inner {{
                    flex-direction: column;
                    text-align: center;
                }}
                [data-testid="stMain"] .app-footer-inner .footer-social {{
                    justify-content: center;
                    width: 100%;
                }}
                [data-testid="stMain"] .app-footer-copy {{
                    text-align: center;
                    width: 100%;
                }}
            }}

            /* Pie: redes sociales con iconos SVG */
            .footer-social {{
                display: flex;
                justify-content: flex-end;
                align-items: center;
                gap: 10px;
                flex-wrap: wrap;
            }}
            .footer-social-link {{
                display: inline-flex !important;
                align-items: center;
                justify-content: center;
                width: 42px;
                height: 42px;
                border-radius: var(--rc-radius-sm);
                background: rgba(38, 50, 56, 0.06);
                color: {C_TEXT_MUTED} !important;
                text-decoration: none !important;
                transition: transform 0.18s ease, background 0.18s ease, color 0.18s ease, box-shadow 0.18s ease;
                box-shadow: 0 1px 2px rgba(0,0,0,0.04);
                border: 1px solid transparent;
            }}
            .footer-social-link:hover {{
                transform: translateY(-2px);
                color: #ffffff !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.12);
            }}
            .footer-social-link--in:hover {{ background: #0a66c2 !important; }}
            .footer-social-link--ig:hover {{
                background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888) !important;
            }}
            .footer-social-link--yt:hover {{ background: #ff0000 !important; }}
            .footer-social-link--fb:hover {{ background: #1877f2 !important; }}
            .footer-social-svg {{
                width: 22px;
                height: 22px;
                display: block;
                flex-shrink: 0;
            }}

            /* ----- Página Resumen (hero tipo banner FAQ: texto izquierda + gradiente; título en carrusel) ----- */
            .resumen-wrap {{
                margin: 12px 0 12px 0;
            }}
            .resumen-columns {{
                margin-top: 0;
                display: grid;
                grid-template-columns: minmax(0, 1fr) minmax(0, 1.38fr);
                gap: 24px;
                align-items: stretch;
            }}
            .resumen-col-left .resumen-block:first-of-type:not(.resumen-block--executive) {{
                margin-bottom: 20px;
                padding-bottom: 22px;
                border-bottom: 1px solid rgba(27, 94, 32, 0.08);
            }}
            @media (max-width: 900px) {{
                .resumen-columns {{ grid-template-columns: 1fr; }}
                .resumen-fab {{ display: none; }}
            }}
            .resumen-card {{
                background: {C_WHITE};
                border-radius: var(--rc-radius-lg);
                border: 1px solid var(--rc-line);
                box-shadow: var(--rc-shadow-soft);
                padding: 26px 24px 28px;
                height: 100%;
                box-sizing: border-box;
            }}
            .resumen-card--right {{
                position: relative;
                padding-right: 22px;
            }}
            .resumen-purpose-stack {{
                display: flex;
                flex-direction: column;
                gap: 22px;
            }}
            .resumen-block {{
                margin-bottom: 22px;
            }}
            .resumen-block:last-child {{
                margin-bottom: 0;
            }}
            .resumen-block-head {{
                display: flex;
                align-items: flex-start;
                gap: 12px;
                margin-bottom: 10px;
            }}
            .resumen-block-head .resumen-ic-emoji {{
                font-size: 1.65rem;
                line-height: 1;
                flex-shrink: 0;
                margin-top: 2px;
                width: 44px;
                text-align: center;
            }}
            [data-testid="stMain"] .resumen-wrap .resumen-block-head .resumen-ic {{
                font-family: "Material Symbols Outlined";
                font-variation-settings: "FILL" 0, "wght" 400, "GRAD" 0, "opsz" 32;
                font-size: 32px;
                line-height: 1;
                color: {C_GREEN} !important;
                flex-shrink: 0;
                margin-top: 2px;
            }}
            .resumen-block-title {{
                margin: 0;
                font-size: 1.05rem;
                font-weight: 700;
                color: {C_GREEN} !important;
                line-height: 1.3;
            }}
            .resumen-block-text {{
                margin: 0;
                font-size: 0.93rem;
                line-height: 1.58;
                color: #37474f !important;
                padding-left: 44px;
            }}
            .resumen-block--purpose .resumen-block-head {{
                align-items: center;
                gap: 14px;
                margin-bottom: 12px;
            }}
            .resumen-block--purpose .resumen-block-head .resumen-ic {{
                width: 48px;
                height: 48px;
                min-width: 48px;
                margin-top: 0 !important;
                display: inline-flex !important;
                align-items: center;
                justify-content: center;
                font-size: 26px !important;
                border-radius: 50%;
                background: linear-gradient(160deg, rgba(27, 94, 32, 0.14), rgba(27, 94, 32, 0.05));
                box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65);
            }}
            .resumen-block--purpose .resumen-block-head .resumen-ic-emoji {{
                width: 48px;
                height: 48px;
                min-width: 48px;
                margin-top: 0 !important;
                display: inline-flex !important;
                align-items: center;
                justify-content: center;
                font-size: 1.35rem !important;
                line-height: 1 !important;
                border-radius: 50%;
                background: linear-gradient(160deg, rgba(27, 94, 32, 0.14), rgba(27, 94, 32, 0.05));
                box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65);
            }}
            .resumen-block--purpose .resumen-block-title {{
                font-size: 1.2rem;
                font-weight: 800;
                letter-spacing: -0.025em;
            }}
            .resumen-block--purpose .resumen-block-text {{
                padding-left: 0;
                margin-left: 0;
                font-size: 0.96rem;
                line-height: 1.68;
                color: #455a64 !important;
                letter-spacing: 0.01em;
            }}
            .resumen-stats-wrap {{
                position: relative;
                margin: 0;
                padding-right: 26px;
            }}
            .resumen-stats {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 0;
                margin: 0;
                padding: 6px 0;
                background: linear-gradient(165deg, #f4faf4 0%, #e8f5e9 45%, #dff0e2 100%);
                border-radius: 14px;
                border: 1px solid rgba(27, 94, 32, 0.16);
                box-shadow:
                    inset 0 1px 0 rgba(255, 255, 255, 0.85),
                    0 6px 20px rgba(27, 94, 32, 0.08);
                overflow: visible;
            }}
            .resumen-stat-cell {{
                position: relative;
                padding: 20px 16px;
                text-align: center;
            }}
            @media (min-width: 721px) {{
                .resumen-stat-cell:not(:nth-child(4n))::after {{
                    content: "";
                    position: absolute;
                    right: 0;
                    top: 18%;
                    bottom: 18%;
                    width: 1px;
                    background: linear-gradient(
                        180deg,
                        transparent 0%,
                        rgba(27, 94, 32, 0.14) 35%,
                        rgba(27, 94, 32, 0.14) 65%,
                        transparent 100%
                    );
                }}
            }}
            @media (max-width: 720px) {{
                .resumen-stats {{ grid-template-columns: repeat(2, 1fr); }}
                .resumen-stat-cell::after {{ content: none; }}
                .resumen-stat-cell:nth-child(odd)::after {{
                    content: "";
                    position: absolute;
                    right: 0;
                    top: 15%;
                    bottom: 15%;
                    width: 1px;
                    background: linear-gradient(
                        180deg,
                        transparent 0%,
                        rgba(27, 94, 32, 0.12) 40%,
                        rgba(27, 94, 32, 0.12) 60%,
                        transparent 100%
                    );
                }}
                .resumen-stat-cell {{
                    border-bottom: 1px solid rgba(27, 94, 32, 0.08);
                }}
                .resumen-stat-cell:nth-last-child(-n + 2) {{
                    border-bottom: none;
                }}
            }}
            .resumen-wrap .resumen-stat-val {{
                display: block;
                font-size: 1.03rem;
                font-weight: 800;
                color: {C_GREEN} !important;
                line-height: 1.28;
                letter-spacing: -0.02em;
            }}
            .resumen-wrap .resumen-stat-lbl {{
                display: block;
                font-size: 0.74rem;
                font-weight: 500;
                color: {C_TEXT_MUTED} !important;
                margin-top: 6px;
                line-height: 1.35;
            }}
            .resumen-biz-grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 12px 8px;
                margin-top: 12px;
            }}
            @media (max-width: 720px) {{
                .resumen-biz-grid {{ grid-template-columns: repeat(2, 1fr); }}
            }}
            .resumen-biz-item {{
                text-align: center;
            }}
            [data-testid="stMain"] .resumen-wrap .resumen-biz-item .resumen-ic {{
                font-family: "Material Symbols Outlined";
                font-variation-settings: "FILL" 0, "wght" 400, "GRAD" 0, "opsz" 40;
                font-size: 36px;
                line-height: 1;
                color: {C_GREEN} !important;
                display: block;
                margin: 0 auto 8px auto;
            }}
            [data-testid="stMain"] .resumen-wrap .resumen-biz-item .resumen-biz-lbl {{
                margin: 0;
                font-size: 0.78rem;
                font-weight: 600;
                color: {C_TEXT_MUTED} !important;
                line-height: 1.35;
            }}
            .resumen-fab {{
                position: absolute;
                width: 46px;
                height: 46px;
                border-radius: 50%;
                background: linear-gradient(165deg, #546e7a, #455a64) !important;
                color: #fff !important;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                text-decoration: none !important;
                line-height: 1;
                border: 3px solid {C_WHITE};
                box-shadow:
                    0 4px 14px rgba(0, 0, 0, 0.15),
                    0 0 0 1px rgba(27, 94, 32, 0.08);
                transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
                z-index: 4;
            }}
            .resumen-stats-wrap .resumen-fab {{
                right: 0;
                top: 50%;
                transform: translate(42%, -50%);
            }}
            .resumen-fab-icon {{
                font-size: 1.28rem;
                font-weight: 400;
                line-height: 1;
                margin-left: 2px;
            }}
            .resumen-fab:hover {{
                filter: brightness(1.05);
                box-shadow:
                    0 6px 20px rgba(0, 0, 0, 0.2),
                    0 0 0 1px rgba(27, 94, 32, 0.1);
            }}
            .resumen-stats-wrap .resumen-fab:hover {{
                transform: translate(42%, -50%) scale(1.06);
            }}
            .resumen-wrap .resumen-fab,
            .resumen-wrap .resumen-fab .resumen-fab-icon {{
                color: #fff !important;
            }}
            .resumen-footbar {{
                margin-top: 26px;
                display: flex;
                align-items: center;
                gap: 16px;
                padding: 18px 22px;
                background: linear-gradient(180deg, #f4faf4 0%, {C_GREEN_SOFT} 100%);
                border-radius: var(--rc-radius-md);
                border: 1px solid var(--rc-line-green);
                box-shadow: var(--rc-shadow-soft);
            }}
            [data-testid="stMain"] .resumen-wrap .resumen-footbar .resumen-foot-emoji {{
                font-size: 1.35rem;
                line-height: 1;
                flex-shrink: 0;
                margin-right: 4px;
            }}
            [data-testid="stMain"] .resumen-wrap .resumen-footbar p,
            [data-testid="stMain"] .resumen-wrap .resumen-footbar .resumen-foot-md {{
                flex: 1;
                max-width: 56rem;
                margin: 0 auto;
                text-align: center;
                font-size: 0.88rem;
                line-height: 1.5;
                color: #37474f !important;
                font-weight: 500;
            }}
            .resumen-purpose-md.resumen-ai-md {{
                padding-left: 0;
            }}
            .resumen-purpose-fallback,
            .resumen-foot-fallback {{
                margin: 0 !important;
                font-style: italic;
                color: #78909c !important;
                font-weight: 400 !important;
            }}

            .resumen-lineas-heading {{
                display: flex;
                align-items: center;
                gap: 14px;
                margin: 8px 0 20px 0;
            }}
            [data-testid="stMain"] .resumen-lineas-heading .resumen-ic {{
                font-family: "Material Symbols Outlined";
                font-variation-settings: "FILL" 0, "wght" 400, "GRAD" 0, "opsz" 32;
                font-size: 32px;
                color: {C_GREEN} !important;
            }}
            .resumen-lineas-h {{
                margin: 0;
                font-size: 1.08rem;
                font-weight: 800;
                letter-spacing: -0.02em;
                color: {C_GREEN} !important;
            }}
            .resumen-biz-click {{
                text-align: center;
                margin-bottom: 4px;
            }}
            [data-testid="stMain"] .resumen-biz-click .material-symbols-outlined {{
                font-family: "Material Symbols Outlined";
                font-variation-settings: "FILL" 0, "wght" 400, "GRAD" 0, "opsz" 40;
                font-size: 38px;
                color: {C_GREEN} !important;
                line-height: 1;
                display: block;
            }}
            .resumen-productos-box {{
                margin-top: 20px;
                padding: 20px 22px;
                background: linear-gradient(180deg, #ffffff 0%, {C_GREEN_SOFT} 100%);
                border-radius: var(--rc-radius-md);
                border: 1px solid var(--rc-line-green);
                box-shadow: var(--rc-shadow-soft);
            }}
            .resumen-productos-box h4 {{
                margin: 0 0 10px 0;
                font-size: 1.02rem;
                font-weight: 700;
                color: {C_GREEN} !important;
            }}
            .resumen-productos-box ul {{
                margin: 0;
                padding-left: 1.25rem;
                color: #37474f !important;
                font-size: 0.93rem;
                line-height: 1.55;
            }}
            .resumen-productos-box li {{
                margin-bottom: 6px;
            }}

            .resumen-page-mount {{
                display: none !important;
            }}
            [data-testid="stAppViewContainer"]:has(#resumen-page-mount) [data-testid="stMainBlockContainer"] {{
                max-width: 1180px;
            }}
            .resumen-ai-body {{
                margin: 4px 0 0 0;
                padding-left: 44px;
                font-size: 0.93rem;
                line-height: 1.58;
                color: #37474f !important;
                text-align: left !important;
                max-width: 72ch;
            }}
            .resumen-wrap .resumen-ai-md p {{
                margin: 0 0 0.85em 0;
            }}
            .resumen-wrap .resumen-ai-md p:last-child {{
                margin-bottom: 0;
            }}
            .resumen-wrap .resumen-ai-md h1,
            .resumen-wrap .resumen-ai-md h2,
            .resumen-wrap .resumen-ai-md h3,
            .resumen-wrap .resumen-ai-md h4 {{
                margin: 1.15em 0 0.45em 0;
                font-weight: 800;
                color: {C_GREEN} !important;
                line-height: 1.25;
                letter-spacing: -0.02em;
            }}
            .resumen-wrap .resumen-ai-md h1:first-child,
            .resumen-wrap .resumen-ai-md h2:first-child,
            .resumen-wrap .resumen-ai-md h3:first-child,
            .resumen-wrap .resumen-ai-md h4:first-child {{
                margin-top: 0;
            }}
            .resumen-wrap .resumen-ai-md ul,
            .resumen-wrap .resumen-ai-md ol {{
                margin: 0 0 0.85em 0;
                padding-left: 1.35rem;
            }}
            .resumen-wrap .resumen-ai-md li {{
                margin-bottom: 0.35em;
            }}
            .resumen-wrap .resumen-ai-md li > p {{
                margin: 0;
            }}
            .resumen-wrap .resumen-ai-md strong {{
                font-weight: 700;
                color: #263238 !important;
            }}
            .resumen-wrap .resumen-ai-md code {{
                font-size: 0.88em;
                padding: 0.12em 0.35em;
                border-radius: 6px;
                background: rgba(27, 94, 32, 0.06);
            }}
            .resumen-wrap .resumen-ai-md blockquote {{
                margin: 0.75em 0;
                padding: 10px 14px;
                border-left: 3px solid rgba(27, 94, 32, 0.35);
                background: rgba(232, 245, 233, 0.55);
                border-radius: 0 10px 10px 0;
            }}
            .resumen-wrap .resumen-ai-md a {{
                color: {C_GREEN} !important;
                text-underline-offset: 2px;
            }}

            /* ----- FAQ: panel lista temas + respuesta (diseño original) ----- */
            .faq-page-mount {{
                display: none !important;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stMainBlockContainer"] {{
                max-width: 1180px;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] {{
                gap: 2.25rem !important;
                align-items: stretch !important;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) h1,
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) h2,
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) h3 {{
                color: {C_FAQ_PRIMARY} !important;
            }}
            .faq-sidebar-eyebrow {{
                margin: 0 !important;
                padding: 14px 18px 8px 18px !important;
                font-size: 0.72rem !important;
                font-weight: 800 !important;
                letter-spacing: 0.16em !important;
                text-transform: uppercase !important;
                color: #546e7a !important;
                border-bottom: 1px solid rgba({C_FAQ_PRIMARY_RGB}, 0.09) !important;
                text-align: left !important;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) [data-testid="stVerticalBlock"] {{
                background: {C_FAQ_SIDEBAR} !important;
                border: 1px solid {C_FAQ_SIDEBAR_BORDER};
                border-radius: var(--rc-radius-lg);
                box-shadow:
                    0 1px 3px rgba(0, 0, 0, 0.06),
                    0 12px 40px rgba({C_FAQ_PRIMARY_RGB}, 0.07);
                padding: 0 !important;
                margin-top: 8px;
                gap: 0 !important;
                overflow: hidden;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) [data-testid="stVerticalBlock"] [data-testid="stElementContainer"] {{
                margin: 0 !important;
                width: 100% !important;
                padding-left: 0 !important;
                padding-right: 0 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) [data-testid="stVerticalBlock"] [data-testid="stElementContainer"]:first-of-type .stMarkdown {{
                padding: 0 !important;
                margin: 0 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(2) > div[data-testid="stVerticalBlock"] {{
                gap: 0 !important;
                margin-top: 0 !important;
                padding-top: 0 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(2) [data-testid="stElementContainer"] {{
                margin: 0 !important;
                padding-left: 0 !important;
                padding-right: 0 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton {{
                width: 100%;
                margin: 0 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button {{
                width: 100% !important;
                display: flex !important;
                flex-direction: row !important;
                align-items: flex-start !important;
                justify-content: space-between !important;
                gap: 10px !important;
                border-radius: 0 !important;
                border: none !important;
                border-bottom: 1px solid #eceff1 !important;
                padding: 16px 18px !important;
                min-height: 0 !important;
                height: auto !important;
                font-weight: 700 !important;
                font-size: 0.88rem !important;
                line-height: 1.4 !important;
                letter-spacing: -0.01em;
                box-shadow: none !important;
                text-align: left !important;
                transition: background 0.18s ease, color 0.18s ease;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button:focus-visible {{
                outline: 2px solid rgba({C_FAQ_PRIMARY_RGB}, 0.35) !important;
                outline-offset: -2px !important;
                position: relative;
                z-index: 1;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button[kind="secondary"]::after,
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button[kind="primary"]::after {{
                content: "" !important;
                display: inline-block !important;
                width: 7px !important;
                height: 7px !important;
                border-right: 2px solid {C_FAQ_ACCENT} !important;
                border-bottom: 2px solid {C_FAQ_ACCENT} !important;
                transform: rotate(-45deg) !important;
                flex-shrink: 0 !important;
                margin: 0.4em 2px 0 8px !important;
                opacity: 0.9 !important;
                vertical-align: middle !important;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [class*="st-key-faq_sub"] .stButton > button[kind="primary"]::after {{
                content: none !important;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) [data-testid="stVerticalBlock"] [data-testid="stElementContainer"]:has(.stButton):last-of-type .stButton > button {{
                border-bottom: none !important;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button[kind="secondary"] {{
                background: #ffffff !important;
                color: #263238 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button[kind="secondary"] p,
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button[kind="secondary"] span,
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button[kind="secondary"] * {{
                color: #263238 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button[kind="secondary"]:hover {{
                background: {C_FAQ_MIST} !important;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button[kind="primary"] {{
                background: {C_FAQ_SOFT} !important;
                color: {C_FAQ_PRIMARY} !important;
                border-bottom: 1px solid rgba({C_FAQ_PRIMARY_RGB}, 0.12) !important;
                box-shadow: inset 4px 0 0 {C_FAQ_ACCENT} !important;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button[kind="primary"] p,
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button[kind="primary"] span,
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button[kind="primary"] * {{
                color: {C_FAQ_PRIMARY} !important;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button[kind="tertiary"] {{
                background: #ffffff !important;
                color: #455a64 !important;
                border: none !important;
                border-bottom: 1px solid #eceff1 !important;
                border-radius: 0 !important;
                margin: 0 !important;
                width: 100% !important;
                padding: 16px 18px !important;
                font-size: 0.84rem !important;
                font-weight: 600 !important;
                justify-content: flex-start !important;
                letter-spacing: -0.01em;
                line-height: 1.45 !important;
                box-shadow: none !important;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [class*="st-key-faq_sub"] .stButton > button[kind="tertiary"]:hover {{
                background: {C_FAQ_MIST} !important;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [class*="st-key-faq_sub"] .stButton > button[kind="primary"] {{
                box-shadow: inset 4px 0 0 {C_FAQ_ACCENT} !important;
                background: {C_FAQ_SOFT} !important;
                border-bottom: 1px solid rgba({C_FAQ_PRIMARY_RGB}, 0.12) !important;
                font-weight: 600 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button[kind="tertiary"] p,
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button[kind="tertiary"] span,
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button[kind="tertiary"] * {{
                color: #455a64 !important;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button[kind="tertiary"]::after {{
                content: none !important;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton [data-testid="stMarkdownContainer"] {{
                flex: 1 1 auto !important;
                min-width: 0 !important;
                display: flex !important;
                flex-direction: row !important;
                justify-content: flex-start !important;
                align-items: flex-start !important;
                text-align: left !important;
                width: 100% !important;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton [data-testid="stMarkdownContainer"] p {{
                text-align: left !important;
                width: 100% !important;
                margin: 0 !important;
                display: block !important;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button p {{
                flex: 1 1 auto !important;
                margin: 0 !important;
                text-align: left !important;
                align-self: stretch !important;
                white-space: normal !important;
                min-width: 0 !important;
                display: block !important;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button span {{
                text-align: left !important;
            }}
            .faq-answer-card {{
                position: relative;
                background: {C_WHITE};
                border-radius: var(--rc-radius-lg);
                border: 1px solid rgba({C_FAQ_PRIMARY_RGB}, 0.1);
                box-shadow:
                    0 1px 0 rgba(255, 255, 255, 1) inset,
                    0 14px 40px rgba({C_FAQ_PRIMARY_RGB}, 0.09),
                    0 4px 12px rgba(0, 0, 0, 0.04);
                padding: 30px 30px 32px;
                margin-top: 6px;
                overflow: hidden;
                max-width: 100%;
            }}
            .faq-answer-card::before {{
                content: "";
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, {C_FAQ_PRIMARY} 0%, {C_FAQ_PRIMARY_MID} 45%, #f4b584 100%);
                opacity: 1;
                pointer-events: none;
            }}
            .faq-answer-head {{
                display: flex;
                align-items: flex-start;
                gap: 14px;
                margin-bottom: 16px;
            }}
            .faq-answer-ic {{
                font-family: "Material Symbols Outlined";
                font-variation-settings: "FILL" 0, "wght" 500, "GRAD" 0, "opsz" 28;
                font-size: 24px;
                line-height: 1;
                width: 44px;
                height: 44px;
                min-width: 44px;
                display: inline-flex !important;
                align-items: center;
                justify-content: center;
                border-radius: 12px;
                background: linear-gradient(155deg, rgba({C_FAQ_PRIMARY_RGB}, 0.18), rgba({C_FAQ_PRIMARY_RGB}, 0.06));
                color: {C_FAQ_PRIMARY_MID} !important;
                flex-shrink: 0;
                margin-top: 1px;
                box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.75);
            }}
            /* st.html no carga Material Symbols: emoji estable para iconos de FAQ */
            .faq-answer-ic.faq-answer-ic-emoji {{
                font-family: "Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji", sans-serif !important;
                font-variation-settings: normal !important;
                font-size: 22px !important;
                line-height: 1 !important;
            }}
            .faq-answer-q {{
                margin: 0;
                padding-top: 2px;
                font-size: 1.125rem;
                font-weight: 800;
                letter-spacing: -0.028em;
                line-height: 1.3;
                color: {C_FAQ_PRIMARY} !important;
                text-align: left !important;
            }}
            .faq-answer-meta {{
                margin: 0 0 20px 0;
                font-size: 0.8125rem;
                line-height: 1.45;
                color: #607d8b !important;
                text-align: left !important;
            }}
            .faq-answer-body {{
                margin: 0 0 18px 0;
                font-size: 0.9375rem;
                line-height: 1.65;
                color: #455a64 !important;
                text-align: left !important;
                max-width: 65ch;
                word-wrap: break-word;
            }}
            .faq-answer-body p {{
                margin: 0 0 0.85em 0;
            }}
            .faq-answer-body p:last-child {{
                margin-bottom: 0;
            }}
            .faq-answer-body.faq-answer-body-md ul,
            .faq-answer-body.faq-answer-body-md ol {{
                margin: 0 0 0.85em 0;
                padding-left: 1.25rem;
                color: #455a64 !important;
            }}
            .faq-answer-body.faq-answer-body-md li {{
                margin-bottom: 0.35em;
            }}
            .faq-answer-body.faq-answer-body-md li > p {{
                margin: 0;
            }}
            .faq-answer-body.faq-answer-body-md strong {{
                font-weight: 700;
                color: #37474f !important;
            }}
            .faq-answer-body.faq-answer-body-md h1,
            .faq-answer-body.faq-answer-body-md h2,
            .faq-answer-body.faq-answer-body-md h3,
            .faq-answer-body.faq-answer-body-md h4 {{
                margin: 1em 0 0.4em 0;
                font-weight: 800;
                font-size: 1rem;
                color: {C_FAQ_PRIMARY} !important;
                line-height: 1.3;
            }}
            .faq-answer-body.faq-answer-body-md h3:first-child,
            .faq-answer-body.faq-answer-body-md h4:first-child,
            .faq-answer-body.faq-answer-body-md p:first-child {{
                margin-top: 0;
            }}
            .faq-answer-body.faq-answer-body-md a {{
                color: {C_FAQ_PRIMARY_MID} !important;
                text-underline-offset: 2px;
            }}
            .faq-answer-body-empty {{
                margin: 0;
                font-style: italic;
                color: #78909c !important;
            }}
            .faq-callout {{
                background: linear-gradient(165deg, {C_FAQ_MIST} 0%, {C_FAQ_SOFT} 100%);
                border: 1px solid {C_FAQ_CALLOUT_BORDER};
                border-radius: 12px;
                padding: 16px 18px;
                box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
                margin-top: 4px;
            }}
            .faq-callout-title {{
                margin: 0 0 14px 0;
                font-size: 0.92rem;
                font-weight: 800;
                letter-spacing: -0.02em;
                color: {C_FAQ_PRIMARY} !important;
                text-align: left !important;
            }}
            .faq-callout-list {{
                list-style: none;
                margin: 0;
                padding: 0;
            }}
            .faq-callout-list li {{
                display: flex;
                align-items: flex-start;
                gap: 12px;
                margin-bottom: 12px;
                font-size: 0.87rem;
                line-height: 1.52;
                color: #455a64 !important;
            }}
            .faq-callout-list li:last-child {{
                margin-bottom: 0;
            }}
            .faq-callout-ic {{
                font-family: "Material Symbols Outlined";
                font-variation-settings: "FILL" 0, "wght" 400, "GRAD" 0, "opsz" 22;
                font-size: 20px;
                color: {C_FAQ_PRIMARY_MID} !important;
                flex-shrink: 0;
                margin-top: 1px;
            }}
            [data-testid="stAppViewContainer"]:has(#faq-page-mount) [data-testid="stCaption"] {{
                text-align: left !important;
                color: {C_TEXT_MUTED} !important;
                margin-top: 1.25rem !important;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ----- API y modelo -----
def _configurar_groq_api_key() -> None:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if key:
        os.environ["GROQ_API_KEY"] = key
        return
    try:
        if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
            sk = str(st.secrets["GROQ_API_KEY"]).strip()
            if sk:
                os.environ["GROQ_API_KEY"] = sk
    except Exception:
        pass


def obtener_contexto() -> str:
    ctx = contexto_para_prompt()
    if not ctx.strip():
        return (
            "Error: No se encontró el archivo de conocimiento o está vacío: "
            f"{PATH_CONSOLIDADO}"
        )
    return ctx


def responder(pregunta: str, historial) -> str:
    del historial
    try:
        return invocar_qa(pregunta.strip())
    except Exception as e:
        msg = str(e)
        if "401" in msg or "invalid_api_key" in msg.lower():
            return (
                "⚠️ La clave de Groq no es válida o fue revocada. "
                "Genera una nueva en https://console.groq.com/keys , "
                "pégala en `.streamlit/secrets.toml` como `GROQ_API_KEY` "
                "(o en la variable de entorno `GROQ_API_KEY`) y reinicia Streamlit."
            )
        if (
            "413" in msg
            or "rate_limit" in msg.lower()
            or "tokens per minute" in msg.lower()
            or "rate_limit_exceeded" in msg.lower()
        ):
            return (
                "⚠️ La petición supera el límite de tokens de tu plan Groq (mensaje demasiado grande). "
                "Reinicia la app tras el cambio o define en PowerShell, antes de Streamlit: "
                "`$env:KB_MAX_CONTEXT_CHARS='8000'` (prueba 8000–12000). "
                "Con más cuota: https://console.groq.com/settings/billing — "
                "o implementa RAG en un módulo siguiente para no enviar todo el texto."
            )
        return f"⚠️ Error: {msg}"


def obtener_vista_resumen_contexto(max_chars: int = 3500) -> str:
    ctx = obtener_contexto()
    if ctx.startswith("Error:"):
        return ctx
    if len(ctx) <= max_chars:
        return ctx
    return ctx[:max_chars].rstrip() + "…"


def _render_qa_composer(
    *,
    input_key: str,
    button_key: str,
    input_form_label: str,
    show_composer_head: bool = True,
    show_composer_foot: bool = True,
) -> None:
    """Cabecera opcional + fila input / Enviar; pie de disclaimer opcional."""
    st.markdown(
        '<div class="qa-composer-surface-anchor" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )
    if show_composer_head:
        st.markdown(
            """
            <div class="qa-composer-head">
                <h3 class="qa-composer-title">Q&amp;A &mdash; Haz tu pregunta</h3>
                <p class="qa-composer-sub">
                    Historia, sostenibilidad, producci&oacute;n y m&aacute;s. Escribe con libertad:
                    las respuestas se basan en la informaci&oacute;n oficial de Riopaila Castillo.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    row_left, row_btn = st.columns([3.4, 1.15])
    with row_left:
        q = st.text_input(
            input_form_label,
            placeholder="Escribe tu pregunta aquí…",
            label_visibility="collapsed",
            key=input_key,
        )
    with row_btn:
        if st.button(
            "Enviar",
            type="primary",
            key=button_key,
            use_container_width=True,
            icon=":material/send:",
        ):
            _ejecutar_consulta(q)
    if show_composer_foot:
        st.markdown(
            "<p class='qa-composer-foot'>Nuestro asistente responderá basándose únicamente en la "
            "información oficial de Riopaila Castillo.</p>",
            unsafe_allow_html=True,
        )


def _ultimo_par_qa() -> tuple[str, str] | None:
    h = st.session_state.chat_historial
    if len(h) >= 2 and h[-1]["role"] == "assistant" and h[-2]["role"] == "user":
        return h[-2]["content"], h[-1]["content"]
    return None


def _formato_hora_es(when: datetime | None = None) -> str:
    """Hora local estilo 10:32 a. m. / p. m. (se recalcula en cada ejecución de Streamlit)."""
    now = when or datetime.now()
    h12 = now.hour % 12
    if h12 == 0:
        h12 = 12
    suf = "a. m." if now.hour < 12 else "p. m."
    return f"{h12}:{now.minute:02d} {suf}"


def _respuesta_asistente_md_a_html_fragment(text: str) -> str:
    """Convierte Markdown del modelo a HTML para la burbuja del asistente (listas, negritas, títulos).

    Sin ``html=True`` en CommonMark: no se interpreta HTML crudo. Si ``markdown-it`` falla, se escapa como texto.
    """
    raw = (text or "").strip()
    if not raw:
        return ""
    try:
        from markdown_it import MarkdownIt

        md_it = MarkdownIt(
            "commonmark",
            {"options": {"html": False, "linkify": False, "breaks": True}},
        )
        out = md_it.render(raw).strip()
        out = re.sub(r'href\s*=\s*"\s*javascript:[^"]*"', 'href="#"', out, flags=re.I)
        out = re.sub(r"href\s*=\s*'\s*javascript:[^']*'", "href='#'", out, flags=re.I)
        return out
    except Exception:
        return html.escape(text).replace("\n", "<br/>")


def _html_qa_user_bubble(text: str) -> str:
    esc = html.escape(text)
    t = html.escape(_formato_hora_es())
    inner = (
        f'<div class="qa-chat-row qa-chat-row--user" role="group">'
        f'<div class="qa-chat-bubble qa-chat-bubble--user">'
        f"<p>{esc}</p>"
        f'<span class="qa-chat-time">{t}</span>'
        f"</div>"
        f'<div class="qa-chat-avatar qa-chat-avatar--user" aria-hidden="true">'
        f'<span class="material-symbols-outlined" style="color:#ffffff">person</span>'
        f"</div></div>"
    )
    return f'<div class="qa-chat-wrap">{inner}</div>'


def _html_qa_bot_bubble(text: str) -> str:
    body = _respuesta_asistente_md_a_html_fragment(text)
    t = html.escape(_formato_hora_es())
    logo_uri = _logotipo_card_data_uri()
    if logo_uri:
        av = (
            f'<div class="qa-chat-avatar qa-chat-avatar--bot" aria-hidden="true">'
            f'<img src="{html.escape(logo_uri, quote=True)}" alt="" />'
            f"</div>"
        )
    else:
        av = (
            '<div class="qa-chat-avatar qa-chat-avatar--bot" aria-hidden="true">'
            '<span class="material-symbols-outlined">wb_sunny</span></div>'
        )
    inner = (
        f'<div class="qa-chat-row qa-chat-row--bot" role="group">'
        f"{av}"
        f'<div class="qa-chat-bubble qa-chat-bubble--bot"><div class="qa-chat-bot-body qa-chat-bot-md">{body}</div>'
        f'<span class="qa-chat-time qa-chat-time--bot">{t}</span></div></div>'
    )
    return f'<div class="qa-chat-wrap">{inner}</div>'


def _html_qa_chat_transcript(hist: list[dict[str, str]]) -> str:
    """Un solo bloque HTML para que el scroll vertical sea fiable (st.html por mensaje rompe el layout)."""
    if not hist:
        inner = (
            '<p class="qa-empty-hint">'
            "Escribe tu pregunta abajo o elige uno de los temas sugeridos."
            "</p>"
        )
    else:
        parts: list[str] = []
        for msg in hist:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                parts.append(_html_qa_user_bubble(content))
            elif role == "assistant":
                parts.append(_html_qa_bot_bubble(content))
        inner = "".join(parts)
    return (
        '<div class="qa-chat-transcript-shell">'
        '<div class="qa-chat-scroll-viewport" role="log" aria-live="polite" aria-relevant="additions">'
        f"{inner}</div></div>"
    )


def _render_qa_quick_topics(*, input_key: str) -> None:
    """Tarjetas sugeridas: rellenan el campo de pregunta al pulsar."""
    st.markdown(
        '<p class="qa-quick-lead">También puedes preguntar sobre:</p>',
        unsafe_allow_html=True,
    )
    cols = st.columns(4, gap="medium")
    for i, (label, pregunta, icon) in enumerate(QA_QUICK_TOPICS):
        with cols[i]:
            if st.button(
                label,
                key=f"qa_quick_{i}",
                use_container_width=True,
                type="secondary",
                icon=icon,
            ):
                st.session_state[input_key] = pregunta
                st.rerun()


def _render_qa_ejemplos_column(*, input_key: str) -> None:
    """Columna izquierda Q&A: solo ejemplos rápidos (las 20 del Módulo 1 van fuera de la tarjeta, abajo)."""
    st.markdown(
        '<div class="qa-ejemplos-stack" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="qa-ejemplos-only-heading">Ejemplos de preguntas</p>',
        unsafe_allow_html=True,
    )
    for i, (pregunta, icon) in enumerate(QA_EJEMPLO_PREGUNTAS):
        if st.button(
            pregunta,
            key=f"qa_ejemplo_{i}",
            use_container_width=True,
            type="secondary",
            icon=icon,
        ):
            st.session_state[input_key] = pregunta
            st.rerun()


def _ejecutar_consulta(pregunta: str) -> None:
    if not (pregunta and pregunta.strip()):
        return
    hist = st.session_state.chat_historial.copy()
    st.session_state.chat_historial.append({"role": "user", "content": pregunta.strip()})
    with st.spinner("Consultando al asistente…"):
        out = responder(pregunta.strip(), hist)
    st.session_state.chat_historial.append({"role": "assistant", "content": out})
    st.rerun()


def _logotipo_card_data_uri() -> str | None:
    """Data-URI del logotipo para tarjetas de respuesta; fondo blanco → transparente."""
    global _LOGOTIPO_CARD_CACHE
    path = LOGOTIPO_CARD_IMAGE
    if not os.path.isfile(path):
        return None
    mtime = os.path.getmtime(path)
    if _LOGOTIPO_CARD_CACHE[0] == mtime:
        return _LOGOTIPO_CARD_CACHE[1]
    try:
        from PIL import Image
    except ImportError:
        with open(path, "rb") as f:
            b64 = base64.standard_b64encode(f.read()).decode("ascii")
        ext = os.path.splitext(path)[1].lower()
        mime = "image/png" if ext == ".png" else "image/jpeg"
        uri = f"data:{mime};base64,{b64}"
        _LOGOTIPO_CARD_CACHE = (mtime, uri)
        return uri
    im = Image.open(path).convert("RGBA")
    px = im.load()
    w, h = im.size
    thresh = 248
    for yy in range(h):
        for xx in range(w):
            r, g, b, a = px[xx, yy]
            if r >= thresh and g >= thresh and b >= thresh:
                px[xx, yy] = (255, 255, 255, 0)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    b64 = base64.standard_b64encode(buf.getvalue()).decode("ascii")
    uri = f"data:image/png;base64,{b64}"
    _LOGOTIPO_CARD_CACHE = (mtime, uri)
    return uri


def _render_card_respuesta(preg: str, resp: str, meta_prefix: str = "") -> None:
    """Tarjeta Q&A con logotipo, hora en el pie y Copiar (st.html en el DOM principal, sin iframe)."""
    hora = _formato_hora_es()
    pie_izq = f"{meta_prefix} · {hora}" if meta_prefix.strip() else hora
    pe = html.escape(preg)
    re_ = html.escape(resp).replace("\n", "<br/>")
    logo_uri = _logotipo_card_data_uri()
    logo_html = (
        f'<img src="{html.escape(logo_uri, quote=True)}" width="48" height="48" '
        f'style="object-fit:contain;flex-shrink:0;display:block;" alt="" />'
        if logo_uri
        else ""
    )
    copy_b64 = base64.standard_b64encode(f"{preg}\n\n{resp}".encode("utf-8")).decode(
        "ascii"
    )
    pie_esc = html.escape(pie_izq)
    rid = secrets.token_hex(4)
    bid = f"qa-copy-{rid}"
    frag = f"""<style>
#qa-rc-{rid} .qa-rc-wrap {{
  box-sizing:border-box;border:1px solid #c8e6c9;border-radius:12px;background:#ffffff;
  box-shadow:0 2px 12px rgba(27,94,32,0.08);padding:16px 18px;color:#263238;
  max-height:520px;overflow-y:auto;font-family:"Source Sans Pro",sans-serif;
}}
#qa-rc-{rid} .qa-rc-hdr {{ display:flex;align-items:flex-start;gap:12px;margin-bottom:14px; }}
#qa-rc-{rid} .qa-rc-q {{ margin:0;flex:1;font-weight:700;font-size:1rem;padding-top:2px;line-height:1.35;color:{C_GREEN}; }}
#qa-rc-{rid} .qa-rc-body {{ margin:0;font-size:0.95rem;line-height:1.55;color:#263238; }}
#qa-rc-{rid} .qa-rc-meta {{
  margin-top:14px;padding-top:12px;border-top:1px solid #e8f5e9;display:flex;
  justify-content:space-between;align-items:center;font-size:0.82rem;color:#546e7a;
}}
#qa-rc-{rid} .qa-rc-copy {{ background:none;border:none;color:#1565c0;font-weight:500;cursor:pointer;padding:0;font:inherit; }}
#qa-rc-{rid} .qa-rc-copy:hover {{ text-decoration:underline; }}
</style>
<div id="qa-rc-{rid}">
  <div class="qa-rc-wrap">
    <div class="qa-rc-hdr">{logo_html}<p class="qa-rc-q">{pe}</p></div>
    <p class="qa-rc-body">{re_}</p>
    <div class="qa-rc-meta">
      <span>{pie_esc}</span>
      <button type="button" class="qa-rc-copy" id="{bid}">Copiar</button>
    </div>
  </div>
</div>
<script>
(function() {{
  var b64 = {json.dumps(copy_b64)};
  var btn = document.getElementById({json.dumps(bid)});
  if (!btn) return;
  btn.onclick = function() {{
    var bin = atob(b64);
    var u8 = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
    var text = new TextDecoder("utf-8").decode(u8);
    navigator.clipboard.writeText(text).then(function() {{
      var p = btn.textContent;
      btn.textContent = "Copiado";
      setTimeout(function() {{ btn.textContent = p; }}, 1600);
    }}).catch(function() {{
      alert("No se pudo copiar. Prueba con otro navegador o permisos del portapapeles.");
    }});
  }};
}})();
</script>"""
    st.html(frag, unsafe_allow_javascript=True)


FAQ_CATEGORIAS: list[dict[str, object]] = [
    {
        "titulo": "¿Dónde están ubicadas las operaciones de Riopaila Castillo?",
        "relacionadas": [
            {
                "pregunta": "¿Dónde están ubicadas las operaciones de Riopaila Castillo?",
                "respuesta": (
                    "Nuestras operaciones principales están ubicadas en el Valle del Cauca, Colombia. "
                    "Contamos con plantaciones, producción de azúcar, cogeneración de energía y destilerías "
                    "en la región —por ejemplo en el municipio de Zarzal— además de extensas áreas de cultivo "
                    "de caña."
                ),
                "icono_respuesta": "location_on",
                "callout": {
                    "titulo": "Ubicaciones principales",
                    "items": [
                        "Zarzal, Valle del Cauca — Plantas de producción y oficinas principales",
                        "Valle del Cauca — Áreas de cultivo de caña",
                        "Colombia — Operaciones y distribución",
                    ],
                },
            },
            {
                "pregunta": "¿La compañía opera solo en el Valle del Cauca?",
                "respuesta": (
                    "El corazón operativo está en el Valle del Cauca, donde se concentra el cultivo de caña "
                    "y la mayor parte de la cadena agroindustrial. La presencia comercial y logística puede "
                    "articularse a nivel nacional según el negocio."
                ),
                "icono_respuesta": "map",
            },
            {
                "pregunta": "¿Cómo se articula la cadena de valor en la región?",
                "respuesta": (
                    "Desde el campo (siembra y suministro de caña) hasta las plantas industriales y la "
                    "generación energética, la cadena busca eficiencia, trazabilidad y relación con "
                    "proveedores y comunidades del territorio."
                ),
                "icono_respuesta": "account_tree",
            },
        ],
    },
    {
        "titulo": "¿Qué productos y servicios ofrece Riopaila Castillo?",
        "relacionadas": [
            {
                "pregunta": "¿Qué productos y servicios ofrece Riopaila Castillo?",
                "respuesta": (
                    "Ofrecemos soluciones ligadas al agroindustrial de la caña: azúcar y derivados, "
                    "generación de energía a partir de biomasa y bagazo, biocombustibles como el etanol, "
                    "y otros coproductos para distintas cadenas de valor."
                ),
                "icono_respuesta": "inventory_2",
            },
            {
                "pregunta": "¿Qué incluye la línea de azúcar y derivados?",
                "respuesta": (
                    "Incluye productos asociados al procesamiento de la caña — entre ellos azúcar para "
                    "diferentes usos industriales y de consumo, y derivados y coproductos según la "
                    "configuración productiva de cada unidad."
                ),
                "icono_respuesta": "nutrition",
            },
            {
                "pregunta": "¿Ofrecen soluciones energéticas o biocombustibles?",
                "respuesta": (
                    "Sí: formamos parte de esquemas de cogeneración con biomasa y de producción de etanol "
                    "y biocombustibles asociados al esquema caña–azúcar, alineados con políticas del sector."
                ),
                "icono_respuesta": "local_fire_department",
            },
        ],
    },
    {
        "titulo": "¿Riopaila Castillo produce energía?",
        "relacionadas": [
            {
                "pregunta": "¿Riopaila Castillo produce energía?",
                "respuesta": (
                    "Sí. Aprovechamos el bagazo y la biomasa asociada al proceso de la caña para generar "
                    "electricidad en esquemas de cogeneración, mejorando la eficiencia de las plantas y "
                    "aportando a la matriz cuando corresponde."
                ),
                "icono_respuesta": "bolt",
            },
            {
                "pregunta": "¿Qué es la cogeneración en este contexto?",
                "respuesta": (
                    "La cogeneración aprovecha el vapor y la energía del proceso industrial para generar "
                    "electricidad de forma integrada, reduciendo desperdicio energético respecto a procesos "
                    "desacoplados."
                ),
                "icono_respuesta": "electrical_services",
            },
            {
                "pregunta": "¿La energía generada sale a la red?",
                "respuesta": (
                    "Depende del esquema de cada instalación y de la regulación aplicable. En muchos casos "
                    "se prioriza autoconsumo industrial y excedentes pueden inyectarse según condiciones técnicas y contractuales."
                ),
                "icono_respuesta": "power",
            },
        ],
    },
    {
        "titulo": "¿Qué significa la sostenibilidad para Riopaila Castillo?",
        "relacionadas": [
            {
                "pregunta": "¿Qué significa la sostenibilidad para Riopaila Castillo?",
                "respuesta": (
                    "Integra buenas prácticas agrícolas, eficiencia en plantas, cuidado del agua y del suelo, "
                    "relación con comunidades y trazabilidad en la cadena de valor como eje transversal."
                ),
                "icono_respuesta": "eco",
            },
            {
                "pregunta": "¿Cómo se relaciona con el territorio y las comunidades?",
                "respuesta": (
                    "Mediante diálogo, programas de relacionamiento y enfoque en desarrollo local asociado "
                    "a operaciones responsables, sin sustituir la normativa ni los canales oficiales de cada caso."
                ),
                "icono_respuesta": "groups",
            },
            {
                "pregunta": "¿Hay enfoque en agua y suelo?",
                "respuesta": (
                    "Sí: el manejo agrícola y las mejoras en procesos industriales buscan reducir huella y "
                    "presión sobre recursos, en línea con prácticas del sector cañero moderno."
                ),
                "icono_respuesta": "water_drop",
            },
        ],
    },
    {
        "titulo": "¿Cómo puedo trabajar con Riopaila Castillo?",
        "relacionadas": [
            {
                "pregunta": "¿Cómo puedo trabajar con Riopaila Castillo?",
                "respuesta": (
                    "Las vacantes y convocatorias vigentes suelen publicarse en los canales oficiales. "
                    "Puedes empezar aquí:\n\n"
                    "- **Talento y cultura (sitio web):** [nuestra-gente](https://www.riopaila-castilla.com/nuestra-gente/)\n"
                    "- **Ofertas y novedades laborales (LinkedIn corporativo):** "
                    "[linkedin.com/company/riopaila-castilla-s.-a.](https://www.linkedin.com/company/riopaila-castilla-s.-a./)\n\n"
                    "En esos espacios encontrarás perfiles, requisitos y cómo postularte; evita intermediarios no verificados."
                ),
                "icono_respuesta": "work",
            },
            {
                "pregunta": "¿Hay opciones para proveedores o aliados?",
                "respuesta": (
                    "Las relaciones comerciales y de abastecimiento suelen gestionarse por áreas de compras "
                    "y cadena de suministro, según políticas y calendarios corporativos publicados o informados en canales oficiales."
                ),
                "icono_respuesta": "handshake",
            },
            {
                "pregunta": "¿Dónde veo ofertas laborales actualizadas?",
                "respuesta": (
                    "Consulta los canales oficiales donde la compañía comunica oportunidades:\n\n"
                    "- [LinkedIn — Riopaila Castilla](https://www.linkedin.com/company/riopaila-castilla-s.-a./) "
                    "(publicaciones de vacantes, p. ej. campañas tipo #ViernesdeVacantes)\n"
                    "- [Nuestra gente — sitio web](https://www.riopaila-castilla.com/nuestra-gente/) "
                    "(compromiso con talento y desarrollo)\n\n"
                    "Prioriza siempre estas fuentes verificadas frente a intermediarios no oficiales."
                ),
                "icono_respuesta": "badge",
            },
        ],
    },
    {
        "titulo": "¿Dónde puedo consultar informes y reportes de la empresa?",
        "relacionadas": [
            {
                "pregunta": "¿Dónde puedo consultar informes y reportes de la empresa?",
                "respuesta": (
                    "La información corporativa, noticias y materiales de sostenibilidad o relacionamiento "
                    "con inversionistas suelen publicarse en el sitio oficial y documentos de transparencia, "
                    "según el tipo de informe."
                ),
                "icono_respuesta": "description",
            },
            {
                "pregunta": "¿Hay reportes de sostenibilidad o ESG?",
                "respuesta": (
                    "Muchas compañías del sector publican memorias o informes de gestión ambiental y social; "
                    "consulta la sección correspondiente del sitio oficial para la versión más reciente disponible al público."
                ),
                "icono_respuesta": "verified",
            },
            {
                "pregunta": "¿Cómo diferenciar información oficial de rumores?",
                "respuesta": (
                    "Usa solo dominios y cuentas verificadas de Riopaila Castillo / Riopaila Castilla y "
                    "comunicados corporativos. Este asistente complementa con base en la documentación del proyecto."
                ),
                "icono_respuesta": "gavel",
            },
        ],
    },
]


_FAQ_ICON_EMOJI: dict[str, str] = {
    "location_on": "📍",
    "map": "🗺️",
    "account_tree": "🌳",
    "inventory_2": "📦",
    "nutrition": "🌾",
    "local_fire_department": "🔥",
    "bolt": "⚡",
    "electrical_services": "⚙️",
    "power": "🔌",
    "eco": "🌿",
    "groups": "👥",
    "water_drop": "💧",
    "work": "💼",
    "handshake": "🤝",
    "badge": "🎖️",
    "description": "📄",
    "verified": "✅",
    "gavel": "⚖️",
    "help": "❔",
}


def _faq_icon_a_emoji(icon_raw: str) -> str:
    key = (icon_raw or "help").strip().lower()
    return _FAQ_ICON_EMOJI.get(key, "📌")


def _faq_entrada_actual() -> dict[str, object]:
    """Devuelve el dict de pregunta/respuesta según categoría y subíndice guardados en sesión."""
    ci = int(st.session_state.get("faq_sel_cat", 0) or 0)
    ci = max(0, min(ci, len(FAQ_CATEGORIAS) - 1))
    cat = FAQ_CATEGORIAS[ci]
    rel_raw = cat.get("relacionadas")
    if not isinstance(rel_raw, list) or not rel_raw:
        return {"pregunta": "", "respuesta": ""}
    sj = int(st.session_state.get("faq_sel_sub", 0) or 0)
    sj = max(0, min(sj, len(rel_raw) - 1))
    ent = rel_raw[sj]
    return ent if isinstance(ent, dict) else {"pregunta": "", "respuesta": ""}


def _html_faq_tarjeta_respuesta(item: dict[str, object], texto_respuesta_md: str) -> str:
    """Tarjeta FAQ: icono, pregunta, meta y cuerpo de respuesta (Markdown→HTML) en un solo article."""
    pq = html.escape(str(item.get("pregunta") or ""))
    icon_vis = html.escape(_faq_icon_a_emoji(str(item.get("icono_respuesta") or "help")))
    body = _respuesta_asistente_md_a_html_fragment(texto_respuesta_md or "")
    if not body.strip():
        body = '<p class="faq-answer-body-empty">Sin contenido para mostrar.</p>'
    return (
        f'<article class="faq-answer-card faq-answer-card--consulta">'
        f'<div class="faq-answer-head">'
        f'<span class="faq-answer-ic faq-answer-ic-emoji" aria-hidden="true">{icon_vis}</span>'
        f'<h2 class="faq-answer-q">{pq}</h2></div>'
        f'<p class="faq-answer-meta">Respuesta generada desde la base consolidada (búsqueda léxica + Groq).</p>'
        f'<div class="faq-answer-body faq-answer-body-md">{body}</div>'
        f"</article>"
    )


LINEAS_NEGOCIO_FILA: list[tuple[str, str, str]] = [
    ("azucar", "Azúcar", "experiment"),
    ("energia", "Energía renovable", "bolt"),
    ("biocombustibles", "Biocombustibles", "local_gas_station"),
    ("derivados", "Derivados", "schema"),
]

LINEAS_NEGOCIO_KEYS: frozenset[str] = frozenset(k for k, _, _ in LINEAS_NEGOCIO_FILA)


def _label_linea_negocio(key: str) -> str:
    for k, lbl, _ in LINEAS_NEGOCIO_FILA:
        if k == key:
            return lbl
    return key


def _html_resumen_main_columns(ai_fragment: str, proposito_html: str) -> str:
    """Dos columnas: izquierda y derecha con texto generado vía consulta (HTML ya convertido desde Markdown)."""
    href_faq = "?nav=" + quote("FAQ")
    href_esc = html.escape(href_faq, quote=True)
    frag = ai_fragment.strip() if ai_fragment else ""
    if not frag:
        frag = (
            '<p class="resumen-block-text" style="padding-left:44px;margin:0;">'
            "Sin contenido para mostrar. Pulsa <strong>Regenerar resumen</strong>.</p>"
        )
    prop = proposito_html.strip() if proposito_html else ""
    if not prop:
        prop = '<p class="resumen-purpose-fallback">Consultando propósito desde la base…</p>'
    left = (
        '<div class="resumen-wrap">'
        '<div class="resumen-columns">'
        '<div class="resumen-col resumen-col-left">'
        '<div class="resumen-card">'
        '<div class="resumen-block resumen-block--executive">'
        '<div class="resumen-block-head">'
        '<span class="resumen-ic-emoji" aria-hidden="true">📋</span>'
        '<h3 class="resumen-block-title">Resumen ejecutivo</h3>'
        "</div>"
        '<div class="resumen-ai-body resumen-ai-md">'
    )
    mid = (
        "</div></div></div></div>"
        '<div class="resumen-col resumen-col-right">'
        '<div class="resumen-card resumen-card--right">'
        '<div class="resumen-purpose-stack">'
        '<div class="resumen-block resumen-block--purpose">'
        '<div class="resumen-block-head">'
        '<span class="resumen-ic-emoji" aria-hidden="true">🎯</span>'
        '<h3 class="resumen-block-title">Nuestro prop&oacute;sito</h3>'
        "</div>"
        '<div class="resumen-purpose-md resumen-ai-md">'
    )
    prop_close = "</div></div>"
    right = (
        '<div class="resumen-stats-wrap">'
        '<div class="resumen-stats" role="group" aria-label="Destacados">'
        '<div class="resumen-stat-cell">'
        '<span class="resumen-stat-val">+100</span>'
        '<span class="resumen-stat-lbl">a&ntilde;os de historia</span>'
        "</div>"
        '<div class="resumen-stat-cell">'
        '<span class="resumen-stat-val">Valle del Cauca</span>'
        '<span class="resumen-stat-lbl">Nuestra casa</span>'
        "</div>"
        '<div class="resumen-stat-cell">'
        '<span class="resumen-stat-val">Sostenibilidad</span>'
        '<span class="resumen-stat-lbl">En el centro de todo</span>'
        "</div>"
        '<div class="resumen-stat-cell">'
        '<span class="resumen-stat-val">Innovaci&oacute;n</span>'
        '<span class="resumen-stat-lbl">Para un mejor futuro</span>'
        "</div>"
        "</div>"
        f'<a class="resumen-fab" href="{href_esc}" target="_self" aria-label="Ir a preguntas frecuentes">'
        '<span class="resumen-fab-icon" aria-hidden="true">&rarr;</span>'
        "</a>"
        "</div></div></div></div></div></div>"
    )
    return left + frag + mid + prop + prop_close + right


def _html_resumen_pie_consulta(inner_html: str) -> str:
    """Pie verde con contenido proveniente de consulta Q&A (HTML interno)."""
    body = inner_html.strip() if inner_html else ""
    if not body:
        body = '<p class="resumen-foot-fallback">Sin mensaje de cierre. Pulsa <strong>Regenerar resumen</strong>.</p>'
    return (
        '<div class="resumen-wrap">'
        '<div class="resumen-footbar">'
        '<span class="resumen-foot-emoji" aria-hidden="true">✎</span>'
        f'<div class="resumen-foot-md resumen-ai-md">{body}</div>'
        "</div></div>"
    )


def _render_resumen_lineas_negocio() -> None:
    """Cuatro líneas con botones; la respuesta sale de invocar_linea_negocio (misma cadena Q&A que el chat)."""
    st.markdown(
        '<div class="resumen-wrap">'
        '<div class="resumen-lineas-heading">'
        '<span class="material-symbols-outlined resumen-ic" aria-hidden="true">energy_savings_leaf</span>'
        '<h3 class="resumen-lineas-h">Nuestras líneas de negocio</h3></div></div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(4, gap="medium")
    for col, (key, label, icon) in zip(cols, LINEAS_NEGOCIO_FILA, strict=True):
        with col:
            st.markdown(
                f'<div class="resumen-wrap"><div class="resumen-biz-click"><span class="material-symbols-outlined" '
                f'aria-hidden="true">{html.escape(icon)}</span></div></div>',
                unsafe_allow_html=True,
            )
            if st.button(
                label,
                key=f"res_linea_{key}",
                use_container_width=True,
                type="secondary",
            ):
                st.session_state.resumen_linea = key

    sel = st.session_state.get("resumen_linea")
    if isinstance(sel, str) and sel in LINEAS_NEGOCIO_KEYS:
        prev = st.session_state.get("_resumen_linea_track")
        if prev != sel:
            st.session_state["_resumen_linea_track"] = sel
            st.session_state.pop("_resumen_linea_md", None)
        if st.session_state.get("_resumen_linea_md") is None:
            _configurar_groq_api_key()
            with st.spinner(f"Consultando la base sobre «{_label_linea_negocio(sel)}»…"):
                st.session_state["_resumen_linea_md"] = invocar_linea_negocio(sel)
        inner = _respuesta_asistente_md_a_html_fragment(st.session_state["_resumen_linea_md"] or "")
        tit = html.escape(_label_linea_negocio(sel))
        st.markdown(
            f'<div class="resumen-wrap"><div class="resumen-productos-box resumen-linea-consulta">'
            f"<h4>Información desde la base — {tit}</h4>"
            f'<div class="resumen-linea-md resumen-ai-md">{inner}</div></div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.caption("Pulsa una línea de negocio para lanzar una consulta guiada al consolidado.")


def _init_state() -> None:
    if "pagina" not in st.session_state:
        st.session_state.pagina = "Inicio"
    if st.session_state.pagina not in PAGINAS_VALIDAS:
        st.session_state.pagina = "Inicio"
    if "chat_historial" not in st.session_state:
        st.session_state.chat_historial = []
    if "resumen_linea" not in st.session_state:
        st.session_state.resumen_linea = None
    if "faq_sel_cat" not in st.session_state:
        st.session_state.faq_sel_cat = 0
    if "faq_sel_sub" not in st.session_state:
        st.session_state.faq_sel_sub = 0
    if "faq_cat_open" not in st.session_state:
        st.session_state.faq_cat_open = 0

def _sync_nav_from_query() -> None:
    """Navegación por enlaces ?nav= en el menú HTML lateral."""
    if not hasattr(st, "query_params"):
        return
    if "nav" not in st.query_params:
        return
    raw = st.query_params["nav"]
    if isinstance(raw, list):
        raw = raw[0]
    decoded = unquote(str(raw))
    if decoded in PAGINAS_VALIDAS:
        st.session_state.pagina = decoded
    try:
        del st.query_params["nav"]
    except Exception:
        pass


def _ir_a(pagina: str) -> None:
    st.session_state.pagina = pagina
    st.rerun()


def _sidebar_panel_modulo1() -> None:
    """Estado de la base consolidada + chunking."""
    with st.sidebar.expander("Módulo 1 — Base de conocimiento", expanded=False):
        stats = estadisticas_base()

        if not stats.get("existe"):
            st.info(
                "Coloca el archivo consolidado en `reportes/tu_archivo_riopaila.txt` "
                "(esa es la única fuente que usa Resumen, FAQ y Q&A)."
            )
            return

        st.success("Base de conocimiento cargada")

        marcadas = stats.get("fuentes_en_consolidado") or []
        if marcadas:
            st.caption("**Bloques `FUENTE:` en el consolidado:**")
            st.caption(", ".join(f"`{x}`" for x in marcadas))

        st.metric("Caracteres en archivo", f"{int(stats['chars_archivo']):,}")
        st.metric("Chunks (`RecursiveCharacterTextSplitter`)", f"{int(stats['num_chunks']):,}")
        st.metric("Contexto — Resumen (inicio del texto)", f"{int(stats['chars_contexto_prompt']):,}")
        ce = stats.get("chars_contexto_consulta_ejemplo")
        if ce is not None:
            st.metric("Contexto — FAQ/Q&A (ej. multi‑tema)", f"{int(ce):,}")
        st.caption(
            f"Máximo por solicitud: {int(stats['max_context_config']):,} caracteres (`KB_MAX_CONTEXT_CHARS`). "
            "FAQ y Q&A **eligen fragmentos** por palabras de la pregunta (búsqueda léxica); sin embeddings ni RAG."
        )
        if st.button("Exportar muestra de chunks", key="m1_export_chunks", type="secondary"):
            try:
                path = exportar_muestra_chunks()
                st.info(f"Archivo generado:\n`{path}`")
            except Exception as ex:
                st.error(str(ex))
        st.caption(
            "**Resumen**, **FAQ** (expander LangChain) y **Q&A** orquestan prompts con LangChain + Groq."
        )


def _apply_qa_m1_prefill_if_any(*, input_key: str) -> None:
    """Consume la cola del bloque Módulo 1 (solo antes de crear el widget `input_key`)."""
    if _QA_M1_PREFILL_KEY not in st.session_state:
        return
    st.session_state[input_key] = st.session_state.pop(_QA_M1_PREFILL_KEY)


def _render_modulo1_veinte_pruebas_below_card() -> None:
    """20 preguntas Módulo 1 debajo de la tarjeta Q&A (sin restricción de altura del layout de dos columnas)."""
    with st.container(key="qa_m1_below_card"):
        with st.expander(
            "20 preguntas · pruebas informe (Módulo 1)",
            expanded=False,
        ):
            st.caption(
                "Pulsa una fila: se cargará en **Tu pregunta** (recuadro en la tarjeta de arriba). Luego **Enviar**. "
                "Usa la lista para documentar el informe."
            )
            for i, pregunta in enumerate(MODULO1_PREGUNTAS_PRUEBA):
                etiqueta = f"{i + 1}. {pregunta}"
                if st.button(
                    etiqueta,
                    key=f"m1_prueba_{i}",
                    use_container_width=True,
                    help=f"Cargar en el campo de pregunta: {pregunta}",
                    type="secondary",
                ):
                    st.session_state[_QA_M1_PREFILL_KEY] = pregunta
                    st.rerun()


def _sidebar() -> None:
    """Menú lateral: botones Streamlit (misma ventana; sin recarga tipo enlace <a>)."""
    if os.path.isfile(LOGO_IMAGE):
        st.sidebar.image(LOGO_IMAGE, use_container_width=True)
    else:
        st.sidebar.caption("Coloca el logotipo en `assets/logo_riopaila.png`.")
    st.sidebar.divider()
    st.sidebar.markdown(
        f"""
        <p style="font-size:0.85rem;line-height:1.5;color:{C_TEXT_MUTED};margin:0 0 18px 0;">
        Somos una empresa colombiana con más de 100 años de historia, dedicada al cultivo de
        caña de azúcar y la producción de azúcar, energías renovables, biocombustibles y derivados.
        </p>
        """,
        unsafe_allow_html=True,
    )

    pagina_actual = st.session_state.pagina
    try:
        active_idx = next(i for i, (_, pid, _) in enumerate(MENU_NAV) if pid == pagina_actual)
    except StopIteration:
        active_idx = 0
    # Índice 1-based del primer bloque del menú dentro del VB principal del sidebar:
    # imagen o caption (1), divisor (2), texto intro (3), luego botones (4…).
    _SIDEBAR_NAV_EC_CHILD = 4
    nav_sel = (
        f'[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > '
        f'div[data-testid="stElementContainer"]:nth-child({_SIDEBAR_NAV_EC_CHILD + active_idx}) '
        f".stButton button"
    )

    for idx, (etiqueta, pid, ikey) in enumerate(MENU_NAV):
        ic = NAV_MATERIAL_ICON.get(ikey, "")
        label = f"{ic} {etiqueta}" if ic else etiqueta
        if st.sidebar.button(
            label,
            key=f"sidebar_nav_{idx}",
            use_container_width=True,
            type="tertiary",
        ):
            _ir_a(pid)

    st.sidebar.markdown(
        f"""<style>
            {nav_sel}, {nav_sel} * {{
                color: #ffffff !important;
            }}
            {nav_sel} {{
                background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%) !important;
                border: 1px solid rgba(255, 255, 255, 0.15) !important;
                box-shadow: 0 4px 16px rgba(27, 94, 32, 0.28) !important;
            }}
            {nav_sel}:hover {{
                background: linear-gradient(135deg, #2e7d32 0%, #388e3c 100%) !important;
                border-color: rgba(255, 255, 255, 0.22) !important;
                color: #ffffff !important;
                box-shadow: 0 4px 18px rgba(27, 94, 32, 0.32) !important;
            }}
            {nav_sel}:hover *, {nav_sel}:hover span {{
                color: #ffffff !important;
            }}
            </style>""",
        unsafe_allow_html=True,
    )

    _sidebar_panel_modulo1()

    st.sidebar.markdown(
        f"""
        <div style="margin-top:20px;padding:14px;border-radius:14px;background:{C_GREEN_SOFT};
        border:1px solid #c8e6c9;font-size:0.82rem;line-height:1.45;color:{C_GREEN};">
            <div style="display:flex;align-items:flex-start;gap:10px;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="{C_GREEN}"
                  stroke-width="1.5" stroke-linecap="round" style="flex-shrink:0;margin-top:2px;" aria-hidden="true">
                  <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
                  <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
                </svg>
                <span>Transformamos la caña de azúcar en bienestar para el país.</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _html_footer_redes() -> str:
    """Iconos SVG + enlaces oficiales (constantes SOCIAL_*)."""
    _svg_in = (
        "<svg class='footer-social-svg' viewBox='0 0 24 24' aria-hidden='true'>"
        "<path fill='currentColor' d='M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 "
        "0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 "
        "2.37 4.267 5.455v6.286zM5.337 7.433a2.07 2.07 0 1 1 0 4.139 2.07 2.07 0 0 1 0-4.139zm1.782 13.019H3.555V9h3.564v11.452zM22.225 "
        "0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 "
        "23.2 0 22.222 0h.003z'/></svg>"
    )
    _svg_ig = (
        "<svg class='footer-social-svg' viewBox='0 0 24 24' aria-hidden='true'>"
        "<path fill='currentColor' d='M12 2.2c3.2 0 3.6 0 4.9.07 2.4.12 3.8 1.35 4 4 .05 1.3.07 1.7.07 4.9s0 3.6-.07 "
        "4.9c-.12 2.4-1.35 3.8-4 4-1.3.05-1.7.07-4.9.07s-3.6 0-4.9-.07c-2.4-.12-3.8-1.35-4-4C2.25 15.6 2.2 15.2 2.2 "
        "12s0-3.6.08-4.9c.12-2.4 1.35-3.8 4-4C8.4 2.25 8.8 2.2 12 2.2zm0-2.2C8.7 0 8.3 0 7 .07 2.7.27.3 2.7.07 7 0 8.3 0 "
        "8.7 0 12c0 3.3 0 3.7.07 5 .2 4.4 2.6 6.8 6.98 7C15.6 24.07 16 24 19.3 24c3.3 0 3.7 0 5-.07 4.35-.2 6.78-2.6 "
        "6.98-7 .07-1.3.07-1.7.07-5 0-3.3 0-3.7-.07-5-.2-4.35-2.6-6.78-6.98-7-1.28-.07-1.64-.07-5-.07zm0 5.8a6.2 6.2 0 "
        "1 0 0 12.4 6.2 6.2 0 0 0 0-12.4zm0 10.2a4 4 0 1 1 0-8 4 4 0 0 1 0 8zm6.4-11.8a1.44 1.44 0 1 0 0 2.88 1.44 1.44 "
        "0 0 0 0-2.88z'/></svg>"
    )
    _svg_yt = (
        "<svg class='footer-social-svg' viewBox='0 0 24 24' aria-hidden='true'>"
        "<path fill='currentColor' d='M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.4.6A3 3 0 0 0 .5 "
        "6.2C0 8.1 0 12 0 12s0 3.9.5 5.8a3 3 0 0 0 2.1 2.1c1.9.5 9.4.5 9.4.5s7.5 0 9.4-.5a3 3 0 0 0 2.1-2.1c.5-1.9.5-5.8 "
        ".5-5.8s0-3.9-.5-5.8zM9.5 15.6V8.4L16 12l-6.5 3.6z'/></svg>"
    )
    _svg_fb = (
        "<svg class='footer-social-svg' viewBox='0 0 24 24' aria-hidden='true'>"
        "<path fill='currentColor' d='M24 12.1C24 5.4 18.6 0 12 0S0 5.4 0 12.1c0 6 4.4 11 10.1 11.9v-8.4H7.1V12h3V9.4c0-3 "
        "1.8-4.7 4.5-4.7 1.3 0 2.7.2 2.7.2v3h-1.5c-1.5 0-2 1-2 1.8V12h3.4l-.5 3.5h-2.9v8.4C19.6 23.1 24 18.1 24 12.1z'/>"
        "</svg>"
    )
    li = html.escape(SOCIAL_LINKEDIN, quote=True)
    ig = html.escape(SOCIAL_INSTAGRAM, quote=True)
    yt = html.escape(SOCIAL_YOUTUBE, quote=True)
    fb = html.escape(SOCIAL_FACEBOOK, quote=True)
    return (
        f'<nav class="footer-social" aria-label="Redes sociales de Riopaila Castillo">'
        f'<a class="footer-social-link footer-social-link--in" href="{li}" target="_blank" '
        f'rel="noopener noreferrer" title="LinkedIn" aria-label="Riopaila Castillo en LinkedIn">{_svg_in}</a>'
        f'<a class="footer-social-link footer-social-link--ig" href="{ig}" target="_blank" '
        f'rel="noopener noreferrer" title="Instagram" aria-label="Riopaila Castillo en Instagram">{_svg_ig}</a>'
        f'<a class="footer-social-link footer-social-link--yt" href="{yt}" target="_blank" '
        f'rel="noopener noreferrer" title="YouTube" aria-label="Riopaila Castillo en YouTube">{_svg_yt}</a>'
        f'<a class="footer-social-link footer-social-link--fb" href="{fb}" target="_blank" '
        f'rel="noopener noreferrer" title="Facebook" aria-label="Riopaila Castillo en Facebook">{_svg_fb}</a>'
        f"</nav>"
    )


def _pie() -> None:
    y = datetime.now().year
    st.markdown(
        f'<footer class="app-footer-wrap" role="contentinfo">'
        f'<div class="app-footer-inner">'
        f'<p class="app-footer-copy">'
        f"© {y} Riopaila Castillo. Todos los derechos reservados."
        f"</p>"
        f"{_html_footer_redes()}"
        f"</div></footer>",
        unsafe_allow_html=True,
    )


def _explora_funcionalidades_html() -> str:
    """Una sola tarjeta blanca con grid 4 columnas; botones enlace ?nav= (misma altura)."""
    F = _FEAT
    q_res, q_faq, q_qa, q_agent = (
        quote("Resumen"), quote("FAQ"), quote("Q&A"), quote("Agente"),
    )
    return f"""
<div class="feat-shell">
    <h3 class="feat-shell-title">Explora nuestras funcionalidades</h3>
    <div class="feat-grid">
        <div class="feat-col">
            <div class="card feat-card feat-card-triple">
                <div class="feat-head feat-head-green">
                    <div class="feat-head-inner">
                        {F["icon_doc"]}
                        <div>
                            <p class="feat-head-title">Resumen</p>
                            <p class="feat-head-sub">Obtén un resumen de Riopaila Castillo.</p>
                        </div>
                    </div>
                </div>
                <div class="feat-body-white feat-body-grow">
                    <div class="feat-illo feat-illo-fixed">{F["illo_resumen"]}</div>
                    <p class="feat-desc">Conoce en pocos párrafos quiénes somos, qué hacemos y nuestro propósito.</p>
                </div>
                <div class="feat-card-footer">
                    <a class="feat-btn feat-btn--green" href="?nav={q_res}" target="_self">Ver Resumen →</a>
                </div>
            </div>
        </div>
        <div class="feat-col">
            <div class="card feat-card feat-card-triple">
                <div class="feat-head feat-head-blue">
                    <div class="feat-head-inner">
                        {F["icon_faq"]}
                        <div>
                            <p class="feat-head-title">FAQ</p>
                            <p class="feat-head-sub">Consulta las preguntas frecuentes.</p>
                        </div>
                    </div>
                </div>
                <div class="feat-body-white feat-body-grow">
                    <div class="feat-illo feat-illo-fixed">{F["illo_faq"]}</div>
                    <p class="feat-desc">Encuentra respuestas rápidas a las preguntas más comunes sobre nuestra empresa.</p>
                </div>
                <div class="feat-card-footer">
                    <a class="feat-btn feat-btn--blue" href="?nav={q_faq}" target="_self">Ver FAQ →</a>
                </div>
            </div>
        </div>
        <div class="feat-col">
            <div class="card feat-card feat-card-triple">
                <div class="feat-head feat-head-yellow">
                    <div class="feat-head-inner">
                        {F["icon_qa"]}
                        <div>
                            <p class="feat-head-title">Q&amp;A</p>
                            <p class="feat-head-sub">Haz tu pregunta y recibe una respuesta.</p>
                        </div>
                    </div>
                </div>
                <div class="feat-body-white feat-body-grow">
                    <div class="feat-illo feat-illo-fixed">{F["illo_qa"]}</div>
                    <p class="feat-desc">Escribe tu pregunta sobre Riopaila Castillo y nuestro asistente te responderá.</p>
                </div>
                <div class="feat-card-footer">
                    <a class="feat-btn feat-btn--yellow" href="?nav={q_qa}" target="_self">Ir a Q&amp;A →</a>
                </div>
            </div>
        </div>
        <div class="feat-col">
            <div class="card feat-card feat-card-triple">
                <div class="feat-head feat-head-agent">
                    <div class="feat-head-inner">
                        {F["icon_agent"]}
                        <div>
                            <p class="feat-head-title">Agente</p>
                            <p class="feat-head-sub">Asistente con RAG + memoria.</p>
                        </div>
                    </div>
                </div>
                <div class="feat-body-white feat-body-grow">
                    <div class="feat-illo feat-illo-fixed">{F["illo_agent"]}</div>
                    <p class="feat-desc">Conversa con un asistente que consulta documentos oficiales, datos verificados y recuerda el contexto.</p>
                </div>
                <div class="feat-card-footer">
                    <a class="feat-btn feat-btn--agent" href="?nav={q_agent}" target="_self">Ir al Agente →</a>
                </div>
            </div>
        </div>
    </div>
</div>
"""


def pagina_inicio() -> None:
    with st.container():
        _render_hero_unificado(_collect_hero_images())

    with st.container():
        st.markdown(_explora_funcionalidades_html(), unsafe_allow_html=True)

    with st.container():
        st.markdown(
            "<div class='qa-bloque-inicio-spacer' aria-hidden='true'></div>",
            unsafe_allow_html=True,
        )
        col_in, col_out = st.columns([1, 1])

        with col_in:
            _render_qa_composer(
                input_key="inicio_q_input",
                button_key="inicio_q_enviar",
                input_form_label="Pregunta",
            )

        with col_out:
            par = _ultimo_par_qa()
            if par:
                pq, pa = par
                _render_card_respuesta(pq, pa)
                st.download_button(
                    label="📋 Descargar respuesta (txt)",
                    data=f"{pq}\n\n{pa}",
                    file_name="respuesta_riopaila.txt",
                    mime="text/plain",
                    key="dl_home_resp",
                    use_container_width=True,
                )
            else:
                _render_card_respuesta(PLACEHOLDER_Q, PLACEHOLDER_A)

    _pie()


def pagina_resumen() -> None:
    st.markdown(
        '<div id="resumen-page-mount" class="resumen-page-mount" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )
    # Fix de contraste para botones secundarios dentro de la página Resumen
    # (Regenerar resumen + botones de líneas de negocio): texto blanco sobre
    # fondo verde institucional, en vez del oscuro-sobre-oscuro por defecto.
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"]:has(#resumen-page-mount) .stButton > button[kind="secondary"] {{
            background: linear-gradient(135deg, {C_GREEN} 0%, #2e7d32 100%) !important;
            color: #ffffff !important;
            border: 1px solid rgba(255,255,255,0.15) !important;
            box-shadow: 0 3px 12px rgba(27, 94, 32, 0.22) !important;
            font-weight: 600 !important;
        }}
        [data-testid="stAppViewContainer"]:has(#resumen-page-mount) .stButton > button[kind="secondary"] p,
        [data-testid="stAppViewContainer"]:has(#resumen-page-mount) .stButton > button[kind="secondary"] span,
        [data-testid="stAppViewContainer"]:has(#resumen-page-mount) .stButton > button[kind="secondary"] * {{
            color: #ffffff !important;
        }}
        [data-testid="stAppViewContainer"]:has(#resumen-page-mount) .stButton > button[kind="secondary"]:hover {{
            background: linear-gradient(135deg, #2e7d32 0%, #388e3c 100%) !important;
            border-color: rgba(255,255,255,0.25) !important;
            box-shadow: 0 4px 16px rgba(27, 94, 32, 0.32) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.container():
        _render_hero_unificado(
            _collect_hero_images(),
            hero_layout="faq_banner",
            show_cap=False,
            title_txt="Resumen de Riopaila Castillo",
            sub=(
                "Toda la página usa consultas al consolidado (recuperación léxica + LangChain + Groq): "
                "resumen, propósito, mensaje de cierre y líneas de negocio."
            ),
            title_color=C_GREEN,
            show_title_emoji=False,
        )

    bar_txt, bar_btn = st.columns([3.15, 1], gap="medium")
    with bar_txt:
        st.caption(
            "Cada bloque de texto llama al modelo con fragmentos del consolidado (sin embeddings). "
            "**Regenerar** actualiza resumen, propósito, pie y limpia la última consulta de línea."
        )
    with bar_btn:
        regen = st.button(
            "Regenerar resumen",
            key="btn_resumen_llm",
            type="secondary",
            use_container_width=True,
        )

    necesita = st.session_state.get("_resumen_llm_md") is None
    if necesita or regen:
        _configurar_groq_api_key()
        with st.spinner("Generando resumen desde la base…"):
            st.session_state["_resumen_llm_md"] = invocar_resumen()
        st.session_state.pop("_resumen_proposito_md", None)
        st.session_state.pop("_resumen_pie_md", None)
        st.session_state.pop("_resumen_linea_md", None)
        st.session_state.pop("_resumen_linea_track", None)

    md_res = st.session_state.get("_resumen_llm_md")
    exec_frag = _respuesta_asistente_md_a_html_fragment(md_res or "")

    if st.session_state.get("_resumen_proposito_md") is None:
        _configurar_groq_api_key()
        with st.spinner("Consultando «Nuestro propósito» en la base…"):
            st.session_state["_resumen_proposito_md"] = invocar_proposito_tarjeta_resumen()
    prop_frag = _respuesta_asistente_md_a_html_fragment(st.session_state["_resumen_proposito_md"] or "")

    st.html(_html_resumen_main_columns(exec_frag, prop_frag))

    _render_resumen_lineas_negocio()

    if st.session_state.get("_resumen_pie_md") is None:
        _configurar_groq_api_key()
        with st.spinner("Generando mensaje de cierre desde la base…"):
            st.session_state["_resumen_pie_md"] = invocar_mensaje_cierre_resumen()
    pie_frag = _respuesta_asistente_md_a_html_fragment(st.session_state["_resumen_pie_md"] or "")
    st.html(_html_resumen_pie_consulta(pie_frag))
    _pie()


def pagina_faq() -> None:
    st.markdown(
        '<div id="faq-page-mount" class="faq-page-mount" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )
    with st.container():
        _render_hero_unificado(
            _collect_hero_images(),
            hero_layout="faq_banner",
            show_cap=False,
            title_txt="FAQ — Preguntas frecuentes",
            sub=(
                "Cada respuesta se obtiene al elegir la pregunta: misma base consolidada "
                "y modelo que en Q&A."
            ),
            title_color=C_FAQ_PRIMARY,
            show_title_emoji=False,
        )

    c_side, c_ans = st.columns([1, 2.15], gap="large")
    with c_side:
        st.markdown(
            '<p class="faq-sidebar-eyebrow">Temas</p>',
            unsafe_allow_html=True,
        )
        sel_cat = int(st.session_state.get("faq_sel_cat", 0) or 0)
        sel_cat = max(0, min(sel_cat, len(FAQ_CATEGORIAS) - 1))
        for ci, cat in enumerate(FAQ_CATEGORIAS):
            tit = str(cat.get("titulo", ""))
            if st.button(
                tit,
                key=f"faq_cat_{ci}",
                use_container_width=True,
                type="primary" if ci == sel_cat else "secondary",
            ):
                open_i = st.session_state.faq_cat_open
                if open_i is not None and int(open_i) == ci:
                    st.session_state.faq_cat_open = None
                else:
                    st.session_state.faq_cat_open = ci
                    st.session_state.faq_sel_cat = ci
                    st.session_state.faq_sel_sub = 0

            open_i = st.session_state.faq_cat_open
            if open_i is not None and int(open_i) == ci:
                rel_raw = cat.get("relacionadas")
                if isinstance(rel_raw, list):
                    for sj, sub in enumerate(rel_raw):
                        if not isinstance(sub, dict):
                            continue
                        sub_lbl = str(sub.get("pregunta", ""))
                        sub_on = sel_cat == ci and int(
                            st.session_state.get("faq_sel_sub", 0) or 0
                        ) == sj
                        if st.button(
                            sub_lbl,
                            key=f"faq_sub_{ci}_{sj}",
                            use_container_width=True,
                            type="primary" if sub_on else "tertiary",
                        ):
                            st.session_state.faq_cat_open = ci
                            st.session_state.faq_sel_cat = ci
                            st.session_state.faq_sel_sub = sj

    with c_ans:
        ent_faq = _faq_entrada_actual()
        pq_ia = str(ent_faq.get("pregunta") or "").strip()
        if not pq_ia:
            st.caption("Selecciona una pregunta en la lista de temas.")
        else:
            prev_p = st.session_state.get("_faq_respuesta_pregunta")
            if prev_p != pq_ia:
                st.session_state["_faq_respuesta_pregunta"] = pq_ia
                st.session_state.pop("_faq_respuesta_ia", None)
            if st.session_state.get("_faq_respuesta_ia") is None:
                _configurar_groq_api_key()
                guia = str(ent_faq.get("respuesta") or "").strip()
                with st.spinner("Consultando la base de conocimiento…"):
                    st.session_state["_faq_respuesta_ia"] = invocar_faq(
                        pq_ia,
                        respuesta_estatica=guia or None,
                    )
            md_faq = st.session_state.get("_faq_respuesta_ia") or ""
            st.html(_html_faq_tarjeta_respuesta(ent_faq, md_faq))
    st.caption("¿Necesitas más detalle? Usa la sección **Q&A** del menú.")
    _pie()


def pagina_qa() -> None:
    st.markdown(
        '<div id="qa-page-mount" class="qa-page-mount" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )
    if st.session_state.pop("_qa_pending_chat_clear", False):
        st.session_state.chat_historial = []
        st.session_state.qa_pregunta = ""
    _apply_qa_m1_prefill_if_any(input_key="qa_pregunta")
    with st.container():
        _render_hero_unificado(
            _collect_hero_images(),
            hero_layout="faq_banner",
            show_cap=False,
            title_txt="Q&A — Preguntas y respuestas",
            sub="Tu fuente de información sobre nuestra empresa.",
            title_color=C_GREEN,
            show_title_emoji=False,
        )

    st.markdown(
        '<div class="qa-after-hero-spacer" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )

    with st.container(border=False, key="qa_unified_card", gap=None):
        st.markdown(
            '<div class="qa-unified-card-root" aria-hidden="true"></div>',
            unsafe_allow_html=True,
        )
        _render_qa_header_bar()
        with st.container(border=False, key="qa_chat_inset", gap="medium"):
            st.markdown(
                '<div class="qa-chat-gray-root" aria-hidden="true"></div>',
                unsafe_allow_html=True,
            )
            rail_col, chat_col = st.columns([1, 2.05], gap="medium")
            with rail_col:
                _render_qa_ejemplos_column(input_key="qa_pregunta")
            with chat_col:
                st.markdown(
                    '<div class="qa-chat-stream-root" aria-hidden="true"></div>',
                    unsafe_allow_html=True,
                )
                qa_col = st.columns([1])[0]
                with qa_col:
                    hist = st.session_state.chat_historial
                    st.markdown(
                        _html_qa_chat_transcript(hist),
                        unsafe_allow_html=True,
                    )

                    _render_qa_quick_topics(input_key="qa_pregunta")

                    _render_qa_composer(
                        input_key="qa_pregunta",
                        button_key="qa_enviar",
                        input_form_label="Tu pregunta",
                        show_composer_head=False,
                        show_composer_foot=False,
                    )

                    if st.button("Limpiar conversación", key="qa_limpiar", type="secondary"):
                        st.session_state["_qa_pending_chat_clear"] = True
                        st.rerun()

    st.markdown(
        '<div class="qa-m1-below-spacer" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )
    _render_modulo1_veinte_pruebas_below_card()
    _pie()


# ============================================================================
# Página Agente (Módulo 2) — chat con RAG + tools estructuradas + memoria
# Calcado visualmente de la página Q&A; el motor interno es el agente ReAct.
# ============================================================================

_TOOL_LABELS = {
    "rag_search": "Búsqueda semántica (RAG vectorial sobre Supabase pgvector)",
    "company_info_search": "Consulta determinista a datos estructurados (company_info)",
}

_TOOL_ICONS = {
    "rag_search": ":material/manage_search:",
    "company_info_search": ":material/business:",
}


def _agente_extraer_fuentes(rag_output: str) -> list[dict[str, str]]:
    """Extrae lista de fuentes del output formateado por rag_search.

    Cabecera de cada bloque (formato actual):
        [Fuente: X | Sección: Y | Fragmento: N/M | Similitud: 0.NN]

    Formato legado (sin fragmento) también soportado por compatibilidad.
    """
    pattern_nuevo = re.compile(
        r"\[Fuente:\s*(.+?)\s*\|\s*Sección:\s*(.+?)\s*\|\s*"
        r"Fragmento:\s*(\d+/\d+)\s*\|\s*Similitud:\s*([\d.]+)\]"
    )
    pattern_legado = re.compile(
        r"\[Fuente:\s*(.+?)\s*\|\s*Sección:\s*(.+?)\s*\|\s*Similitud:\s*([\d.]+)\]"
    )

    fuentes: list[dict[str, str]] = []
    for m in pattern_nuevo.finditer(rag_output):
        fuentes.append({
            "fuente": m.group(1).strip(),
            "seccion": m.group(2).strip(),
            "fragmento": m.group(3).strip(),
            "similitud": m.group(4).strip(),
        })
    if fuentes:
        return fuentes

    for m in pattern_legado.finditer(rag_output):
        fuentes.append({
            "fuente": m.group(1).strip(),
            "seccion": m.group(2).strip(),
            "fragmento": "",
            "similitud": m.group(3).strip(),
        })
    return fuentes


def _agente_render_tool_panel(eventos_tools: list[dict], *, key_suffix: str = "") -> None:
    """Renderiza el desplegable de fuentes/herramientas usado para un mensaje del bot."""
    if not eventos_tools:
        with st.expander("Ver fuentes consultadas", expanded=False):
            st.caption(
                "El asistente no consultó documentos para esta respuesta "
                "(saludo, aclaración conversacional o pregunta fuera de alcance)."
            )
        return

    label = f"Ver fuentes consultadas ({len(eventos_tools)})"
    with st.expander(label, expanded=False):
        for i, ev in enumerate(eventos_tools, start=1):
            nombre = ev.get("name", "")
            args = ev.get("args", {}) or {}
            resultado = ev.get("result", "") or ""
            icono = _TOOL_ICONS.get(nombre, ":material/build:")
            descripcion = _TOOL_LABELS.get(nombre, nombre)

            st.markdown(f"**{i}. {icono} `{nombre}`** — {descripcion}")

            if args:
                args_pretty = ", ".join(f"`{k}={v!r}`" for k, v in args.items())
                st.caption(f"Argumentos: {args_pretty}")

            if nombre == "rag_search":
                fuentes = _agente_extraer_fuentes(resultado)
                if fuentes:
                    st.markdown("**Documentos consultados:**")
                    for f in fuentes:
                        nombre_doc = f["fuente"]
                        seccion = f.get("seccion") or "sin sección"
                        fragmento = f.get("fragmento", "")
                        sim = f.get("similitud", "")
                        ubic = f"fragmento {fragmento}" if fragmento else ""
                        partes = [p for p in [
                            f"**{nombre_doc}**",
                            f"sección _{seccion}_",
                            ubic,
                            f"similitud `{sim}`",
                        ] if p]
                        st.markdown("- " + " · ".join(partes))
            elif nombre == "company_info_search":
                categoria = args.get("category", "")
                if categoria:
                    st.markdown(
                        f"**Categoría consultada:** `{categoria}` "
                        "(tabla `company_info` — datos estructurados verificados)"
                    )
                else:
                    st.caption(
                        "Consulta general a `company_info` "
                        "(todas las categorías de datos estructurados)."
                    )

            if i < len(eventos_tools):
                st.divider()


def _agente_session_id() -> str:
    """Obtiene o crea un session_id estable para esta sesión de Streamlit."""
    if "agente_session_id" not in st.session_state:
        st.session_state.agente_session_id = secrets.token_urlsafe(12)
    return st.session_state.agente_session_id


def _render_agente_quick_topics(*, input_key: str) -> None:
    """Tarjetas sugeridas. Reusa keys `qa_quick_*` para heredar la CSS de Q&A."""
    st.markdown(
        '<p class="qa-quick-lead">También puedes preguntar sobre:</p>',
        unsafe_allow_html=True,
    )
    cols = st.columns(4, gap="medium")
    for i, (label, pregunta, icon) in enumerate(AGENTE_QUICK_TOPICS):
        with cols[i]:
            if st.button(
                label,
                key=f"qa_quick_{i}",
                use_container_width=True,
                type="secondary",
                icon=icon,
            ):
                st.session_state[input_key] = pregunta
                st.rerun()


def _render_agente_ejemplos_column(*, input_key: str) -> None:
    """Columna izquierda. Reusa keys `qa_ejemplo_*` para heredar la CSS de Q&A."""
    st.markdown(
        '<div class="qa-ejemplos-stack" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="qa-ejemplos-only-heading">Ejemplos de preguntas</p>',
        unsafe_allow_html=True,
    )
    for i, (pregunta, icon) in enumerate(AGENTE_EJEMPLO_PREGUNTAS):
        if st.button(
            pregunta,
            key=f"qa_ejemplo_{i}",
            use_container_width=True,
            type="secondary",
            icon=icon,
        ):
            st.session_state[input_key] = pregunta
            st.rerun()


def _ejecutar_consulta_agente(pregunta: str) -> None:
    """Encola la pregunta del usuario y limpia el input. El streaming real
    se ejecuta en el siguiente render dentro de `pagina_agente` para poder
    mostrar `st.status` + `st.write_stream` en vivo dentro del chat."""
    if not (pregunta and pregunta.strip()):
        return

    pregunta_limpia = pregunta.strip()
    # 1. Agregamos la pregunta al historial visible inmediatamente
    st.session_state.agente_chat_historial.append({
        "role": "user", "content": pregunta_limpia
    })
    # 2. Marcamos como pendiente para procesarla en el siguiente render
    st.session_state._agente_pending_question = pregunta_limpia
    # 3. Bandera para limpiar el input en el siguiente render
    st.session_state._agente_clear_input = True
    st.rerun()


def _procesar_pregunta_pendiente(pregunta: str) -> None:
    """Ejecuta `ask_streaming` con un spinner visible. Acumula los tokens
    sin mostrarlos en vivo: la respuesta final aparece dentro de la burbuja
    del bot del transcript después del rerun (look & feel idéntico al Q&A).
    """
    from riopaila_rag.agent import ask_streaming

    session_id = _agente_session_id()
    eventos_tools: list[dict] = []
    pending_tool: dict | None = None
    tokens: list[str] = []

    with st.spinner("Generando respuesta…", show_time=False):
        try:
            for event in ask_streaming(pregunta, session_id):
                kind = event["kind"]
                if kind == "tool_call":
                    pending_tool = {
                        "name": event["name"],
                        "args": event.get("args", {}),
                        "result": "",
                    }
                elif kind == "tool_result":
                    if pending_tool and pending_tool["name"] == event["name"]:
                        pending_tool["result"] = event["content"]
                        eventos_tools.append(pending_tool)
                        pending_tool = None
                elif kind == "token":
                    tokens.append(event["content"])
                elif kind == "final":
                    if event.get("content"):
                        tokens = [event["content"]]
            respuesta_final = "".join(tokens).strip() or "(sin respuesta)"
        except Exception as e:
            respuesta_final = f"Lo siento, ocurrió un error procesando la respuesta: {e}"

    st.session_state.agente_chat_historial.append({
        "role": "assistant",
        "content": respuesta_final,
        "tools": eventos_tools,
    })
    st.session_state.pop("_agente_pending_question", None)
    st.rerun()


def _on_enter_agente() -> None:
    """Callback disparado cuando el usuario presiona Enter en el campo
    de pregunta (o quita el foco). Encola la pregunta como pendiente
    sin invocar `st.rerun()` (Streamlit re-renderiza automáticamente
    después de ejecutar un callback)."""
    q = (st.session_state.get("qa_pregunta") or "").strip()
    if not q:
        return
    # Evita disparar dos veces si el usuario hizo Tab tras enviar
    if st.session_state.get("_agente_pending_question"):
        return
    st.session_state.setdefault("agente_chat_historial", []).append({
        "role": "user", "content": q
    })
    st.session_state._agente_pending_question = q
    st.session_state._agente_clear_input = True


def _render_agente_composer() -> None:
    """Composer del Agente. Reusa las keys `qa_pregunta` y `qa_enviar` para heredar la CSS."""
    st.markdown(
        '<div class="qa-composer-surface-anchor" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )
    row_left, row_btn = st.columns([3.4, 1.15])
    with row_left:
        q = st.text_input(
            "Tu pregunta",
            placeholder="Escribe tu pregunta aquí…",
            label_visibility="collapsed",
            key="qa_pregunta",
            on_change=_on_enter_agente,
        )
    with row_btn:
        if st.button(
            "Enviar",
            type="primary",
            key="qa_enviar",
            use_container_width=True,
            icon=":material/send:",
        ):
            _ejecutar_consulta_agente(q)


def _html_agente_chat_transcript(hist: list[dict]) -> str:
    """Transcript del Agente — reutiliza las burbujas y clases de Q&A."""
    if not hist:
        inner = (
            '<p class="qa-empty-hint">'
            "Escribe tu pregunta abajo o elige uno de los temas sugeridos."
            "</p>"
        )
    else:
        parts: list[str] = []
        for msg in hist:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                parts.append(_html_qa_user_bubble(content))
            elif role == "assistant":
                parts.append(_html_qa_bot_bubble(content))
        inner = "".join(parts)
    return (
        '<div class="qa-chat-transcript-shell">'
        '<div class="qa-chat-scroll-viewport" role="log" aria-live="polite" aria-relevant="additions">'
        f"{inner}</div></div>"
    )


def pagina_agente() -> None:
    """Página Agente (Módulo 2) — calco visual de Q&A con motor RAG + tools + memoria.

    Estrategia visual: la página se identifica con el mismo mount `qa-page-mount`
    que Q&A para heredar TODA la CSS scopeada (tarjeta unificada, columnas, chat,
    burbujas, composer). Añade un id adicional `agente-page-mount` por si se
    quisiera diferenciar en el futuro. Como las páginas no se renderizan a la vez,
    no hay colisión de keys con Q&A.
    """
    st.markdown(
        '<div id="qa-page-mount" class="qa-page-mount" aria-hidden="true"></div>'
        '<div id="agente-page-mount" class="agente-page-mount" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )

    # CSS scopeado: estilo claro y centrado para el st.status y los expanders
    # del Agente (sobreescribe los estilos heredados con bajo contraste).
    st.markdown(
        f"""
        <style>
        /* Wrapper del expander: marca el inicio en columna izquierda */
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) div[class*="st-key-agente_fuentes_wrapper"] {{
            margin-top: 18px !important;
        }}
        /* Caja del expander (solo el de fuentes del agente, scopeado por wrapper key).
           Vive en la columna izquierda — ancho 100% del rail. */
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) div[class*="st-key-agente_fuentes_wrapper"] [data-testid="stExpander"] {{
            background: {C_WHITE} !important;
            border: 1.5px solid {C_GREEN_SOFT} !important;
            border-radius: 14px !important;
            box-shadow: 0 2px 10px rgba(27, 94, 32, 0.06) !important;
            margin: 0 !important;
            width: 100% !important;
            overflow: hidden !important;
        }}
        /* Header del expander */
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) div[class*="st-key-agente_fuentes_wrapper"] [data-testid="stExpander"] summary {{
            background: linear-gradient(135deg, {C_GREEN_SOFT} 0%, #ffffff 100%) !important;
            color: {C_GREEN} !important;
            font-weight: 700 !important;
            padding: 12px 18px !important;
            list-style: none !important;
            border-top-left-radius: 14px !important;
            border-top-right-radius: 14px !important;
        }}
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) div[class*="st-key-agente_fuentes_wrapper"] [data-testid="stExpander"] summary * {{
            color: {C_GREEN} !important;
            fill: {C_GREEN} !important;
        }}
        /* CONTENIDO DEL EXPANDER — altura fija compacta con scroll interno.
           Mantiene el panel pequeño para no sobresalir del recuadro verde. */
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) div[class*="st-key-agente_fuentes_wrapper"] [data-testid="stExpanderDetails"] {{
            background: {C_WHITE} !important;
            color: {C_TEXT} !important;
            padding: 12px 14px 20px 14px !important;
            height: 240px !important;
            max-height: 240px !important;
            overflow-y: scroll !important;
            overflow-x: hidden !important;
            scrollbar-width: thin !important;
            scrollbar-color: {C_GREEN} rgba(27, 94, 32, 0.08) !important;
            border-bottom-left-radius: 14px !important;
            border-bottom-right-radius: 14px !important;
            font-size: 0.85rem !important;
            display: block !important;
            box-sizing: border-box !important;
        }}
        /* Aire adicional al final del contenido del expander */
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) div[class*="st-key-agente_fuentes_wrapper"] [data-testid="stExpanderDetails"] > *:last-child {{
            margin-bottom: 12px !important;
        }}
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) div[class*="st-key-agente_fuentes_wrapper"] [data-testid="stExpanderDetails"]::-webkit-scrollbar {{
            width: 10px !important;
        }}
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) div[class*="st-key-agente_fuentes_wrapper"] [data-testid="stExpanderDetails"]::-webkit-scrollbar-track {{
            background: rgba(27, 94, 32, 0.06) !important;
            border-radius: 0 0 14px 0 !important;
        }}
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) div[class*="st-key-agente_fuentes_wrapper"] [data-testid="stExpanderDetails"]::-webkit-scrollbar-thumb {{
            background: {C_GREEN} !important;
            border-radius: 8px !important;
            border: 2px solid {C_WHITE} !important;
        }}
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) div[class*="st-key-agente_fuentes_wrapper"] [data-testid="stExpanderDetails"]::-webkit-scrollbar-thumb:hover {{
            background: #145214 !important;
        }}
        /* Wrap de líneas largas (rutas / URLs) */
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) div[class*="st-key-agente_fuentes_wrapper"] [data-testid="stExpander"] *,
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) div[class*="st-key-agente_fuentes_wrapper"] details[data-testid="stExpander"] * {{
            overflow-wrap: anywhere !important;
            word-break: break-word !important;
        }}

        /* Bloques <code> inline dentro del expander: fondo claro, texto legible */
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) [data-testid="stExpander"] code,
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) details[data-testid="stExpander"] code {{
            background: {C_GREEN_SOFT} !important;
            color: {C_GREEN} !important;
            padding: 2px 8px !important;
            border-radius: 6px !important;
            border: 1px solid rgba(27, 94, 32, 0.12) !important;
            font-family: ui-monospace, "Cascadia Code", "Consolas", monospace !important;
            font-size: 0.85em !important;
            font-weight: 500 !important;
        }}

        /* Texto general dentro del expander: legible sobre fondo blanco */
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) [data-testid="stExpander"] p,
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) [data-testid="stExpander"] li,
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) [data-testid="stExpander"] span:not(code):not(.material-symbols-outlined),
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) [data-testid="stExpander"] div:not([data-testid]),
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) details[data-testid="stExpander"] p,
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) details[data-testid="stExpander"] li,
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) details[data-testid="stExpander"] span:not(code):not(.material-symbols-outlined) {{
            color: {C_TEXT} !important;
        }}

        /* Negritas en verde institucional para destacar nombres */
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) [data-testid="stExpander"] strong,
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) details[data-testid="stExpander"] strong {{
            color: {C_GREEN} !important;
            font-weight: 700 !important;
        }}

        /* Captions (st.caption) */
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) [data-testid="stExpander"] [data-testid="stCaptionContainer"],
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) [data-testid="stExpander"] [data-testid="stCaptionContainer"] * {{
            color: {C_TEXT_MUTED} !important;
        }}

        /* Iconos Material Symbols dentro del expander */
        [data-testid="stAppViewContainer"]:has(#agente-page-mount) [data-testid="stExpander"] .material-symbols-outlined {{
            color: {C_GREEN} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.pop("_agente_pending_chat_clear", False):
        from riopaila_rag.agent import clear_session
        clear_session(_agente_session_id())
        st.session_state.agente_chat_historial = []
        st.session_state.qa_pregunta = ""
        st.session_state.pop("_agente_pending_question", None)
        st.session_state.agente_session_id = secrets.token_urlsafe(12)

    # Bandera levantada por _ejecutar_consulta_agente para vaciar el campo
    # (Streamlit no permite modificar el valor de un widget ya renderizado;
    # debemos hacerlo ANTES de que el widget se cree)
    if st.session_state.pop("_agente_clear_input", False):
        st.session_state.qa_pregunta = ""

    if "agente_chat_historial" not in st.session_state:
        st.session_state.agente_chat_historial = []

    # ── Hero carrusel (idéntico al de Q&A) ──────────────────────────────────
    with st.container():
        _render_hero_unificado(
            _collect_hero_images(),
            hero_layout="faq_banner",
            show_cap=False,
            title_txt="Agente — RAG + Tools",
            sub="Asistente con búsqueda semántica, datos estructurados y memoria persistente.",
            title_color=C_GREEN,
            show_title_emoji=False,
        )

    st.markdown(
        '<div class="qa-after-hero-spacer" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )

    # ── Tarjeta unificada — usa las mismas keys (qa_unified_card / qa_chat_inset)
    #    que Q&A para que TODA la CSS scopeada aplique tal cual.
    with st.container(border=False, key="qa_unified_card", gap=None):
        st.markdown(
            '<div class="qa-unified-card-root" aria-hidden="true"></div>',
            unsafe_allow_html=True,
        )
        _render_qa_header_bar()
        with st.container(border=False, key="qa_chat_inset", gap="medium"):
            st.markdown(
                '<div class="qa-chat-gray-root" aria-hidden="true"></div>',
                unsafe_allow_html=True,
            )
            hist = st.session_state.agente_chat_historial
            pending = st.session_state.get("_agente_pending_question")

            rail_col, chat_col = st.columns([1, 2.05], gap="medium")
            with rail_col:
                _render_agente_ejemplos_column(input_key="qa_pregunta")

                # ── Panel de fuentes del último mensaje del bot ─────────────
                # Vive en la columna izquierda, debajo de los ejemplos.
                # Aprovecha el espacio vacío del rail y queda siempre visible
                # sin tapar el composer ni el chat.
                if not pending:
                    ultimo_asistente = next(
                        (m for m in reversed(hist) if m.get("role") == "assistant"),
                        None,
                    )
                    if ultimo_asistente is not None and "tools" in ultimo_asistente:
                        with st.container(key="agente_fuentes_wrapper"):
                            _agente_render_tool_panel(ultimo_asistente.get("tools") or [])

            with chat_col:
                st.markdown(
                    '<div class="qa-chat-stream-root" aria-hidden="true"></div>',
                    unsafe_allow_html=True,
                )
                inner_col = st.columns([1])[0]
                with inner_col:
                    st.markdown(
                        _html_agente_chat_transcript(hist),
                        unsafe_allow_html=True,
                    )

                    # Si hay pregunta pendiente, ejecutar el streaming AQUÍ
                    if pending:
                        _procesar_pregunta_pendiente(pending)
                        # _procesar_pregunta_pendiente termina con st.rerun(),
                        # así que el código de abajo no se ejecuta en este render

                    _render_agente_quick_topics(input_key="qa_pregunta")

                    _render_agente_composer()

                    if st.button("Limpiar conversación", key="qa_limpiar", type="secondary"):
                        st.session_state["_agente_pending_chat_clear"] = True
                        st.rerun()

    st.markdown(
        '<div class="qa-m1-below-spacer" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )
    _pie()


def main() -> None:
    st.set_page_config(
        page_title="Riopaila Castillo — Asistente",
        page_icon="🌿",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inyectar_estilos_globales()
    _configurar_groq_api_key()
    _init_state()
    _sync_nav_from_query()
    _sidebar()

    p = st.session_state.pagina
    if p == "Inicio":
        pagina_inicio()
    elif p == "Resumen":
        pagina_resumen()
    elif p == "FAQ":
        pagina_faq()
    elif p == "Q&A":
        pagina_qa()
    elif p == "Agente":
        pagina_agente()
    else:
        st.session_state.pagina = "Inicio"
        pagina_inicio()


if __name__ == "__main__":
    main()

