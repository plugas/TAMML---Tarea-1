"""
Base de conocimiento + tareas LangChain (Q&A sin RAG vectorial).

- Carga el texto consolidado (`data/knowledge/riopaila_castilla_clean.md`).
- Limpieza (conserva párrafos y marcadores `FUENTE:`) y fragmentación semántica (chunking) con LangChain.
- FAQ / Q&A y bloques satélite en Resumen (propósito, pie, líneas): selección léxica + la cadena **Q&A** (`cadena_qa_libre`) salvo la tarea explícita **Resumen** (`cadena_resumen`) y **FAQ** índice (`cadena_faq`).
- Tope de contexto al LLM: `KB_MAX_CONTEXT_CHARS` (por defecto 12_000). Para propósito/pie/líneas en Resumen: **`KB_MAX_CONTEXT_CHARS_TEMATICO`** (por defecto ~5_500) para aliviar límites TPM de Groq.
- Ante error **429** (tokens por minuto) se reintenta automáticamente con esperas breves.
"""
from __future__ import annotations

import os
import re
import time
from typing import Any, Final

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter

from dotenv import load_dotenv

from riopaila_rag.paths import ARCHIVOS_INSUMO_CONSOLIDADO, DATA_DIR, PATH_CONSOLIDADO

load_dotenv()

# Directorio de salida para exportaciones (muestra de chunks, etc.)
REPORTES_DIR = DATA_DIR


def _max_context_chars_config() -> int:
    """Tope de caracteres del CONTEXTO enviado al LLM (sin contar el prompt). KB_MAX_CONTEXT_CHARS en entorno."""
    raw = os.getenv("KB_MAX_CONTEXT_CHARS", "").strip()
    if raw.isdigit():
        return max(4_000, min(int(raw), 131_072))
    # Por defecto conservador: el plan gratuito de Groq suele limitar ~6000 TPM; ~48k chars
    # disparaban ~13k+ tokens por solicitud y devolvían error 413.
    return 12_000


MAX_CONTEXT_CHARS: Final[int] = _max_context_chars_config()


def _max_context_chars_tematico() -> int:
    """Tope de caracteres para propósito / pie / líneas de negocio (menos TPM por llamada)."""
    raw = os.getenv("KB_MAX_CONTEXT_CHARS_TEMATICO", "").strip()
    if raw.isdigit():
        return max(2_500, min(int(raw), MAX_CONTEXT_CHARS))
    return min(5_500, MAX_CONTEXT_CHARS)


_CHUNK_SIZE: Final[int] = 1_400
_CHUNK_OVERLAP: Final[int] = 180
_GROQ_MODEL_DEFAULT = "qwen/qwen3-32b"

# Correo con dominio (evita priorizar menciones tipo @usuario en redes).
_EMAIL_DOMINIO_RX = re.compile(
    r"[a-z0-9][a-z0-9._%+-]{0,63}@[a-z0-9][a-z0-9.-]*\.[a-z]{2,63}",
    re.IGNORECASE,
)

_STOPWORDS: Final[frozenset[str]] = frozenset(
    {
        "que",
        "qué",
        "cual",
        "cuál",
        "cuales",
        "cuáles",
        "como",
        "cómo",
        "donde",
        "dónde",
        "cuando",
        "cuándo",
        "por",
        "para",
        "con",
        "sin",
        "del",
        "al",
        "el",
        "la",
        "los",
        "las",
        "un",
        "una",
        "unos",
        "unas",
        "es",
        "son",
        "está",
        "están",
        "hay",
        "han",
        "más",
        "menos",
        "muy",
        "todo",
        "toda",
        "todos",
        "todas",
        "este",
        "esta",
        "eso",
        "esa",
        "sobre",
        "entre",
        "desde",
        "hacia",
        "también",
        "pero",
        "solo",
        "sólo",
        "ya",
        "quien",
        "quién",
        "puede",
        "puedo",
        "ser",
        "sus",
        "nuestros",
        "nuestra",
        "the",
        "and",
        "for",
    }
)

