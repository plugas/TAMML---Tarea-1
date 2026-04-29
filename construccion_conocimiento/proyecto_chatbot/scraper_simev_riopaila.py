import time
import os
import requests
import pandas as pd
import pdfplumber

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


class ScraperSIMEV:

    def __init__(self):

        self.carpeta_pdf = os.path.abspath("PDFS SIMEV RIOAPILA")

        if not os.path.exists(self.carpeta_pdf):
            os.makedirs(self.carpeta_pdf)

        options = Options()
        options.add_argument("--start-maximized")

        # 🔥 CONFIGURAR DESCARGA AUTOMÁTICA
        prefs = {
            "download.default_directory": self.carpeta_pdf,
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": True
        }
        options.add_experimental_option("prefs", prefs)

        self.driver = webdriver.Chrome(options=options)

        self.url = "https://www.superfinanciera.gov.co/ReportesInformacionRelevante/faces/B_simevRelevantes/A_infoRelevante/repoInfoRelevante.xhtml?entidad=029&tipoEntidad=031"

        self.data = []
        self.vistos = set()

    # ==============================
    # 🧠 LEER PDF
    # ==============================
    def leer_pdf(self, ruta):
        try:
            texto_total = ""

            with pdfplumber.open(ruta) as pdf:
                for pagina in pdf.pages:
                    texto = pagina.extract_text()
                    if texto:
                        texto_total += texto + "\n"

            return texto_total[:2000]

        except Exception as e:
            print("❌ Error leyendo PDF:", e)
            return "Error leyendo PDF"

    # ==============================
    # 📊 EXTRAER TABLA
    # ==============================
    def extraer_tabla(self):
        rows = self.driver.find_elements(By.XPATH, "//tbody/tr")

        print(f"📦 Filas encontradas: {len(rows)}")

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

                    antes = set(os.listdir(self.carpeta_pdf))

                    self.driver.execute_script("arguments[0].click();", boton)
                    time.sleep(5)

                    despues = set(os.listdir(self.carpeta_pdf))
                    nuevos = despues - antes

                    if nuevos:
                        archivo = nuevos.pop()
                        pdf_local = os.path.join(self.carpeta_pdf, archivo)

                        print(f"📥 PDF detectado: {archivo}")

                        contenido_pdf = self.leer_pdf(pdf_local)

                    else:
                        print("⚠️ No se detectó descarga")

                except Exception as e:
                    print("⚠️ No se pudo abrir PDF:", e)

                print(f"📅 {fecha} {hora}")
                print(f"🏷 {tema}")

                self.data.append({
                    "fecha": fecha,
                    "hora": hora,
                    "tema": tema,
                    "resumen": resumen,
                    "pdf_local": pdf_local,
                    "contenido_pdf": contenido_pdf
                })

            except Exception as e:
                print("❌ Error fila:", e)

    # ==============================
    # ▶️ SIGUIENTE PÁGINA
    # ==============================
    def siguiente_pagina(self):
        try:
            boton = self.driver.find_element(By.XPATH, "//a[contains(text(),'Siguiente')]")

            self.driver.execute_script("arguments[0].click();", boton)
            time.sleep(6)

            return True

        except:
            return False

    # ==============================
    # 🚀 SCRAPING
    # ==============================
    def scrapear(self):
        print("\n🌐 Abriendo SIMEV...\n")

        self.driver.get(self.url)
        time.sleep(10)

        pagina = 1

        while True:
            print(f"\n📄 Página {pagina}")

            self.extraer_tabla()

            if not self.siguiente_pagina():
                print("\n🚫 No hay más páginas")
                break

            pagina += 1

    # ==============================
    # 💾 GUARDAR CSV
    # ==============================
    def guardar(self):
        print("\n💾 Guardando CSV...\n")

        df = pd.DataFrame(self.data)
        df.to_csv("reporte_simev_riopaila.csv", index=False, encoding="utf-8-sig")

        print("✅ CSV generado")

        print("\n📈 Análisis:")
        print(df["tema"].value_counts())

    # ==============================
    # 📝 GUARDAR TXT ORGANIZADO
    # ==============================
    def guardar_txt(self):
        print("\n📝 Generando TXT organizado...\n")

        with open("reporte_simev_riopaila.txt", "w", encoding="utf-8") as f:

            for i, item in enumerate(self.data, 1):

                f.write("="*70 + "\n")
                f.write(f"📌 EVENTO #{i}\n\n")

                f.write(f"📅 Fecha: {item['fecha']}\n")
                f.write(f"🕒 Hora: {item['hora']}\n")
                f.write(f"🏷 Tema: {item['tema']}\n\n")

                f.write("📝 Resumen:\n")
                f.write(item['resumen'] + "\n\n")

                f.write("📄 PDF:\n")
                f.write(str(item['pdf_local']) + "\n\n")

                f.write("📖 Contenido (extracto):\n")

                if item['contenido_pdf']:
                    f.write(item['contenido_pdf'][:800] + "\n")
                else:
                    f.write("Sin contenido\n")

                f.write("\n")

        print("✅ TXT generado: reporte_simev_riopaila.txt")

    # ==============================
    # ▶️ EJECUTAR
    # ==============================
    def ejecutar(self):
        self.scrapear()
        self.guardar()
        self.guardar_txt()   # 🔥 NUEVO
        self.driver.quit()


# ==============================
# ▶️ MAIN
# ==============================
if __name__ == "__main__":
    scraper = ScraperSIMEV()
    scraper.ejecutar()