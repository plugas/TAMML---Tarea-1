# Módulo: scraper_web.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class RiopailaWebScraper:
    def __init__(self):
        self.base_url = "https://www.riopailacastilla.com/"
        self.dominio = urlparse(self.base_url).netloc
        self.visitados = set()

    def extraer(self, url):
        if url in self.visitados or not self.es_interna(url):
            return ""
        
        self.visitados.add(url)
        try:
            res = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(res.text, 'html.parser')
            # Extraemos títulos y párrafos con sentido
            textos = [tag.get_text().strip() for tag in soup.find_all(['h1', 'h2', 'p']) if len(tag.get_text()) > 50]
            return "\n".join(textos)
        except:
            return ""

    def es_interna(self, url):
        return urlparse(url).netloc == self.dominio