# Pregunta activa un tema → sumamos términos para rankear chunks (recuperación léxica).
_RET_TERMS_POR_TEMA: Final[tuple[tuple[frozenset[str], frozenset[str]], ...]] = (
    (
        frozenset(
            {
                "contacto",
                "contactar",
                "llamar",
                "escribir",
                "correo",
                "email",
                "e-mail",
                "telefono",
                "teléfono",
                "whatsapp",
                "comunicarse",
                "pqrs",
                "petición",
                "peticion",
                "reclamo",
            }
        ),
        frozenset(
            {
                "contacto",
                "teléfono",
                "telefono",
                "celular",
                "móvil",
                "movil",
                "correo",
                "email",
                "@",
                "whatsapp",
                "pagina",
                "página",
                "web",
                "línea",
                "linea",
                "atención",
                "atencion",
                "oficina",
                "número",
                "numero",
                "PBX",
                "directo",
                "infolinea",
                "servicio",
                "cliente",
                "ciudadano",
                "dirección",
                "direccion",
            }
        ),
    ),
    (
        frozenset({"ubicacion", "ubicación", "ubicadas", "ubicado", "donde", "dónde", "operaciones", "sede", "sedes", "planta", "plantas", "ingenio"}),
        frozenset({"ubicación", "ubicacion", "dirección", "direccion", "municipio", "departamento", "valle", "cauca", "colombia", "planta", "ingenio"}),
    ),
    (
        frozenset({"historia", "trayectoria", "origen", "fundación", "fundacion", "1918"}),
        frozenset(
            {
                "historia",
                "1918",
                "trayectoria",
                "somos",
                "siglo",
                "trapiche",
                "hacienda",
                "106",
                "años",
                "anos",
                "rnve",
                "sociedad",
                "emisores",
                "valores",
            }
        ),
    ),
    (
        frozenset({"producto", "productos", "servicio", "servicios", "ofrece", "negocio", "líneas", "lineas"}),
        frozenset({"alimento", "energía", "energia", "combustible", "abono", "agrícola", "agricola", "caña", "cana", "renovable"}),
    ),
    (
        frozenset({"sostenibilidad", "medioambiente", "ambiente", "esg", "carbono", "ambiental"}),
        frozenset({"sostenibilidad", "regenerativa", "carbono", "ambiental", "territorial", "cadena", "suministro", "fsa"}),
    ),
    (
        frozenset({"noticias", "noticia", "blog", "boletín", "boletin", "oficial"}),
        frozenset({"noticia", "noticias", "boletín", "boletin", "somos", "riopaila-castilla"}),
    ),
    (
        frozenset(
            {
                "proveedor",
                "proveedores",
                "aliado",
                "aliados",
                "suministro",
                "contratista",
                "contratistas",
                "abastecimiento",
                "compras",
            }
        ),
        frozenset(
            {
                "proveedor",
                "proveedores",
                "aliado",
                "aliados",
                "suministro",
                "abastecimiento",
                "compras",
                "contratación",
                "contratacion",
                "licitación",
                "licitacion",
                "cadena",
                "agricultor",
                "agricultores",
                "campo",
                "caña",
                "cana",
            }
        ),
    ),
    (
        frozenset(
            {
                "vacante",
                "vacantes",
                "empleo",
                "laboral",
                "trabajar",
                "trabajo",
                "postul",
                "postulación",
                "postulacion",
                "convocatoria",
                "talento",
                "ofertas",
                "oferta",
            }
        ),
        frozenset(
            {
                "linkedin",
                "nuestra",
                "gente",
                "trabaja",
                "vacante",
                "vacantes",
                "empleo",
                "ofertaslaborales",
                "colaborador",
                "humano",
                "riopaila-castilla.com",
            }
        ),
    ),
)


def cargar_texto_consolidado() -> str:
    if not PATH_CONSOLIDADO.is_file():
        return ""
    return PATH_CONSOLIDADO.read_text(encoding="utf-8", errors="replace")


def limpiar_texto_plano(texto: str) -> str:
    """Quita ruido pero conserva párrafos y marcadores FUENTE: para un chunking más coherente."""
    if not texto:
        return ""
    t = texto.replace("\r\n", "\n").replace("\r", "\n")
    lineas: list[str] = []
    for line in t.split("\n"):
        lineas.append(re.sub(r"[ \t]+", " ", line).strip())
    out = "\n".join(lineas)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def _fuentes_en_bloques_consolidado(raw: str) -> list[str]:
    return re.findall(r"(?m)^FUENTE:\s*(.+)$", raw)


def fragmentos_semanticos(texto: str) -> list[str]:
    if not texto.strip():
        return []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=_CHUNK_SIZE,
        chunk_overlap=_CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_text(texto)


def contexto_para_prompt(max_chars: int = MAX_CONTEXT_CHARS) -> str:
    """
    Contexto enviado al LLM: concatena chunks completos hasta llenar max_chars
    (evita cortar a mitad de un fragmento semántico).
    """
    raw = cargar_texto_consolidado()
    if not raw:
        return ""
    limpio = limpiar_texto_plano(raw)
    chunks = fragmentos_semanticos(limpio)
    if not chunks:
        return limpio[:max_chars]
    parts: list[str] = []
    total = 0
    for ch in chunks:
        sep = 2 if parts else 0
        if total + sep + len(ch) > max_chars:
            break
        parts.append(ch)
        total += sep + len(ch)
    return "\n\n".join(parts)


def _tokens_consulta(texto: str) -> set[str]:
    toks = set(re.findall(r"[a-záéíóúñü0-9]+", texto.lower()))
    return {t for t in toks if len(t) > 2 and t not in _STOPWORDS}


def _expandir_tokens_retrieval(pregunta: str, base: set[str]) -> set[str]:
    """Amplía la consulta con sinónimos según el tema (sin embeddings)."""
    out = set(base)
    pl = pregunta.lower()
    for disparadores, extras in _RET_TERMS_POR_TEMA:
        if disparadores & out or any(d in pl for d in disparadores):
            out |= extras
    return out


def _bigramas_consulta(texto: str) -> set[tuple[str, str]]:
    toks = re.findall(r"[a-záéíóúñü0-9]+", texto.lower())
    return {(toks[i], toks[i + 1]) for i in range(len(toks) - 1)}


def _score_fragmento(chunk: str, q_tokens: set[str], q_bigrams: set[tuple[str, str]]) -> float:
    cl = chunk.lower()
    ct = _tokens_consulta(chunk)
    inter = len(q_tokens & ct)
    largas_en_chunk = sum(1 for w in q_tokens if len(w) >= 5 and w in cl)
    bi = sum(1 for a, b in q_bigrams if a in cl and b in cl)
    return float(inter * 3 + largas_en_chunk * 2 + bi * 3)


def _pregunta_sobre_proveedores_o_aliados(pregunta: str) -> bool:
    pl = _pregunta_sin_instrucciones_internas(pregunta).lower()
    return any(
        k in pl
        for k in (
            "proveedor",
            "proveedores",
            "aliado",
            "aliados",
            "contratista",
            "contratistas",
        )
    ) or ("cadena" in pl and ("suministro" in pl or "abastecimiento" in pl))


