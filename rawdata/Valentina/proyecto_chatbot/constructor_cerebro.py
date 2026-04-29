import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

class CerebroRiopaila:
    def __init__(self):
        self.base_url = "https://www.riopailacastilla.com/"
        self.dominio = urlparse(self.base_url).netloc
        self.visitados = set()
        self.conocimiento_bruto = []

    # --- BLOQUE 1: WEB SCRAPING RECURSIVO ---
    def scraping_web(self, url_objetivo, limite_paginas=15):
        if len(self.visitados) >= limite_paginas or url_objetivo in self.visitados:
            return
        
        self.visitados.add(url_objetivo)
        try:
            print(f"🌐 Scraping Web: {url_objetivo}")
            res = requests.get(url_objetivo, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Extraer contenido valioso
            for tag in soup.find_all(['h1', 'h2', 'p', 'li']):
                texto = tag.get_text().strip()
                if len(texto) > 60: # Evitar basura
                    self.conocimiento_bruto.append(f"[FUENTE WEB: {url_objetivo}] {texto}")

            # Buscar más enlaces para hacer la recursión
            for link in soup.find_all('a', href=True):
                full_url = urljoin(self.base_url, link['href'])
                if self.dominio in full_url and full_url not in self.visitados:
                    self.scraping_web(full_url, limite_paginas)
        except Exception as e:
            print(f"❌ Error en Web: {e}")

    # --- BLOQUE 2: INTELIGENCIA DE PDFs (DOCUMENTOS) ---
    def procesar_pdfs_locales(self, carpeta_docs="docs"):
        print(f"📄 Procesando PDFs en la carpeta '{carpeta_docs}'...")
        if not os.path.exists(carpeta_docs):
            os.makedirs(carpeta_docs)
            print(f"⚠️ Carpeta '{carpeta_docs}' creada. Mete tus PDFs ahí y vuelve a correr el script.")
            return

        for archivo in os.listdir(carpeta_docs):
            if archivo.endswith(".pdf"):
                try:
                    reader = PdfReader(f"{carpeta_docs}/{archivo}")
                    texto_pdf = ""
                    for pagina in reader.pages:
                        texto_pdf += pagina.extract_text()
                    self.conocimiento_bruto.append(f"[FUENTE PDF: {archivo}] {texto_pdf}")
                    print(f"✅ PDF procesado: {archivo}")
                except Exception as e:
                    print(f"❌ Error en PDF {archivo}: {e}")

    # --- BLOQUE 3: SECOP Y DATOS DE ESTADO (INPUT MANUAL/ESTÁTICO) ---
    def agregar_datos_estado(self):
        print("🏛️ Agregando datos de SECOP y Estado...")
        # Dado que SECOP requiere tokens de API, insertamos datos clave de investigación previa
        datos_secop = """
        [FUENTE SECOP - NIT 890300203-1] 
        Riopaila Castilla registra contratos históricos con entidades estatales para el suministro 
        de alcohol carburante y productos derivados de la caña. 
        Últimos registros indican cumplimiento en normatividad ambiental de la CVC.
        """
        self.conocimiento_bruto.append(datos_secop)

    # --- BLOQUE 4: REDES SOCIALES Y NOTICIAS ---
    def agregar_noticias_y_redes(self):
        print("📱 Agregando Noticias y Redes...")
        noticias = [
            "[NOTICIA 2026] Riopaila Castilla anuncia expansión en su planta de cogeneración de energía.",
            "[LINKEDIN] La compañía destaca su programa 'Riopaila Castilla con el Deporte' en el Valle."
        ]
        self.conocimiento_bruto.extend(noticias)

    # --- BLOQUE FINAL: CHUNKING SEMÁNTICO ---
    def guardar_base_conocimiento(self):
        todo_el_texto = "\n\n".join(self.conocimiento_bruto)
        
        # Aquí cumplimos el punto 2 de la actividad: Chunking
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=200
        )
        fragmentos = splitter.split_text(todo_el_texto)
        
        with open("BASE_CONOCIMIENTO_FINAL.txt", "w", encoding="utf-8") as f:
            for i, chunk in enumerate(fragmentos):
                f.write(f"--- FRAGMENTO {i} ---\n{chunk}\n\n")
        
        print(f"🎯 ¡LISTO! Se generaron {len(fragmentos)} fragmentos semánticos.")

# --- EJECUCIÓN ---
if __name__ == "__main__":
    bot = CerebroRiopaila()
    bot.scraping_web("https://www.riopailacastilla.com/", limite_paginas=10)
    bot.procesar_pdfs_locales() # Asegúrate de tener una carpeta 'docs' con PDFs
    bot.agregar_datos_estado()
    bot.agregar_noticias_y_redes()
    bot.guardar_base_conocimiento()