# `reports/` — Salidas crudas del scraping (Módulo 1)

![Selenium](https://img.shields.io/badge/Selenium-scraping-43B02A?logo=selenium&logoColor=white)
![Markdown](https://img.shields.io/badge/Markdown-salidas-000000?logo=markdown&logoColor=white)

Salidas directas de los scrapers del Módulo 1. Son archivos generados automáticamente — **no se editan a mano** y no se versionan en git (están en `.gitignore`). Se incluyen en el repo solo como referencia del estado actual del corpus.

## Archivos

| Archivo | Fuente | Formato | Generado por |
|---|---|---|---|
| `reporte_web_riopaila.md` / `.txt` | Sitio web oficial `riopaila-castilla.com` | Markdown / texto plano | `make scrape-web` |
| `reporte_linkedin_posts_riopaila.md` / `.txt` | Posts de LinkedIn | Markdown / texto plano | `make scrape-linkedin` |
| `reporte_instagram_posts_riopaila.md` / `.txt` | Posts de Instagram | Markdown / texto plano | `make scrape-instagram` |
| `reporte_simev_riopaila.md` / `.txt` / `.csv` | Reportes SIMEV (Superfinanciera) | Markdown / texto / CSV | `make scrape-simev` |
| `reporte_historia_riopaila.txt` | Historia corporativa (fuente web) | Texto plano | `make scrape-web` |

## Flujo de uso

Estas salidas son la entrada del pipeline de conocimiento:

```
reports/*.md  →  make merge  →  data/knowledge/riopaila_castilla.md
                    ↓
             make clean-ctx  →  data/knowledge/riopaila_castilla_clean.md
                                         ↓
                                  Módulo 1 (Q&A)
                                  Módulo 2 (ingest RAG)
                                  Módulo 3 (seed KV + Vector Store)
```

## Notas

- Los archivos `.txt` son versiones sin formato para depuración.
- El `.csv` de SIMEV estructura los metadatos de cada reporte regulatorio (fecha, tipo, URL).
- LinkedIn e Instagram requieren login manual en el navegador Selenium; la calidad del scraping depende de los permisos de la cuenta usada.