def _bonus_proveedores_aliados_en_fragmento(pregunta: str, chunk_lower: str) -> float:
    if not _pregunta_sobre_proveedores_o_aliados(pregunta):
        return 0.0
    cues = (
        "proveedor",
        "proveedores",
        "aliado",
        "aliados",
        "suministro",
        "abastecimiento",
        "compras",
        "contratista",
        "licitación",
        "licitacion",
        "contratación",
        "contratacion",
        "agricultor",
        "agricultores",
    )
    n = sum(1 for k in cues if k in chunk_lower)
    if "cadena" in chunk_lower and ("abastecimiento" in chunk_lower or "suministro" in chunk_lower):
        n += 2
    return float(min(n * 10, 72))


def _bonus_contacto_en_fragmento(pregunta: str, chunk_lower: str) -> float:
    """Prioriza fragmentos con datos de contacto concretos cuando la pregunta lo pide."""
    pl = pregunta.lower()
    if not any(
        k in pl
        for k in (
            "contacto",
            "contactar",
            "llamar",
            "correo",
            "email",
            "whatsapp",
            "teléfono",
            "telefono",
            "escrib",
            "comunic",
        )
    ):
        return 0.0
    b = 0.0
    if _EMAIL_DOMINIO_RX.search(chunk_lower):
        b += 16.0
    elif "@" in chunk_lower:
        b += 2.0
    # Teléfonos y extensiones (incl. formatos sin espacios entre dígitos largos)
    if re.search(r"\d{7,}", chunk_lower):
        b += 14.0
    elif re.search(r"\b\d[\d\s\-+.()]{5,}\d\b", chunk_lower):
        b += 12.0
    if "whatsapp" in chunk_lower:
        b += 10.0
    if any(k in chunk_lower for k in ("tel:", "tel.", "tels.", "extension", "ext.", "PBX", "cel:", "móvil", "movil")):
        b += 6.0
    if "contacto" in chunk_lower and (_EMAIL_DOMINIO_RX.search(chunk_lower) or re.search(r"\d{7}", chunk_lower)):
        b += 8.0
    return b


def _score_fragmento_para_consulta(
    chunk: str,
    q_tokens: set[str],
    q_bigrams: set[tuple[str, str]],
    pq_detect: str,
) -> float:
    cl = chunk.lower()
    base = (
        _score_fragmento(chunk, q_tokens, q_bigrams)
        + _bonus_contacto_en_fragmento(pq_detect, cl)
        + _bonus_proveedores_aliados_en_fragmento(pq_detect, cl)
    )
    if not _pregunta_pide_contacto_general(pq_detect) and _chunk_es_bloque_contacto_predominante(chunk):
        base -= 95.0
    return base


def _chunk_es_bloque_contacto_predominante(chunk: str) -> bool:
    """Fragmento típico de «cómo contactarnos» (email + teléfono + texto de canales), no mezcla temática."""
    cl = chunk.lower()
    tiene_mail = bool(_EMAIL_DOMINIO_RX.search(chunk))
    tiene_tel = bool(re.search(r"\d{7,}", chunk))
    tiene_dir = any(
        x in cl for x in ("carrera ", "calle ", "santiago de cali", "edificio ", "dirección", "direccion")
    )
    cues_datos = sum((tiene_mail, tiene_tel, tiene_dir))
    palabras_canal = (
        "teléfono",
        "telefono",
        "correo electrónico",
        "correo electronico",
        "línea gratuita",
        "linea gratuita",
        "línea ética",
        "linea etica",
        "whatsapp",
        "sitio web",
        "www.",
        "contact",
        "comunicaciones@",
        "lineatransparencia",
        "cómo puedo contactar",
        "como puedo contactar",
        "puede contactar",
        "contáctenos",
        "contactenos",
        "contactarnos",
        "estamos a su disposición",
        "canales:",
        "canal:",
    )
    n_canal = sum(1 for k in palabras_canal if k in cl)
    if cues_datos >= 2 and n_canal >= 3:
        return True
    if tiene_mail and tiene_tel and n_canal >= 2:
        return True
    return False


def _pregunta_sin_instrucciones_internas(pregunta: str) -> str:
    """Recorta colas tipo «No incluyas correos…» / «no inventes…» para detectar intención real."""
    t = (pregunta or "").strip()
    low = t.lower()
    for marker in (
        " no incluyas ",
        " no respondas ",
        " sin datos de ",
        "\nno incluyas",
        "\nno respondas",
        "; no inventes ",
        " no inventes ",
    ):
        i = low.find(marker)
        if i != -1:
            t = t[:i].strip()
            low = t.lower()
    return t.strip()


def _chunk_es_footer_corporativo_informe(chunk: str) -> bool:
    """Boilerplate «consultas sobre el informe… gerente… comunicaciones@» (no operativo)."""
    cl = (chunk or "").lower()
    c0 = re.sub(r"\s+", "", cl)
    if "guillermocarvajal" in c0:
        return True
    if "guillermo carvajal" in cl:
        return True
    if "gerente" in cl and "asuntos corporativos" in cl:
        return True
    if "comunicaciones@" in c0 and "riopaila" in cl:
        return True
    if "para consultas relacionadas con" in cl and ("informe" in cl or "igr" in cl):
        return True
    if "informe global de reputación" in cl or "informe global de reputacion" in cl:
        return True
    if ("informe de sostenibilidad y gestión" in cl or "informe de sostenibilidad y gestion" in cl) and any(
        x in cl for x in ("correo", "gerente", "comunicaciones@", "punto de contacto", "consultas relacionadas")
    ):
        return True
    if "punto de contacto" in cl and "informe" in cl:
        return True
    return False


