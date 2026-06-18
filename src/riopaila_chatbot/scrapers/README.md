# `scrapers/` — Módulo 1: Extractores de fuentes públicas

![Selenium](https://img.shields.io/badge/Selenium-browser%20automation-43B02A?logo=selenium&logoColor=white)
![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-HTML%20parsing-4B8BBE)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)

Scrapers que construyen el corpus de conocimiento de Riopaila Castilla. Cada scraper es independiente y escribe su salida en `reports/`.

## Archivos

### `web.py` — Scraper del sitio oficial

**Comando:** `make scrape-web`

Extrae el contenido estructurado de `riopaila-castilla.com` usando Selenium para renderizar JavaScript y BeautifulSoup para parsear el HTML resultante. Navega secciones clave: historia, productos, sostenibilidad, gobierno corporativo y contacto.

**Salida:** `reports/reporte_web_riopaila.md` y `reports/reporte_historia_riopaila.txt`

**Función principal:** `scrape_website() -> str`

---

### `simev.py` — Scraper de reportes regulatorios (SIMEV)

**Comando:** `make scrape-simev`

Accede al sistema SIMEV de la Superintendencia Financiera de Colombia para extraer los reportes que Riopaila Castilla está obligada a publicar (hechos relevantes, estados financieros, comunicados). Descarga los PDFs a `data/pdfs/` y genera un índice estructurado.

**Salida:** `reports/reporte_simev_riopaila.md`, `.txt`, `.csv`

**Función principal:** `scrape_simev() -> str` — también invoca la descarga de PDFs

---

### `linkedin.py` — Scraper de LinkedIn

**Comando:** `make scrape-linkedin`

Extrae posts del perfil corporativo de Riopaila Castilla en LinkedIn. Requiere login manual: el scraper abre un navegador Selenium y espera a que el usuario inicie sesión antes de continuar.

**Salida:** `reports/reporte_linkedin_posts_riopaila.md` y `.txt`

**Función principal:** `scrape_linkedin() -> str`

> Login interactivo: el script detecta si el usuario ya está autenticado antes de continuar el scraping.

---

### `instagram.py` — Scraper de Instagram

**Comando:** `make scrape-instagram`

Extrae posts del perfil corporativo de Riopaila Castilla en Instagram. Igual que LinkedIn, requiere login manual vía Selenium.

**Salida:** `reports/reporte_instagram_posts_riopaila.md` y `.txt`

**Función principal:** `scrape_instagram() -> str`

---

### `__init__.py`

Marcador del paquete. Vacío por convención — los scrapers se invocan como módulos individuales (`python -m riopaila_chatbot.scrapers.web`) o vía `make`.

## Notas de implementación

- **Encoding Windows:** todos los scrapers usan `OK`/`FAIL` en lugar de `✓`/`✗` para evitar `UnicodeEncodeError` en PowerShell con `cp1252`.
- **webdriver-manager:** gestiona automáticamente la descarga del ChromeDriver compatible con la versión instalada de Chrome.
- **Robustez:** cada scraper tiene manejo de errores por sección — si una parte del sitio falla, el resto continúa y se reporta el error sin abortar.
