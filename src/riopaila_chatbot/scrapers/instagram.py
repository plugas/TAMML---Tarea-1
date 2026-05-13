import re
import time
import requests
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

REPORTS_DIR = Path(__file__).parent.parent.parent.parent / "reports"


class ScraperRedesRiopaila:

    def __init__(self):
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-gpu")
        options.add_argument("--log-level=3")
        self.driver = webdriver.Chrome(options=options)
        self.instagram_url = "https://www.instagram.com/riopailacastilla/"
        self.resultados = []

    def login_instagram(self):
        print("\nAbriendo Instagram para login...\n")
        self.driver.get("https://www.instagram.com/")
        time.sleep(5)
        input("Inicia sesión manualmente en el navegador y presiona ENTER cuando estés logueado...")

    def scrapear_instagram(self):
        print("\nExtrayendo Instagram...\n")
        self.driver.get(self.instagram_url)
        time.sleep(5)

        posts = set()
        for i in range(20):
            print(f"Scroll {i+1}")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            for link in self.driver.find_elements(By.TAG_NAME, "a"):
                href = link.get_attribute("href")
                if href and "/p/" in href:
                    posts.add(href.split("?")[0])
            print(f"Posts acumulados: {len(posts)}")

        posts = list(posts)
        print(f"\nTotal posts únicos: {len(posts)}")
        vistos = set()

        for i, post_url in enumerate(posts[:30]):
            if post_url in vistos:
                continue
            vistos.add(post_url)
            self.driver.get(post_url)
            time.sleep(3)
            texto = ""
            try:
                candidatos = []
                for p in self.driver.find_elements(By.XPATH, "//span"):
                    t = p.text.strip()
                    if len(t) < 40 or len(t.split()) < 6:
                        continue
                    if any(x in t.lower() for x in ["español", "english", "http",
                                                      "condiciones de uso", "política de privacidad",
                                                      "entra para indicar"]):
                        continue
                    candidatos.append(t)
                if candidatos:
                    texto = max(candidatos, key=len)
            except Exception:
                pass

            if not texto or len(texto.strip()) < 30:
                continue

            self.resultados.append({"red": "Instagram", "texto": texto, "url": post_url})

        try:
            self.driver.get(self.instagram_url)
            time.sleep(3)
            header = self.driver.find_element(By.TAG_NAME, "header")
            perfil_texto = header.text.strip()
            self.resultados.insert(0, {
                "red": "Instagram - Perfil",
                "texto": perfil_texto,
                "url": self.instagram_url
            })
        except Exception as e:
            print("Error perfil:", e)

    def scrapear_otras_redes(self):
        print("\nExtrayendo otras redes...\n")
        redes = {
            "Facebook": "https://www.facebook.com/riopailacastilla/",
            "TikTok": "https://www.tiktok.com/@riopailacastilla",
            "X": "https://x.com/RioCas"
        }
        for nombre, url in redes.items():
            try:
                res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                match = re.search(r"<title>(.*?)</title>", res.text)
                title = match.group(1) if match else ""
                self.resultados.append({"red": nombre, "texto": title, "url": url})
            except Exception as e:
                print(f"Error {nombre}:", e)

    def guardar(self):
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        salida = REPORTS_DIR / "reporte_instagram_posts_riopaila.md"
        with open(salida, "w", encoding="utf-8") as f:
            f.write("# Riopaila Castilla — Redes Sociales\n\n")
            red_actual = None
            for i, item in enumerate(self.resultados, 1):
                if item["red"] != red_actual:
                    red_actual = item["red"]
                    f.write(f"## {red_actual}\n\n")
                f.write(f"### Publicación {i}\n\n")
                f.write(f"> {item['texto']}\n\n")
                f.write(f"**URL:** {item['url']}\n\n")
                f.write("---\n\n")
        print(f"Archivo generado: {salida}")

    def ejecutar(self):
        self.login_instagram()
        self.scrapear_instagram()
        self.scrapear_otras_redes()
        self.guardar()
        self.driver.quit()


if __name__ == "__main__":
    scraper = ScraperRedesRiopaila()
    scraper.ejecutar()