def _pregunta_pide_contacto_general(pregunta: str) -> bool:
    """¿La consulta busca medios de contacto del público / empresa (no solo tema normativo)?"""
    pl = _pregunta_sin_instrucciones_internas(pregunta).lower()
    return any(
        k in pl
        for k in (
            "contacto",
            "contactar",
            "comunic",
            "llamar",
            "correo",
            "email",
            "e-mail",
            "whatsapp",
            "teléfono",
            "telefono",
            "escrib",
            "ubicación",
            "ubicacion",
            "dirección",
            "direccion",
            "donde los encuentro",
            "donde encuentro",
            "atención",
            "atencion",
            "atención al cliente",
            "linea de atencion",
            "línea de atención",
            "número",
            "numero",
            "telephone",
        )
    )


def _chunk_tiene_datos_contacto_visibles(chunk: str) -> bool:
    """Fragmento que probablemente incluye datos útiles (no solo texto genérico)."""
    cl = chunk.lower()
    if _EMAIL_DOMINIO_RX.search(chunk):
        return True
    if "whatsapp" in cl or "wa.me" in cl:
        return True
    if re.search(r"\d{7,}", chunk):
        return True
    if re.search(r"\b\d{3}\s+\d{6,}\b", chunk):
        return True
    if "tel:" in cl or "mailto:" in cl:
        return True
    return False


def contexto_para_consulta(
    pregunta_usuario: str,
    max_chars: int | None = None,
    texto_retrieval: str | None = None,
    omitir_footer_informes_corporativos: bool = False,
) -> str:
    """
    Arma el CONTEXTO para FAQ/Q&A: rankea fragmentos por solape léxico con la consulta.

    ``texto_retrieval`` amplía términos para rankear sin cambiar la pregunta visible al LLM
    (útil para líneas de negocio / propósito sin sesgar la respuesta hacia «contacto»).
    ``omitir_footer_informes_corporativos``: excluye del ranking fragmentos boilerplate de «consultas sobre el informe…»
    / gerente de asuntos corporativos / comunicaciones@ (útil en líneas de negocio y propósito).
    """
    mc = max_chars or MAX_CONTEXT_CHARS
    raw = cargar_texto_consolidado()
    if not raw.strip():
        return ""
    limpio = limpiar_texto_plano(raw)
    chunks = fragmentos_semanticos(limpio)
    if not chunks:
        return limpio[:mc]

    pq_user = (pregunta_usuario or "").strip()
    pq_eff = (texto_retrieval or pq_user).strip()
    pq_detect = _pregunta_sin_instrucciones_internas(pq_user)
    q_tokens = _expandir_tokens_retrieval(pq_eff, _tokens_consulta(pq_eff))
    q_bi = _bigramas_consulta(pq_eff)

    aplicar_omit_footer = omitir_footer_informes_corporativos and not _pregunta_pide_contacto_general(
        pq_detect
    )

    ranked: list[tuple[float, int, str]] = []
    for idx, ch in enumerate(chunks):
        if aplicar_omit_footer and _chunk_es_footer_corporativo_informe(ch):
            sc = -1e9
        else:
            sc = _score_fragmento_para_consulta(ch, q_tokens, q_bi, pq_detect)
        ranked.append((sc, idx, ch))
    ranked.sort(key=lambda t: (-t[0], t[1]))

    parts: list[str] = []
    used: set[int] = set()
    total = 0

    def _empujar(idx: int, ch: str) -> bool:
        nonlocal total
        if idx in used:
            return False
        sep = 2 if parts else 0
        if total + sep + len(ch) > mc:
            return False
        parts.append(ch)
        used.add(idx)
        total += sep + len(ch)
        return True

    # Solo si la intención detectada pide contacto: priorizar fragmentos con datos de canal
    if _pregunta_pide_contacto_general(pq_detect):
        contact_ranked = [
            (_score_fragmento_para_consulta(ch, q_tokens, q_bi, pq_detect), idx, ch)
            for idx, ch in enumerate(chunks)
            if _chunk_tiene_datos_contacto_visibles(ch)
        ]
        contact_ranked.sort(key=lambda t: (-t[0], t[1]))
        for _, idx, ch in contact_ranked:
            _empujar(idx, ch)

    for _, idx, ch in ranked:
        _empujar(idx, ch)

    min_fill = max(800, min(mc - 1, int(mc * 0.35)))
    if total < min_fill:
        for _, idx, ch in ranked:
            _empujar(idx, ch)
            if total >= min_fill:
                break

    if total < mc:
        for _, idx, ch in ranked:
            _empujar(idx, ch)

    return "\n\n".join(parts)


def obtener_llm_groq(model: str | None = None, temperature: float = 0) -> ChatGroq:
    # Qwen3 puede incluir razonamiento en etiquetas; Groq permite ocultarlo en la respuesta.
    return ChatGroq(
        model=model or _GROQ_MODEL_DEFAULT,
        temperature=temperature,
        reasoning_format="hidden",
        reasoning_effort="none",
    )


