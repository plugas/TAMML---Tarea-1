import re
import time
from pathlib import Path
from difflib import SequenceMatcher
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

REPORTS_DIR = Path(__file__).parent.parent.parent.parent / "reports"


class WebScraperJerarquico:

    def __init__(self):
        self.base_url = "https://www.riopaila-castilla.com/nuestro-camino/"
        self.domain = urlparse(self.base_url).netloc
        self.menu = {}
        self.data = {}
        self.global_seen = set()
        self.global_seen_norm = set()

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        self.driver = webdriver.Chrome(options=options)

    def obtener_menu(self):
        print("Extrayendo menú...")
        try:
            res = requests.get(self.base_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            nav = soup.find("nav") or soup
            for link in nav.find_all("a", href=True):
                nombre = link.get_text().strip()
                url = urljoin(self.base_url, link["href"])
                if nombre and len(nombre) > 2 and self.domain in url:
                    self.menu[nombre] = url
                    self.data[nombre] = {}
            print("Menú detectado:")
            for k in self.menu:
                print(" -", k)
        except Exception as e:
            print("Error obteniendo menú:", e)

    def limpiar_texto(self, text):
        text = re.sub(r'\s+', ' ', text).strip()
        text = text.lower()
        text = re.sub(r'\.+$', '.', text)
        text = re.sub(r'(\d{4})([A-Za-zÁÉÍÓÚáéíóú])', r'\1 \2', text)
        text = re.sub(r'([A-Za-zÁÉÍÓÚáéíóú])(\d{4})', r'\1 \2', text)
        if not text.endswith("."):
            text += "."
        return text

    def texto_valido(self, text):
        if not text or len(text) < 20:
            return False
        t = text.lower()
        basura = ["cookies", "privacidad", "términos", "javascript", "modo", "pantalla",
                  "epilepsia", "tdah", "lector de pantalla", "seleccione una opción", "guía de lectura"]
        if any(b in t for b in basura):
            return False
        if re.search(r'(tel|línea|call center|dirección|carrera|#)', t):
            return False
        if re.search(r'(afirmó|dijo|señaló)', t):
            return False
        return True

    def es_similar(self, a, b):
        return SequenceMatcher(None, a, b).ratio()

    def manejar_duplicados(self, nuevo):
        nuevo = nuevo.strip().lower()
        for existente in list(self.global_seen_norm):
            if self.es_similar(nuevo, existente) > 0.90:
                if len(nuevo) > len(existente):
                    self.global_seen_norm.remove(existente)
                    self.global_seen_norm.add(nuevo)
                    return True
                else:
                    return False
        self.global_seen_norm.add(nuevo)
        return True

    def clasificar_tipo_texto(self, texto):
        t = texto.lower()
        if re.search(r'\d+', t):
            return "DATOS CLAVE"
        if any(p in t for p in ["empresa", "producción", "sostenibilidad", "historia", "energía", "proyectos"]):
            return "CONTENIDO PRINCIPAL"
        return "OTROS"

    def scrapear(self):
        for seccion, url in self.menu.items():
            print(f"\nProcesando: {seccion}")
            try:
                self.driver.get(url)
                time.sleep(5)
                botones = self.driver.find_elements(By.CSS_SELECTOR, ".bt_bb_accordion_item_title")
                for b in botones:
                    try:
                        self.driver.execute_script("arguments[0].click();", b)
                        time.sleep(0.3)
                    except Exception:
                        pass
                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()

                titulo_h1 = "GENERAL"
                titulo_h2 = None
                titulo_h3 = None

                for tag in soup.find_all(True):
                    texto = self.limpiar_texto(tag.get_text())
                    if not texto or len(texto) < 20:
                        continue
                    if tag.name == "h1":
                        titulo_h1 = texto.upper()
                        titulo_h2 = None
                        titulo_h3 = None
                        continue
                    elif tag.name == "h2":
                        titulo_h2 = texto.upper()
                        titulo_h3 = None
                        continue
                    elif tag.name == "h3":
                        titulo_h3 = texto.upper()
                        continue
                    if len(texto) > 2000:
                        continue
                    if not self.texto_valido(texto):
                        continue
                    if not self.manejar_duplicados(texto):
                        continue
                    tipo = self.clasificar_tipo_texto(texto)
                    nivel = titulo_h3 or titulo_h2 or titulo_h1
                    self.data.setdefault(seccion, {})
                    self.data[seccion].setdefault(nivel, {})
                    self.data[seccion][nivel].setdefault(tipo, [])
                    self.data[seccion][nivel][tipo].append(texto)
            except Exception as e:
                print("Error:", e)

    def guardar(self):
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        salida = REPORTS_DIR / "reporte_web_riopaila.md"
        with open(salida, "w", encoding="utf-8") as f:
            f.write("# Riopaila Castilla — Sitio Web Oficial\n\n")
            for seccion, subs in self.data.items():
                f.write(f"## {seccion.title()}\n\n")
                for sub, tipos in subs.items():
                    f.write(f"### {sub.title()}\n\n")
                    for tipo, textos in tipos.items():
                        if not textos:
                            continue
                        f.write(f"**{tipo}**\n\n")
                        for texto in textos:
                            f.write(f"- {texto}\n")
                        f.write("\n")
                f.write("---\n\n")
        print(f"Archivo generado: {salida}")


if __name__ == "__main__":
    scraper = WebScraperJerarquico()
    scraper.obtener_menu()
    scraper.scrapear()
    scraper.guardar()
    scraper.driver.quit()
