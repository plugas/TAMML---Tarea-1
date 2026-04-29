import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class ScraperLinkedInPro:

    def __init__(self):
        options = Options()
        options.add_argument("--start-maximized")

        # 🔥 evitar detección básica
        options.add_argument("--disable-blink-features=AutomationControlled")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

        # 🔥 ocultar webdriver flag
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        self.url = "https://www.linkedin.com/company/riopaila-castilla-s.-a./?originalSubdomain=co"
        self.resultados = []

    # ==============================
    # 🔐 LOGIN
    # ==============================
    def login(self):
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(10)

        print("🔐 Inicia sesión y presiona ENTER...")
        input()

    # ==============================
    # 💼 SCRAPING PRO
    # ==============================
    def scrapear(self):
        print("\n💼 Extrayendo LinkedIn (modo PRO REAL)...\n")

        # 🔥 entrar primero al perfil (NO directo a posts)
        self.driver.get("https://www.linkedin.com/company/riopaila-castilla-s.-a./")
        time.sleep(5)

        # 🔥 click en pestaña posts
        try:
            boton_posts = self.driver.find_element(By.XPATH, "//a[contains(@href,'/posts')]")
            boton_posts.click()
            time.sleep(5)
        except:
            print("⚠️ No se pudo hacer click en posts, usando URL directa")
            self.driver.get(self.url)
            time.sleep(5)

        # 🔥 interacción humana inicial
        self.driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(2)
        self.driver.execute_script("window.scrollBy(0, 800);")
        time.sleep(3)

        posts_unicos = set()

        # ==============================
        # 🔄 SCROLL PROGRESIVO
        # ==============================
        for i in range(25):
            print(f"🔄 Scroll {i+1}")

            self.driver.execute_script("window.scrollBy(0, 1200);")
            time.sleep(3)

            # 🔥 selector principal
            posts = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'feed-shared-update-v2')]"
            )

            # 🔥 fallback si LinkedIn cambia estructura
            if len(posts) == 0:
                posts = self.driver.find_elements(
                    By.XPATH,
                    "//div[contains(@data-id,'urn:li:activity')]"
                )

            print(f"📦 Encontrados en DOM: {len(posts)}")

            for p in posts:
                try:
                    texto = p.text.strip()

                    if len(texto) < 50:
                        continue
                    if "Activar para ver" in texto:
                        continue
                    if "Número de publicación" in texto:
                        continue

                    clave = texto[:200]

                    if clave not in posts_unicos:
                        posts_unicos.add(clave)

                        print("📝", texto[:100])

                        self.resultados.append({
                            "red": "LinkedIn",
                            "texto": texto,
                            "url": self.url
                        })

                except:
                    continue

            print(f"📊 Posts acumulados: {len(self.resultados)}")

        print(f"\n🔥 Total posts únicos: {len(self.resultados)}")

    # ==============================
    # 💾 GUARDAR
    # ==============================
    def guardar(self):
        print("\n💾 Guardando...\n")

        with open("reporte_linkedin_posts_riopaila.txt", "w", encoding="utf-8") as f:

            for item in self.resultados:
                f.write("\n" + "=" * 70 + "\n")
                f.write(f"📌 {item['red']}\n\n")
                f.write(item["texto"] + "\n\n")
                f.write(f"🔗 {item['url']}\n")

        print("✅ Archivo generado: reporte_linkedin_posts_riopaila.txt")

    # ==============================
    # 🚀 EJECUCIÓN
    # ==============================
    def ejecutar(self):
        self.login()
        self.scrapear()
        self.guardar()
        self.driver.quit()


# ==============================
# ▶️ MAIN
# ==============================
if __name__ == "__main__":
    s = ScraperLinkedInPro()
    s.ejecutar()