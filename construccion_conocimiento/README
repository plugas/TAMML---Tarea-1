# Construcción de la Base de Conocimiento Semántico – Riopaila Castilla

## Descripción
Esta carpeta contiene el proceso de recolección, extracción, limpieza y estructuración de la información utilizada para construir la base de conocimiento del sistema Q&A de Riopaila Castilla.

El objetivo fue transformar información pública dispersa en diferentes fuentes digitales en un corpus estructurado en formato de texto plano, listo para ser utilizado como contexto en un modelo de lenguaje.

---

## Metodología aplicada

El proceso se desarrolló en cuatro fases principales:

### 1. Recolección de información (Web Scraping y fuentes digitales)
Se realizó extracción de información desde:

- Sitio web oficial de Riopaila Castilla
- Instagram corporativo (~100 publicaciones)
- LinkedIn (acceso mediante login manual y scroll automatizado)
- Plataforma SIMEV (documentos institucionales)

Se utilizaron herramientas como:
- Python
- Selenium
- Requests

---

### 2. Extracción de documentos PDF y OCR
Los documentos institucionales en formato PDF fueron procesados mediante:

- PyPDF para extracción de texto digital
- pdf2image + pytesseract para contenido basado en imágenes (OCR en español)

Esto permitió convertir contenido no estructurado en texto procesable.

---

### 3. Preprocesamiento y limpieza de datos
Se aplicaron técnicas de normalización:

- Eliminación de HTML
- Eliminación de caracteres especiales
- Eliminación de ruido del scraping
- Consolidación por fuente

Cada fuente fue almacenada en archivos `.txt` separados para trazabilidad.

---

### 4. Chunking y segmentación
El texto final fue segmentado en bloques semánticos mediante:

- Segmentación por tokens aproximados
- División por longitud de caracteres

Esto permitió preparar el contenido para su uso como contexto en modelos de lenguaje.

---

## Archivos incluidos

- `reporte_web_riopaila.txt`
- `reporte_instagram_post_riopaila.txt`
- `reporte_linkedin_post_riopaila.txt`
- `reporte_simev_riopaila.txt`
- `reportes_historia_riopaila.txt`
- `tu_archivo_riopaila.txt` (consolidado final)

---

## Limitaciones encontradas

- Variabilidad en la estructura de las fuentes web.
- Restricciones de acceso en LinkedIn (requiere login manual).
- Presencia de contenido no estructurado en PDFs (necesidad de OCR).
- Ruido en datos de redes sociales.

---

## 🎯 Resultado

Se logró construir una base de conocimiento unificada, limpia y estructurada, utilizada como input principal del sistema Q&A basado en LLM.
