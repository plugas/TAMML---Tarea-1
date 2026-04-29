import time
import re
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class ScraperRedesRiopaila:

    def __init__(self):
        options = Options()
        # options.add_argument("--headless")

        options.add_argument("--start-maximized")
        options.add_argument("--disable-gpu")
        options.add_argument("--log-level=3")

        self.driver = webdriver.Chrome(options=options)

        self.instagram_url = "https://www.instagram.com/riopailacastilla/"
        self.resultados = []

    # ==============================
    # LOGIN MANUAL
    # ==============================
    def login_instagram(self):
        print("\n🔐 Abriendo Instagram para login...\n")

        self.driver.get("https://www.instagram.com/")
        time.sleep(5)

        print("👉 Inicia sesión manualmente en el navegador")
        input("⏳ Presiona ENTER cuando ya estés logueado...")

    # ==============================
    # INSTAGRAM 
    # ==============================
    def scrapear_instagram(self):
        print("\n📸 Extrayendo Instagram (modo PRO)...\n")

        self.driver.get(self.instagram_url)
        time.sleep(5)

        # SCRAPING PROGRESIVO (NO TOCAR)
        posts = set()

        for i in range(20):
            print(f"🔄 Scroll {i+1}")

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            links = self.driver.find_elements(By.TAG_NAME, "a")

            for link in links:
                href = link.get_attribute("href")

                if href and "/p/" in href:
                    href = href.split("?")[0]
                    posts.add(href)

            print(f"📊 Posts acumulados: {len(posts)}")

        posts = list(posts)

        print(f"\n🔥 Total posts únicos: {len(posts)}")

        vistos = set()

        for i, post_url in enumerate(posts[:30]):

            if post_url in vistos:
                continue

            vistos.add(post_url)

            print(f"\n🔎 Post {i+1}")
            self.driver.get(post_url)
            time.sleep(3)

            texto = ""

            try:
                posibles = self.driver.find_elements(By.XPATH, "//span")

                candidatos = []

                for p in posibles:
                    t = p.text.strip()

                    if len(t) < 40:
                        continue
                    if "Español" in t:
                        continue
                    if "English" in t:
                        continue
                    if "http" in t:
                        continue
                    if "condiciones de uso" in t.lower():
                        continue
                    if "política de privacidad" in t.lower():
                        continue
                    if "entra para indicar" in t.lower():
                        continue
                    if len(t.split()) < 6:
                        continue

                    candidatos.append(t)

                if candidatos:
                    texto = max(candidatos, key=len)

            except:
                pass

            if not texto or len(texto.strip()) < 30:
                print("⚠️ Post sin texto útil, ignorado")
                continue

            print("📝 Texto:", texto[:200])
            print("🔗", post_url)

            self.resultados.append({
                "red": "Instagram",
                "texto": texto,
                "url": post_url
            })

        # ==============================
        # PERFIL 
        # ==============================
        try:
            self.driver.get(self.instagram_url)
            time.sleep(3)

            header = self.driver.find_element(By.TAG_NAME, "header")
            perfil_texto = header.text.strip()

            print("\n👤 PERFIL:")
            print(perfil_texto)

            # 🔥 LO PONEMOS AL INICIO
            self.resultados.insert(0, {
                "red": "Instagram - Perfil",
                "texto": perfil_texto,
                "url": self.instagram_url
            })

        except Exception as e:
            print("❌ Error perfil:", e)

    # ==============================
    # OTRAS REDES
    # ==============================
    def scrapear_links_basicos(self):
        print("\n🌐 Extrayendo otras redes...\n")

        redes = {
            "Facebook": "https://www.facebook.com/riopailacastilla/",
            "TikTok": "https://www.tiktok.com/@riopailacastilla",
            "X": "https://x.com/RioCas"
        }

        for nombre, url in redes.items():
            print(f"🔎 {nombre}")

            try:
                res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)

                title = ""
                match = re.search(r"<title>(.*?)</title>", res.text)
                if match:
                    title = match.group(1)

                print("📝", title)
                print("🔗", url)

                self.resultados.append({
                    "red": nombre,
                    "texto": title,
                    "url": url
                })

            except Exception as e:
                print("❌ Error:", e)

    # ==============================
    # GUARDAR
    # ==============================
    def guardar(self):
        print("\n💾 Guardando resultados...\n")

        with open("reporte_instagram_post_riopaila.txt", "w", encoding="utf-8") as f:

            for item in self.resultados:
                f.write(f"\n📌 {item['red']}\n")
                f.write(f"• {item['texto']}\n")
                f.write(f"🔗 {item['url']}\n")

        print("✅ Archivo generado: reporte_instagram_post_riopaila.txt")

    # ==============================
    # EJECUCIÓN
    # ==============================
    def ejecutar(self):
        self.login_instagram()
        self.scrapear_instagram()
        self.scrapear_links_basicos()
        self.guardar()
        self.driver.quit()


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    scraper = ScraperRedesRiopaila()
    scraper.ejecutar()