import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

REPORTS_DIR = Path(__file__).parent.parent.parent.parent / "reports"


class ScraperLinkedInPro:

    def __init__(self):
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        self.url = "https://www.linkedin.com/company/riopaila-castilla-s.-a./?originalSubdomain=co"
        self.resultados = []

    def login(self):
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(10)
        print("Inicia sesión y presiona ENTER...")
        input()

    def scrapear(self):
        print("\nExtrayendo LinkedIn...\n")
        self.driver.get("https://www.linkedin.com/company/riopaila-castilla-s.-a./")
        time.sleep(5)
        try:
            boton_posts = self.driver.find_element(By.XPATH, "//a[contains(@href,'/posts')]")
            boton_posts.click()
            time.sleep(5)
        except Exception:
            self.driver.get(self.url)
            time.sleep(5)

        self.driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(2)
        self.driver.execute_script("window.scrollBy(0, 800);")
        time.sleep(3)

        posts_unicos = set()
        for i in range(25):
            print(f"Scroll {i+1}")
            self.driver.execute_script("window.scrollBy(0, 1200);")
            time.sleep(3)
            posts = self.driver.find_elements(By.XPATH, "//div[contains(@class,'feed-shared-update-v2')]")
            if not posts:
                posts = self.driver.find_elements(By.XPATH, "//div[contains(@data-id,'urn:li:activity')]")

            for p in posts:
                try:
                    texto = p.text.strip()
                    if len(texto) < 50 or "Activar para ver" in texto or "Número de publicación" in texto:
                        continue
                    clave = texto[:200]
                    if clave not in posts_unicos:
                        posts_unicos.add(clave)
                        self.resultados.append({"red": "LinkedIn", "texto": texto, "url": self.url})
                except Exception:
                    continue

        print(f"\nTotal posts únicos: {len(self.resultados)}")

    def guardar(self):
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        salida = REPORTS_DIR / "reporte_linkedin_posts_riopaila.md"
        with open(salida, "w", encoding="utf-8") as f:
            f.write("# Riopaila Castilla — LinkedIn\n\n")
            for i, item in enumerate(self.resultados, 1):
                f.write(f"## Post {i}\n\n")
                f.write(f"> {item['texto']}\n\n")
                f.write(f"**Fuente:** {item['url']}\n\n")
                f.write("---\n\n")
        print(f"Archivo generado: {salida}")

    def ejecutar(self):
        self.login()
        self.scrapear()
        self.guardar()
        self.driver.quit()


if __name__ == "__main__":
    s = ScraperLinkedInPro()
    s.ejecutar()