_PROMPT_REGLAS = """\
Comportamiento: tu conocimiento para esta respuesta es únicamente la INFORMACIÓN DE REFERENCIA que recibes abajo (documentación interna). No inventes datos.

REGLAS DE CONTENIDO:
- Usa solo lo que conste en esa información. No cites fuentes externas que no aparezcan ahí.
- Si algo no consta, dilo en una frase breve y natural; no rellenes con suposiciones.
- Usa siempre la marca **Riopaila Castillo** (no "Castilla"), salvo en URLs literales copiadas de la información de referencia.

REDACCIÓN PARA EL USUARIO (obligatorio):
- Escribe como canal de información de la empresa: **no uses** las palabras «CONTEXTO», «contexto proporcionado», «texto proporcionado», «material adjunto», ni expliques que tus datos vienen de un documento o de un fragmento limitado.
- **No recomiendes** el Registro Nacional de Valores (RNVE), «emisores», organismos de supervisión ni páginas genéricas como “salida” cuando la pregunta es contacto o información práctica, salvo que la información de referencia mencione explícitamente ese tema de forma pertinente.
- Si preguntan cómo contactar: prioriza teléfonos, correos, WhatsApp, enlaces y direcciones que **sí** aparezcan; si solo hay datos parciales (p. ej. un correo de un área), ofrécelos primero. Si no hay ningún dato concreto, una sola frase neutra del tipo «No tenemos aquí ese dato de contacto consolidado» y, si quieres, invita en **una frase** a usar los canales públicos de Riopaila Castillo **sin** listar organismos regulatorios.
- Si la pregunta **no** es sobre contacto (teléfono, correo, dirección, sedes, «cómo ubicarlos», «medios de comunicación»): **no** respondas con listados de teléfonos, correos ni direcciones aunque salgan en la información de referencia; céntrate **solo** en lo que se preguntó (productos, líneas de negocio, propósito, historia, etc.).
- Si preguntan historia u origen, prioriza fechas, fundación e hitos que figuren en la información de referencia.
- Tono profesional y corporativo. No menciones que eres un modelo de lenguaje ni describas tu proceso interno.
"""


def cadena_resumen():
    tpl = (
        "Eres el asistente corporativo de Riopaila Castillo.\n"
        f"{_PROMPT_REGLAS}\n"
        "TAREA: Redacta un RESUMEN EJECUTIVO (3 a 5 párrafos breves) sobre la empresa: "
        "quiénes son, qué hacen, historia relevante y líneas de negocio que aparezcan en la información de referencia.\n\n"
        "INFORMACIÓN DE REFERENCIA:\n{contexto}\n\n"
        "RESUMEN:"
    )
    return ChatPromptTemplate.from_template(tpl) | obtener_llm_groq()


def cadena_faq():
    tpl = (
        "Eres el asistente corporativo de Riopaila Castillo.\n"
        f"{_PROMPT_REGLAS}\n"
        "TAREA: Responde la PREGUNTA de forma directa y útil para un visitante (estilo FAQ).\n"
        "- Si la pregunta es específica (p. ej. proveedores o aliados, empleo, energía, informes), "
        "centrarte en ese tema; **no** sustituyas la respuesta por un perfil genérico «quiénes somos» "
        "(años de historia, lista de productos o cobertura territorial) salvo que la referencia no "
        "contenga nada aplicable al tema.\n"
        "- Si al inicio del contexto aparece un bloque entre corchetes «Guía breve para esta pregunta "
        "del FAQ», intégralo con naturalidad y **priorízalo** cuando el resto sea solo descripción "
        "corporativa amplia.\n"
        "- Si en la referencia aparecen URLs (`https://…`) útiles para la pregunta (empleo, talento, "
        "proveedores, informes, etc.), **inclúyelas en la respuesta** como enlaces concretos para que el "
        "usuario pueda abrirlas; no las sustituyas solo por «sitio web» o «redes sociales» sin el enlace.\n\n"
        "INFORMACIÓN DE REFERENCIA:\n{contexto}\n\n"
        "PREGUNTA:\n{pregunta}\n\n"
        "RESPUESTA:"
    )
    return ChatPromptTemplate.from_template(tpl) | obtener_llm_groq()


_PROMPT_SOLO_CONTENIDO_OPERATIVO = """\
PRIORIDAD (esta respuesta):
- Entra directamente al tema: **sin** saludo («hola», «¡claro!»), **sin** «¿en qué puedo ayudarte?», **sin** preguntas retóricas al usuario.
- **Prohibido** usar plantillas de «para consultas sobre el informe…», gerente de asuntos corporativos, IGR, puntos de contacto para memorias, correos corporativos tipo comunicaciones@…, teléfonos, líneas gratuitas o direcciones, salvo que la PREGUNTA pida explícitamente esos datos.
- Si la información de referencia no cubre el tema, dilo en **una** frase breve; no sustituyas por datos de contacto.
"""


def cadena_qa_libre():
    tpl = (
        "Eres el Asistente experto de Riopaila Castillo.\n"
        f"{_PROMPT_REGLAS}\n"
        "Si la pregunta **sí** pide cómo contactar y en la información aparecen teléfonos o correos, inclúyelos tal cual.\n"
        "Si la pregunta **no** pide contacto, ignora bloques de teléfonos/correos en la información salvo que sean imprescindibles para responder el tema.\n\n"
        "INFORMACIÓN DE REFERENCIA:\n{contexto}\n\n"
        "Pregunta del usuario: {pregunta}\n\n"
        "Respuesta:"
    )
    return ChatPromptTemplate.from_template(tpl) | obtener_llm_groq()


