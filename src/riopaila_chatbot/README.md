# `src/riopaila_chatbot/` — Módulo 1: Scrapers de la base de conocimiento

Paquete legado del **Módulo 1**. Contiene los scrapers que construyen el corpus de conocimiento de Riopaila Castilla a partir de fuentes públicas. La salida cruda (`reports/*.md`) se consolida después con `src/scripts/merge_reports.py` y `clean_context.py` en `data/knowledge/riopaila_castilla_clean.md`.

## Scrapers (`scrapers/`)

| Archivo | Comando | Fuente |
|---|---|---|
| `web.py` | `make scrape-web` | Sitio web oficial `riopaila-castilla.com` (Selenium + BeautifulSoup). |
| `linkedin.py` | `make scrape-linkedin` | Posts de LinkedIn (requiere login manual). |
| `instagram.py` | `make scrape-instagram` | Posts de Instagram y otras redes (requiere login manual). |
| `simev.py` | `make scrape-simev` | Reportes regulatorios de **SIMEV** (Superfinanciera) + descarga de PDFs. |

Ejecutar todos en secuencia:

```bash
make scrape-all          # web + simev + linkedin + instagram
make build-knowledge     # consolida (merge) + limpia (clean) → riopaila_castilla_clean.md
```

## Notas

- **Login manual:** LinkedIn e Instagram requieren autenticación interactiva; los scrapers abren el navegador (Selenium + `webdriver-manager`) y esperan a que el usuario inicie sesión.
- **Salida no versionada:** los datos crudos van a `reports/` (ignorado por git). Lo que se versiona es el resultado limpio en `data/knowledge/`.
- **Evolución:** este conocimiento alimenta los tres módulos — directamente el Módulo 1 (context stuffing), tras embeber el Módulo 2 (RAG en Supabase) y, migrado, el Módulo 3 (memoria de OpenFang).
- **Encoding Windows:** los scripts evitan caracteres no-ASCII en la consola (`OK`/`FAIL` en vez de `✓`/`✗`) para no romper en `cp1252`.
