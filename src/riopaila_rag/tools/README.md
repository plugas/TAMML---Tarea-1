# `src/riopaila_rag/tools/` — Herramientas del agente

Cada archivo expone una **tool LangChain** decorada con `@tool` que el agente ReAct invoca autónomamente. Las descripciones de cada tool están escritas para guiar al modelo en su decisión de cuándo usarlas.

## Archivos

### `__init__.py`
Re-exporta las dos tools:
```python
from riopaila_rag.tools import rag_search, company_info_search
```

### `rag_tool.py` — `rag_search(query)`

**Propósito:** búsqueda semántica en la base de documentos vectorizada (Supabase pgvector). Se usa para preguntas narrativas y descriptivas.

**Flujo interno:**
1. Embedde la `query` con OpenAI `text-embedding-3-small` (1536 dimensiones).
2. Llama a la función SQL `match_documents(query_embedding, match_count, filter)` que hace búsqueda por similitud coseno.
3. Retorna los `RAG_TOP_K` (default 5) fragmentos más similares con header:
   ```
   [Fuente: <archivo.md> | Sección: <X> | Fragmento: 23/319 | Similitud: 0.87]
   <contenido del chunk>
   ```

**Datos consultados:**
- Tabla `documents` en Supabase (2.515 chunks indexados).
- 26 archivos fuente: `riopaila_castilla_clean.md` + 25 PDFs convertidos (informes trimestrales SFC, sostenibilidad 2024 y 2025, Código País, comunicados de JD, convocatorias AGA, medidas Asamblea, etc.).

**Cliente Supabase:** instanciado como singleton al importar el módulo. Si la conexión falla, retorna `"Error: cliente Supabase no disponible."` en vez de levantar excepción (el agente puede manejar el error gracefulmente).

### `structured_tool.py` — `company_info_search(category)`

**Propósito:** consulta determinista a datos estructurados verificados. Se usa cuando la pregunta requiere un dato exacto (NIT, teléfono, email, certificación, cifra puntual).

**Flujo interno:**
1. Valida que `category` esté en el set `_VALID_CATEGORIES`.
2. Filtra la tabla `company_info` por esa categoría (o todas si está vacía).
3. Agrupa los resultados por categoría y los formatea como Markdown.

**Categorías disponibles (9):**
| Categoría | Contiene |
|---|---|
| `contacto` | PBX, emails (proveedores, cumplimiento, línea ética, ventas miel) |
| `redes_sociales` | URLs oficiales (LinkedIn, Instagram, YouTube, Facebook) |
| `sedes` | Direcciones de oficinas y plantas |
| `legal` | NIT (900.087.414-4), razón social, año fundación, tipo de sociedad |
| `cifras` | Empleados (>3.800), hectáreas, capacidad de producción |
| `negocio` | Segmentos y productos principales |
| `sostenibilidad` | Iniciativas y metas |
| `certificaciones` | ISO, FSSC, Rainforest Alliance, Bonsucro, etc. |
| `fundacion` | Información de la Fundación Riopaila Castilla |

**Datos:** 42 filas verificadas, cargadas vía `supabase/seeds/company_info.sql`. Extraídas manualmente del KB consolidado durante la fase de setup.

**Por qué existe esta tool:** la búsqueda semántica puede devolver datos antiguos o mal formateados (especialmente cifras numéricas, teléfonos truncados, etc.). Esta tool da respuestas **canónicas** verificadas, evitando alucinaciones en preguntas sensibles como el NIT.

## Cómo añadir una tool nueva

1. Crear `nueva_tool.py` con una función decorada `@tool`.
2. Escribir un **docstring claro** explicando cuándo usarla — el modelo lo lee como descripción para decidir.
3. Exportarla desde `__init__.py`.
4. Registrarla en `agent.py`:
   ```python
   _agent = create_react_agent(llm, [rag_search, company_info_search, nueva_tool], ...)
   ```

## Hallazgos importantes

- **Descripciones de tools = guía del modelo**: cambiar el docstring afecta directamente la decisión del agente sobre cuándo invocar cada herramienta. Mantenerlas precisas y con ejemplos.
- **Imports lazy del cliente Supabase**: el `create_client` está protegido con `try/except` para no romper la importación si Supabase no responde — la tool reporta el error en su output.
- **Output formateado para parsing**: el header `[Fuente: ... | Sección: ... | Fragmento: N/M | Similitud: 0.NN]` que emite `rag_search` es parseado por `_agente_extraer_fuentes()` en `app.py` para mostrar el panel "Ver fuentes consultadas". No cambiar el formato sin actualizar también el parser.
