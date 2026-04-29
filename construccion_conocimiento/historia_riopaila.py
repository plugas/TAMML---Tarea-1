import requests
from bs4 import BeautifulSoup

def scrapear_historia_riopaila(url, archivo_salida):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        print(f"Conectando a: {url}...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # En la web de Riopaila, la historia suele estar en contenedores de 'timeline'
        # o dentro del contenido principal de la página.
        historia_completa = []
        historia_completa.append("--- HISTORIA DE RIOPAILA CASTILLA ---")

        # Buscamos el contenido principal (ajustado a la estructura típica de WordPress)
        contenido = soup.find_all(['h2', 'h3', 'p', 'span', 'li'])
        
        for elemento in contenido:
            texto = elemento.get_text().strip()
            if texto:
                historia_completa.append(texto)

        # Limpiar y guardar en archivo plano
        with open(archivo_salida, "w", encoding="utf-8") as f:
            f.write("\n".join(historia_completa))
        
        print(f"¡Éxito! Se ha guardado la historia en {archivo_salida}")

    except Exception as e:
        print(f"Error al scrapear: {e}")

# --- EJECUCIÓN ---
url_objetivo = "https://www.riopaila-castilla.com/nuestro-camino/"
archivo_txt = "C:\\Users\mrplu\OneDrive\Documentos\\ESTUDIO\Maestria Inteligencia Artificial\\Tecnicas avanzadas de IA aplicadas a modelos de lenguaje\\Tarea 1\\reporte_historia_riopaila.txt"

scrapear_historia_riopaila(url_objetivo, archivo_txt)