
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from difflib import SequenceMatcher
import re


class WebScraperJerarquico:

    def __init__(self):
        self.base_url = "https://www.riopaila-castilla.com/nuestro-camino/"
        self.domain = urlparse(self.base_url).netloc
        self.menu = {}
        self.data = {}
        self.global_seen = set()
        self.global_seen_norm = set()

        # Selenium 
        options = Options()
        options.add_argument("--headless")  # quítalo si quieres ver el navegador
        options.add_argument("--disable-gpu")

        self.driver = webdriver.Chrome(options=options)
    # ==============================
    # 🔍 EXTRAER MENÚ
    # ==============================
    def obtener_menu(self):
        print("🔎 Extrayendo menú...")

        try:
            res = requests.get(self.base_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")

            nav = soup.find("nav") or soup
            links = nav.find_all("a", href=True)

            for link in links:
                nombre = link.get_text().strip()
                url = urljoin(self.base_url, link["href"])

                if nombre and len(nombre) > 2 and self.domain in url:
                    self.menu[nombre] = url
                    self.data[nombre] = {}

            print("✅ Menú detectado:")
            for k in self.menu:
                print(" -", k)

        except Exception as e:
            print("❌ Error obteniendo menú:", e)

    # ==============================
    # 🧹 LIMPIEZA
    # ==============================
    def limpiar_texto(self, text):
        text = re.sub(r'\s+', ' ', text).strip()

        # normalización para evitar duplicados
        text = text.lower()

        # quitar puntos repetidos al final
        text = re.sub(r'\.+$', '.', text)

        # separar números pegados
        text = re.sub(r'(\d{4})([A-Za-zÁÉÍÓÚáéíóú])', r'\1 \2', text)
        text = re.sub(r'([A-Za-zÁÉÍÓÚáéíóú])(\d{4})', r'\1 \2', text)

        if not text.endswith("."):
            text += "."

        return text

    def texto_valido(self, text):
        if not text or len(text) < 20:
            return False

        t = text.lower()

        basura = [
            "cookies", "privacidad", "términos",
            "javascript", "modo", "pantalla",
            "epilepsia", "tdah", "lector de pantalla",
            "seleccione una opción", "guía de lectura"
        ]

        if any(b in t for b in basura):
            return False

        # eliminar contactos
        if re.search(r'(tel|línea|call center|dirección|carrera|#)', t):
            return False

        # eliminar citas de personas
        if re.search(r'(afirmó|dijo|señaló)', t):
            return False

        return True
    


    def es_similar(self, a, b):
        return SequenceMatcher(None, a, b).ratio()

    def manejar_duplicados(self, nuevo):
        nuevo = nuevo.strip().lower()

        for existente in list(self.global_seen_norm):

            similitud = self.es_similar(nuevo, existente)

            # 🔥 solo si son casi iguales
            if similitud > 0.90:
                # conservar el más completo
                if len(nuevo) > len(existente):
                    self.global_seen_norm.remove(existente)
                    self.global_seen_norm.add(nuevo)
                    return True
                else:
                    return False

        self.global_seen_norm.add(nuevo)
        return True

    # ==============================
    # 🧠 CLASIFICACIÓN SEMÁNTICA
    # ==============================
    def clasificar_tipo_texto(self, texto):
        t = texto.lower()

        if re.search(r'\d+', t):
            return "DATOS CLAVE"

        if any(p in t for p in [
            "empresa", "producción", "sostenibilidad",
            "historia", "energía", "proyectos"
        ]):
            return "CONTENIDO PRINCIPAL"

        return "OTROS"

    # ==============================
    # 🧠 ORDEN CRONOLÓGICO
    # ==============================
    def ordenar_por_año(self, textos):
        def extraer_año(t):
            match = re.search(r'\b(19|20)\d{2}\b', t)
            return int(match.group()) if match else 0

        return sorted(textos, key=extraer_año)

    # ==============================
    # 🌐 SCRAPING (SELENIUM FULL)
    # ==============================
    def scrapear(self):

        for seccion, url in self.menu.items():
            print(f"\n🌐 Procesando: {seccion}")

            try:
                # 🔥 CARGA CON SELENIUM (JS INCLUIDO)
                self.driver.get(url)
                time.sleep(5)

                # 🔥 intentar expandir acordeones / botones
                botones = self.driver.find_elements(By.CSS_SELECTOR, ".bt_bb_accordion_item_title")
                for b in botones:
                    try:
                        self.driver.execute_script("arguments[0].click();", b)
                        time.sleep(0.3)
                    except:
                        pass

                soup = BeautifulSoup(self.driver.page_source, "html.parser")

                # 🧹 limpiar DOM
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()

                # ==============================
                # 🔗 EXTRAER LINKS IMPORTANTES
                # ==============================
                for link in soup.find_all("a", href=True):

                    texto = self.limpiar_texto(link.get_text())
                    href = urljoin(self.base_url, link["href"])

                    parsed = urlparse(href)

                    if not texto or len(texto) < 15:
                        continue

                    if any(x in texto for x in ["leer más", "ver más", "clic aquí"]):
                        continue

                    # 🔥 permitir subdominios (trabaja con nosotros, etc)
                    if self.domain not in parsed.netloc:
                        continue

                    texto_completo = f"{texto} ({href})"

                    if not self.texto_valido(texto):
                        continue

                    if not self.manejar_duplicados(texto_completo):
                        continue

                    self.data.setdefault(seccion, {})
                    self.data[seccion].setdefault("ENLACES", {})
                    self.data[seccion]["ENLACES"].setdefault("DATOS CLAVE", [])

                    if texto_completo not in self.data[seccion]["ENLACES"]["DATOS CLAVE"]:
                        self.data[seccion]["ENLACES"]["DATOS CLAVE"].append(texto_completo)

                # ==============================
                # 📄 EXTRAER PDFs
                # ==============================
                for link in soup.find_all("a", href=True):

                    href = urljoin(self.base_url, link["href"])

                    if ".pdf" not in href.lower():
                        continue

                    texto = self.limpiar_texto(link.get_text())

                    if not texto or len(texto) < 5:
                        texto = href.split("/")[-1]

                    texto_completo = f"{texto} ({href})"

                    if not self.manejar_duplicados(texto_completo):
                        continue

                    self.data.setdefault(seccion, {})
                    self.data[seccion].setdefault("PDFs", {})
                    self.data[seccion]["PDFs"].setdefault("DATOS CLAVE", [])

                    if texto_completo not in self.data[seccion]["PDFs"]["DATOS CLAVE"]:
                        self.data[seccion]["PDFs"]["DATOS CLAVE"].append(texto_completo)

                # ==============================
                # 🧩 TARJETAS (CARDS)
                # ==============================
                for card in soup.find_all("div", class_="bt_bb_card_image_title"):

                    titulo = self.limpiar_texto(card.get_text())
                    contenido_div = card.find_next("div", class_="bt_bb_card_image_text")

                    if not contenido_div:
                        continue

                    contenido = self.limpiar_texto(contenido_div.get_text())
                    texto_completo = f"{titulo}: {contenido}"

                    if not self.texto_valido(texto_completo):
                        continue

                    if not self.manejar_duplicados(texto_completo):
                        continue

                    tipo = self.clasificar_tipo_texto(texto_completo)

                    self.data.setdefault(seccion, {})
                    self.data[seccion].setdefault("GENERAL", {})
                    self.data[seccion]["GENERAL"].setdefault(tipo, [])

                    self.data[seccion]["GENERAL"][tipo].append(texto_completo)

                # ==============================
                # 🔥 JERARQUÍA (SIN PERDER INFO)
                # ==============================
                titulo_h1 = "GENERAL"
                titulo_h2 = None
                titulo_h3 = None

                for tag in soup.find_all(True):  # 🔥 TODOS LOS TAGS

                    texto = self.limpiar_texto(tag.get_text())

                    if not texto or len(texto) < 20:
                        continue

                    # 📌 títulos reales
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

                    # 🔥 AQUÍ ESTABA TU PROBLEMA:
                    # ❌ eliminabas div y span → perdías contenido
                    # ✅ ahora los dejamos pasar con control

                    # evitar bloques gigantes repetidos
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
                print("❌ Error:", e)
    # ==============================
    # 💾 GUARDAR
    # ==============================
    def guardar(self):
        with open("reporte_web_riopaila.txt", "w", encoding="utf-8") as f:

            for seccion, subs in self.data.items():
                f.write(f"\n\n📁 {seccion.upper()}\n")

                for sub, tipos in subs.items():
                    f.write(f"\n   ├── {sub.title()}\n")

                    for tipo, textos in tipos.items():

                        if not textos:
                            continue

                        f.write(f"\n   │   ▸ {tipo}\n")

                        textos_ordenados = (textos)

                        for texto in textos_ordenados:

                            f.write(f"   │     • {texto}\n")

                f.write("\n" + "─"*50 + "\n")

        print("\n✅ Archivo generado: reporte_web_riopaila.txt")


# ==============================
# 🚀 EJECUCIÓN
# ==============================
if __name__ == "__main__":
    scraper = WebScraperJerarquico()

    scraper.obtener_menu()
    scraper.scrapear()
    scraper.guardar()