def cadena_qa_solo_contenido_operativo():
    tpl = (
        "Eres el Asistente experto de Riopaila Castillo.\n"
        f"{_PROMPT_REGLAS}\n"
        f"{_PROMPT_SOLO_CONTENIDO_OPERATIVO}\n\n"
        "INFORMACIÓN DE REFERENCIA:\n{contexto}\n\n"
        "PREGUNTA:\n{pregunta}\n\n"
        "RESPUESTA DIRECTA (sin plantillas de informes ni saludos):"
    )
    return ChatPromptTemplate.from_template(tpl) | obtener_llm_groq()


_URL_SPLIT_RX = re.compile(r"(https?://[^\s\)\]>]+)")


def _normalizar_marca_respuesta(texto: str) -> str:
    """Unifica 'Riopaila Castilla' → 'Riopaila Castillo' en texto visible; no altera URLs."""
    if not texto.strip():
        return texto

    def _repl(m: re.Match[str]) -> str:
        raw = m.group(0)
        return "RIOPAILA CASTILLO" if raw.isupper() else "Riopaila Castillo"

    partes = _URL_SPLIT_RX.split(texto)
    out: list[str] = []
    for i, parte in enumerate(partes):
        if i % 2 == 1:
            out.append(parte)
            continue
        s = re.sub(r"\bRiopaila\s+Castilla\b", _repl, parte, flags=re.IGNORECASE)
        out.append(s)
    return "".join(out)


def _strip_bloques_razonamiento(texto: str) -> str:
    """Quita bloques de razonamiento si aparecen en `content` (p. ej. Qwen3 modo raw)."""
    if not texto:
        return texto
    out = texto
    # Etiquetas habituales en Qwen3 vía Groq (modo raw); ver langchain_groq `reasoning_format`.
    pares_abre_cierra = (
        ("<think>", "</think>"),
        ("<thinking>", "</thinking>"),
    )
    for abre, cierra in pares_abre_cierra:
        pat = re.escape(abre) + r"[\s\S]*?" + re.escape(cierra)
        out = re.sub(pat, "", out, flags=re.IGNORECASE)
    return out.strip()


