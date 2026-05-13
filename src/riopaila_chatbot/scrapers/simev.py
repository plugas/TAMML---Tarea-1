import hashlib
import os
import time
from pathlib import Path

import pandas as pd
import pdfplumber
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

REPORTS_DIR = Path(__file__).parent.parent.parent.parent / "reports"
PDFS_DIR = Path(__file__).parent.parent.parent.parent / "data" / "pdfs"


def _hash_archivo(ruta: Path) -> str:
    return hashlib.md5(ruta.read_bytes()).hexdigest()


def deduplicar_pdfs(carpeta: Path) -> None:
    """Elimina PDFs duplicados por contenido, conservando el de nombre más limpio."""
    hashes: dict[str, Path] = {}
    for pdf in sorted(carpeta.glob("*.pdf")):
        h = _hash_archivo(pdf)
        if h in hashes:
            existente = hashes[h]
            # Conservar el nombre más corto (sin sufijos como " (1)", "(003)")
            if len(pdf.stem) < len(existente.stem):
                existente.unlink()
                hashes[h] = pdf
                print(f"  Duplicado eliminado: {existente.name}")
            else:
                pdf.unlink()
                print(f"  Duplicado eliminado: {pdf.name}")
        else:
            hashes[h] = pdf
    print(f"PDFs únicos conservados: {len(hashes)}")


class ScraperSIMEV:

    def __init__(self):
        PDFS_DIR.mkdir(parents=True, exist_ok=True)

        options = Options()
        options.add_argument("--start-maximized")
        prefs = {
            "download.default_directory": str(PDFS_DIR),
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": True
        }
        options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(options=options)

        self.url = (
            "https://www.superfinanciera.gov.co/ReportesInformacionRelevante/faces/"
            "B_simevRelevantes/A_infoRelevante/repoInfoRelevante.xhtml"
            "?entidad=029&tipoEntidad=031"
        )
        self.data = []
        self.vistos = set()
        # Hashes de PDFs ya descargados en esta sesión para evitar duplicados al vuelo
        self._hashes_descargados: set[str] = set()

    def leer_pdf(self, ruta: Path) -> str:
        try:
            texto_total = ""
            with pdfplumber.open(ruta) as pdf:
                for pagina in pdf.pages:
                    texto = pagina.extract_text()
                    if texto:
                        texto_total += texto + "\n"
            return texto_total[:2000]
        except Exception as e:
            print("Error leyendo PDF:", e)
            return "Error leyendo PDF"

    def _registrar_pdf(self, pdf: Path) -> Path | None:
        """Devuelve la ruta del PDF si es único, o None si es duplicado (y lo borra)."""
        h = _hash_archivo(pdf)
        if h in self._hashes_descargados:
            pdf.unlink()
            print(f"  Duplicado descartado: {pdf.name}")
            return None
        self._hashes_descargados.add(h)
        return pdf

    def extraer_tabla(self):
        rows = self.driver.find_elements(By.XPATH, "//tbody/tr")
        print(f"Filas encontradas: {len(rows)}")

        for row in rows:
            try:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) < 5:
                    continue
                fecha = cols[0].text.strip()
                hora = cols[1].text.strip()
                tema = cols[2].text.strip()
                resumen = cols[3].text.strip()
                clave = f"{fecha}-{hora}-{tema}"
                if clave in self.vistos:
                    continue
                self.vistos.add(clave)

                pdf_local = None
                contenido_pdf = ""
                try:
                    boton = cols[4].find_element(By.TAG_NAME, "a")
                    antes = set(os.listdir(PDFS_DIR))
                    self.driver.execute_script("arguments[0].click();", boton)
                    time.sleep(5)
                    nuevos = set(os.listdir(PDFS_DIR)) - antes
                    if nuevos:
                        pdf_nuevo = PDFS_DIR / nuevos.pop()
                        pdf_local = self._registrar_pdf(pdf_nuevo)
                        if pdf_local:
                            contenido_pdf = self.leer_pdf(pdf_local)
                except Exception as e:
                    print("No se pudo abrir PDF:", e)

                print(f"{fecha} {hora} — {tema}")
                self.data.append({
                    "fecha": fecha,
                    "hora": hora,
                    "tema": tema,
                    "resumen": resumen,
                    "pdf_local": str(pdf_local) if pdf_local else "",
                    "contenido_pdf": contenido_pdf
                })
            except Exception as e:
                print("Error fila:", e)

    def siguiente_pagina(self) -> bool:
        try:
            boton = self.driver.find_element(By.XPATH, "//a[contains(text(),'Siguiente')]")
            self.driver.execute_script("arguments[0].click();", boton)
            time.sleep(6)
            return True
        except Exception:
            return False

    def scrapear(self):
        print("\nAbriendo SIMEV...\n")
        self.driver.get(self.url)
        time.sleep(10)
        pagina = 1
        while True:
            print(f"\nPágina {pagina}")
            self.extraer_tabla()
            if not self.siguiente_pagina():
                print("\nNo hay más páginas")
                break
            pagina += 1

    def guardar(self):
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        df = pd.DataFrame(self.data)
        csv_salida = REPORTS_DIR / "reporte_simev_riopaila.csv"
        df.to_csv(csv_salida, index=False, encoding="utf-8-sig")
        print(f"CSV generado: {csv_salida}")

        md_salida = REPORTS_DIR / "reporte_simev_riopaila.md"
        with open(md_salida, "w", encoding="utf-8") as f:
            f.write("# Riopaila Castilla — Hechos Relevantes SIMEV\n\n")
            for i, item in enumerate(self.data, 1):
                f.write(f"## Evento #{i}\n\n")
                f.write("| Campo | Valor |\n")
                f.write("|-------|-------|\n")
                f.write(f"| Fecha | {item['fecha']} |\n")
                f.write(f"| Hora  | {item['hora']} |\n")
                f.write(f"| Tema  | {item['tema']} |\n\n")
                f.write(f"**Resumen:** {item['resumen']}\n\n")
                if item["pdf_local"]:
                    f.write(f"**Documento:** `{item['pdf_local']}`\n\n")
                if item["contenido_pdf"]:
                    f.write("**Contenido del documento:**\n\n")
                    f.write(f"{item['contenido_pdf'][:800]}\n\n")
                f.write("---\n\n")
        print(f"Markdown generado: {md_salida}")

    def ejecutar(self):
        self.scrapear()
        print("\nDeduplicando PDFs descargados...")
        deduplicar_pdfs(PDFS_DIR)
        self.guardar()
        self.driver.quit()


if __name__ == "__main__":
    scraper = ScraperSIMEV()
    scraper.ejecutar()
