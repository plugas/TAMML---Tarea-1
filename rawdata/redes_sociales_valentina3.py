import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ScraperInstagramPro:

    def __init__(self):
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-gpu")
        options.add_argument("--log-level=3")
        
        # El driver se inicializa aquí
        self.driver = webdriver.Chrome(options=options)
        self.target_url = "https://www.instagram.com/plugas/"
        self.resultados = []

    def login_manual(self):
        print("\n🔐 Abriendo Instagram para login...")
        self.driver.get("https://www.instagram.com/")
        input("⏳ Inicia sesión en el navegador y presiona ENTER aquí cuando veas tu feed...")

    def recolectar_urls_posts(self, cantidad_objetivo=100):
        print(f"\n📸 Recolectando enlaces de posts (Objetivo: {cantidad_objetivo})...")
        self.driver.get(self.target_url)
        time.sleep(5)

        posts_urls = set()
        scrolls = 0
        
        # Scroll dinámico hasta alcanzar la cantidad deseada
        while len(posts_urls) < cantidad_objetivo and scrolls < 50:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            links = self.driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                href = link.get_attribute("href")
                if href and "/p/" in href:
                    url_limpia = href.split("?")[0]
                    posts_urls.add(url_limpia)
            
            scrolls += 1
            print(f"🔄 Scroll {scrolls} | Enlaces encontrados: {len(posts_urls)}")
        
        return list(posts_urls)[:cantidad_objetivo]

    def extraer_detalle_post(self, url):
        print(f"🔎 Analizando contenido: {url}")
        self.driver.get(url)
        time.sleep(5) # Tiempo vital para que carguen los comentarios dinámicos
        
        datos = {
            "url": url, 
            "texto_post": "Sin texto", 
            "likes": "0", 
            "comentarios": []
        }
        
        try:
            # 1. CAPTURA DEL TEXTO DEL POST (CAPTION)
            # El texto principal siempre es el primer elemento de la lista de comentarios
            try:
                caption_obj = self.driver.find_element(By.XPATH, "//div[@class='_a9zs']//span")
                datos["texto_post"] = caption_obj.text
            except:
                # Backup: Buscar por el tag h1 que Instagram usa para accesibilidad en el post
                try:
                    datos["texto_post"] = self.driver.find_element(By.TAG_NAME, "h1").text
                except: pass

            # 2. CAPTURA DE LIKES (CORRECCIÓN DEFINITIVA)
            try:
                # Buscamos el elemento que contiene "likes" o "reproducciones"
                likes_section = self.driver.find_element(By.XPATH, "//section//div[contains(@class, 'x1247guj')]//span")
                datos["likes"] = re.sub(r'\D', '', likes_section.text) # Solo números
            except: pass

            # 3. CAPTURA DE COMENTARIOS (TEXTO REAL)
            print("💬 Extrayendo comentarios...")
            comentarios_html = self.driver.find_elements(By.XPATH, "//div[@class='_a9zs']//span")
            
            # El primer elemento [0] suele ser el post, los demás son comentarios
            lista_temp = []
            for i, c in enumerate(comentarios_html):
                if i == 0: continue # Omitir el pie de foto
                texto_c = c.text.strip()
                if texto_c:
                    lista_temp.append(texto_c)
                
                if len(lista_temp) >= 10: break # Límite por post para evitar bloqueos
            
            datos["comentarios"] = lista_temp

        except Exception as e:
            print(f"⚠️ Error en estructura: {e}")
            
        return datos

    def guardar_resultados(self):
        # Veo que trabajas en tu carpeta de la Maestría, asegúrate que la ruta sea accesible
        ruta = "C:\\Users\\mrplu\\Downloads\\analisis_redes_riopaila.txt"
        
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                for i, item in enumerate(self.resultados, 1):
                    f.write(f"\n{'='*70}\n")
                    f.write(f"📌 POST #{i}\n")
                    f.write(f"🔗 URL: {item['url']}\n")
                    f.write(f"❤️ LIKES: {item['likes']}\n")
                    # Usamos len() de la lista de comentarios para evitar el KeyError
                    f.write(f"💬 TOTAL COMENTARIOS CAPTURADOS: {len(item['comentarios'])}\n")
                    f.write(f"📝 TEXTO DEL POST:\n{item['texto_post']}\n")
                    f.write("-" * 30 + "\n")
                    f.write("💬 DETALLE DE COMENTARIOS:\n")
                    for c in item['comentarios']:
                        f.write(f"  • {c}\n")
            print(f"✅ Archivo guardado correctamente en: {ruta}")
        except Exception as e:
            print(f"❌ Error al escribir el archivo: {e}")

    def ejecutar(self):
        self.login_manual()
        urls = self.recolectar_urls_posts(100)
        
        for url in urls:
            info = self.extraer_detalle_post(url)
            self.resultados.append(info)
            # Guardado incremental por seguridad
            if len(self.resultados) % 5 == 0:
                self.guardar_resultados()
        
        self.guardar_resultados()
        self.driver.quit()

if __name__ == "__main__":
    scraper = ScraperInstagramPro()
    scraper.ejecutar()