def _limpiar_meta_respuesta_usuario(texto: str) -> str:
    """Quita restos de formulaciones meta («CONTEXTO», RNVE como consejo genérico) si el modelo las escapa."""
    if not texto or not texto.strip():
        return texto
    t = texto.strip()
    frases = (
        r"(?is)\b(?:lamentablemente[,:\s]+)?en\s+el\s+CONTEXTO\s+proporcionado[^.!?]*[.!?]\s*",
        r"(?is)\ben\s+el\s+CONTEXTO\s+no\s+[^.!?]{0,400}[.!?]\s*",
        r"(?is)\bno\s+(?:se\s+)?incluyen\s+(?:en\s+el\s+)?CONTEXTO[^.!?]{0,400}[.!?]\s*",
        r"(?is)\b(?:según|de\s+acuerdo\s+con)\s+el\s+CONTEXTO[^.!?]*[.!?]\s*",
        r"(?is)\bla\s+información\s+(?:del|en\s+el)\s+CONTEXTO[^.!?]*[.!?]\s*",
        r"(?is)\bel\s+CONTEXTO\s+proporcionado\s+[^.!?]{0,400}[.!?]\s*",
        r"(?is)\ben\s+el\s+contexto\s+proporcionado[^.!?]*[.!?]\s*",
        r"(?is)\bsi\s+necesitas\s+información\s+de\s+contacto,?\s*te\s+recomendamos[^.!?]{0,520}[.!?]\s*",
        r"(?is)\bte\s+recomendamos\s+revisar\s+la\s+página\s+oficial[^.!?]{0,520}[.!?]\s*",
        r"(?is)\bacudir\s+a\s+fuentes\s+oficiales[^.!?]{0,520}[.!?]\s*",
        r"(?is)\b(?:para\s+más\s+información,?\s*)?(?:te\s+)?(?:invitamos|sugerimos)\s+a\s+consultar[^.!?]{0,520}(?:RNVE|Registro\s+Nacional\s+de\s+Valores)[^.!?]*[.!?]\s*",
        r"(?is)^(¡\s*claro!?[^\n]*\n+)",
        r"(?is)^(¿en qué puedo ayudarte[^\n]*\n+)",
        r"(?is)^para consultas relacionadas con el contenido del informe[^\n]+\n*",
    )
    for pat in frases:
        t = re.sub(pat, "", t)
    t = re.sub(r"[ \t]+\n", "\n", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def _salida_mensaje(msg) -> str:
    raw = getattr(msg, "content", str(msg))
    limpio = _strip_bloques_razonamiento(raw)
    limpio = _limpiar_meta_respuesta_usuario(limpio)
    return _normalizar_marca_respuesta(limpio)


_MSG_GROQ_RATE_LIMIT = (
    "⚠️ **Límite temporal de Groq** (tokens por minuto). Espera **30–60 s** y vuelve a intentar "
    "(Regenerar resumen o la línea de negocio). En planes gratuitos el cupo es bajo si hay varias "
    "consultas seguidas. Opcional: variables `KB_MAX_CONTEXT_CHARS` y `KB_MAX_CONTEXT_CHARS_TEMATICO` "
    "para enviar menos texto por llamada."
)


def _groq_es_limite_velocidad(exc: BaseException) -> bool:
    s = str(exc).lower()
    return (
        "429" in str(exc)
        or "rate_limit" in s
        or "rate limit" in s
        or "tokens per minute" in s
        or "too many requests" in s
    )


def _invoke_cadena_groq_con_reintentos(cadena: Any, inputs: dict[str, str]) -> Any:
    """Reintenta ante 429 TPM (varias llamadas seguidas en la página Resumen)."""
    ultimo: BaseException | None = None
    for intento in range(5):
        try:
            return cadena.invoke(inputs)
        except BaseException as e:
            ultimo = e
            if not _groq_es_limite_velocidad(e) or intento == 4:
                raise
            time.sleep(min(18.0, 2.2 * (2**intento)))
    raise ultimo  # pragma: no cover


def invocar_resumen() -> str:
    ctx = contexto_para_prompt()
    if not ctx.strip():
        return (
            "⚠️ No hay texto en la base consolidada. Añade o actualiza el archivo "
            "`reportes/tu_archivo_riopaila.txt`."
        )
    if not os.getenv("GROQ_API_KEY"):
        return "⚠️ Falta GROQ_API_KEY (entorno o `.streamlit/secrets.toml`)."
    try:
        out = _invoke_cadena_groq_con_reintentos(cadena_resumen(), {"contexto": ctx})
    except BaseException as e:
        if _groq_es_limite_velocidad(e):
            return _MSG_GROQ_RATE_LIMIT
        raise
    return _salida_mensaje(out)


def invocar_faq(pregunta: str, *, respuesta_estatica: str | None = None) -> str:
    pq = (pregunta or "").strip()
    if not pq:
        return "Selecciona una pregunta en el índice de temas."
    ctx = contexto_para_consulta(pq)
    guia = (respuesta_estatica or "").strip()
    if guia:
        pref = (
            "[Guía breve para esta pregunta del FAQ — complementa con la documentación que sigue; "
            "no la contradigas salvo que la documentación sea inequívoca en otro sentido.]\n" + guia
        )
        ctx = f"{pref}\n\n---\n\n{ctx}" if ctx.strip() else pref
    if not ctx.strip():
        return "⚠️ No hay contexto consolidado disponible."
    if not os.getenv("GROQ_API_KEY"):
        return "⚠️ Falta GROQ_API_KEY."
    try:
        out = _invoke_cadena_groq_con_reintentos(cadena_faq(), {"contexto": ctx, "pregunta": pq})
    except BaseException as e:
        if _groq_es_limite_velocidad(e):
            return _MSG_GROQ_RATE_LIMIT
        raise
    return _salida_mensaje(out)


def invocar_qa(pregunta: str, *, texto_retrieval: str | None = None, solo_contenido_operativo: bool = False) -> str:
    pq = (pregunta or "").strip()
    if not pq:
        return ""
    ctx = contexto_para_consulta(
        pq,
        max_chars=_max_context_chars_tematico() if solo_contenido_operativo else None,
        texto_retrieval=texto_retrieval,
        omitir_footer_informes_corporativos=solo_contenido_operativo,
    )
    if not ctx.strip():
        return (
            "⚠️ No se encontró la base de conocimiento consolidada "
            "(`reportes/tu_archivo_riopaila.txt`)."
        )
    if not os.getenv("GROQ_API_KEY"):
        return "⚠️ Falta GROQ_API_KEY."
    cadena = cadena_qa_solo_contenido_operativo() if solo_contenido_operativo else cadena_qa_libre()
    try:
        out = _invoke_cadena_groq_con_reintentos(cadena, {"contexto": ctx, "pregunta": pq})
    except BaseException as e:
        if _groq_es_limite_velocidad(e):
            return _MSG_GROQ_RATE_LIMIT
        raise
    return _salida_mensaje(out)


_PREG_PROPOSITO_TARJETA_RESUMEN = """\
Resume en 2 a 4 frases el propósito o compromiso de Riopaila Castillo con productos de calidad, medio ambiente y comunidades, \
según únicamente lo que conste en la información de referencia que el sistema recuperará. Si no hay detalle suficiente, dilo en una frase breve.
"""

_TOKEN_BURST_PROPOSITO_RESUMEN = (
    "misión visión propósito valores corporativos sostenibilidad comunidades territorio bienestar "
    "ambiente responsabilidad social transformación regenerativa cadena agroindustrial estrategia "
    "compromiso cultura organizacional propuesta de valor excelencia futuro"
)

_PREG_MENSAJE_CIERRE_RESUMEN = """\
Redacta un solo párrafo breve tipo mensaje institucional de cierre (tono cercano y profesional): debe reflejar que la empresa \
trabaja cada día por productos y servicios de calidad, cuidando el medio ambiente y el bienestar de las comunidades. \
Fundamenta solo en lo que aparezca en la información de referencia recuperada; no inventes cifras ni menciones canales que no figuren explícitamente ahí.
"""

_TOKEN_BURST_CIERRE_RESUMEN = (
    "compromiso sostenibilidad comunidades territorio calidad excelencia transformación regenerativa "
    "cadena de valor impacto positivo futuro responsabilidad huella ambiental innovación"
)

_LINEA_NEGOCIO_PREGUNTA: dict[str, str] = {
    "azucar": (
        "¿Qué menciona la información sobre azúcar de caña, azúcar crudo o refinada, y la cadena agroindustrial del azúcar "
        "en Riopaila Castillo? Organiza la respuesta en viñetas cortas usando únicamente lo sustentado en la información de referencia."
    ),
    "energia": (
        "¿Qué dice la información sobre energía renovable, cogeneración, bagazo, biomasa o generación eléctrica en Riopaila Castillo? "
        "Viñetas cortas; únicamente lo sustentado en la información de referencia."
    ),
    "biocombustibles": (
        "¿Qué aparece sobre biocombustibles, etanol o esquema caña–azúcar vinculado a Riopaila Castillo? "
        "Respuesta breve basada exclusivamente en la información de referencia."
    ),
    "derivados": (
        "¿Qué derivados o coproductos de la caña o la molienda (melaza, alcohol, subproductos, etc.) menciona la información "
        "respecto a Riopaila Castillo? Viñetas; solo hechos presentes en la información de referencia."
    ),
}

_LINEA_NEGOCIO_TOKEN_BURST: dict[str, str] = {
    "azucar": (
        "azúcar caña molienda trapiche ingenio refino crudo especializado portfolio azúcar morena jarabe "
        "pulverizado sacarosa jugo diluido molinos clarificación meladura tachos centrifugación centrifuga bagazo "
        "melaza alcohol fermentación destilería cristales empaque sacos melaza cat toneladas"
    ),
    "energia": (
        "energía renovable cogeneración bagazo biomasa electricidad megavatios planta térmica autoconsumo "
        "matriz eléctrica eficiencia emisiones vapor turbina"
    ),
    "biocombustibles": (
        "biocombustible etanol alcohol carburante oxigenante mezcla porcentaje litros caña jugo fermentación "
        "producción nacional anhidro combustible renovable"
    ),
    "derivados": (
        "derivados melaza jarabe invertido alcohol anhidro coproductos fertilizante fertirio palmiste "
        "bioinsumos subproductos molienda oleaginosas"
    ),
}


def invocar_proposito_tarjeta_resumen() -> str:
    """Tarjeta «propósito» en página Resumen: misma cadena Q&A + recuperación léxica sobre la pregunta."""
    tr = f"{_PREG_PROPOSITO_TARJETA_RESUMEN} {_TOKEN_BURST_PROPOSITO_RESUMEN}"
    return invocar_qa(_PREG_PROPOSITO_TARJETA_RESUMEN, texto_retrieval=tr, solo_contenido_operativo=True)


def invocar_mensaje_cierre_resumen() -> str:
    """Pie de página Resumen: párrafo corto fundado solo en chunks recuperados."""
    tr = f"{_PREG_MENSAJE_CIERRE_RESUMEN} {_TOKEN_BURST_CIERRE_RESUMEN}"
    return invocar_qa(_PREG_MENSAJE_CIERRE_RESUMEN, texto_retrieval=tr, solo_contenido_operativo=True)


def invocar_linea_negocio(linea_key: str) -> str:
    """Pregunta guía por línea de negocio para demostración Módulo 1 (sin texto prefabricado en Streamlit)."""
    k = (linea_key or "").strip().lower()
    pq = _LINEA_NEGOCIO_PREGUNTA.get(k)
    if not pq:
        return "Línea de negocio no reconocida."
    burst = _LINEA_NEGOCIO_TOKEN_BURST.get(k, "")
    tr = f"{pq} {burst}".strip()
    return invocar_qa(pq, texto_retrieval=tr, solo_contenido_operativo=True)


def estadisticas_base() -> dict[str, object]:
    """Métricas para panel Streamlit (Módulo 1: consolidación + chunking)."""
    path = PATH_CONSOLIDADO
    esperados = list(ARCHIVOS_INSUMO_CONSOLIDADO)
    insumo_ausente_disco = [f for f in esperados if not (REPORTES_DIR / f).is_file()]
    if not path.is_file():
        return {
            "existe": False,
            "ruta": str(path),
            "insumo_ausente_disco": insumo_ausente_disco,
            "fuentes_esperadas": esperados,
        }
    raw = path.read_text(encoding="utf-8", errors="replace")
    marcadas = _fuentes_en_bloques_consolidado(raw)
    set_m = set(marcadas)
    fuentes_faltantes_en_consolidado = [f for f in esperados if f not in set_m]
    limpio = limpiar_texto_plano(raw)
    chunks = fragmentos_semanticos(limpio)
    ctx_seq = contexto_para_prompt()
    ctx_busqueda = contexto_para_consulta(
        "contacto teléfono correo ubicación sedes operaciones historia productos noticias"
    )
    return {
        "existe": True,
        "ruta": str(path.resolve()),
        "chars_archivo": len(raw),
        "chars_tras_limpieza": len(limpio),
        "num_chunks": len(chunks),
        "chars_contexto_prompt": len(ctx_seq),
        "chars_contexto_consulta_ejemplo": len(ctx_busqueda),
        "max_context_config": MAX_CONTEXT_CHARS,
        "fuentes_en_consolidado": marcadas,
        "fuentes_esperadas": esperados,
        "fuentes_faltantes_en_consolidado": fuentes_faltantes_en_consolidado,
        "insumo_ausente_disco": insumo_ausente_disco,
    }


def exportar_muestra_chunks(max_chunks: int = 80) -> str:
    """Genera `reportes/muestra_chunks_semanticos.txt` para evidencia en informe / revisión."""
    REPORTES_DIR.mkdir(parents=True, exist_ok=True)
    raw = cargar_texto_consolidado()
    limpio = limpiar_texto_plano(raw)
    chunks = fragmentos_semanticos(limpio)[:max_chunks]
    muestra = "\n\n--- CHUNK ---\n\n".join(chunks)
    out = REPORTES_DIR / "muestra_chunks_semanticos.txt"
    out.write_text(muestra, encoding="utf-8")
    return str(out)


if __name__ == "__main__":
    path = exportar_muestra_chunks()
    print("Muestra de chunks escrita en:", path)

