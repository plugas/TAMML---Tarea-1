import re

def limpiar_contexto_para_ia(archivo_entrada, archivo_salida):
    with open(archivo_entrada, "r", encoding="utf-8") as f:
        texto = f.read()

    # 1. Eliminar URLs (consumen muchos tokens y no aportan contenido)
    texto = re.sub(r'http\S+', '', texto)
    
    # 2. Eliminar múltiples saltos de línea y espacios
    texto = re.sub(r'\n\s*\n', '\n\n', texto)
    
    # 3. Eliminar caracteres especiales/emojis innecesarios
    texto = re.sub(r'[^\x00-\x7FáéíóúÁÉÍÓÚñÑ]+', ' ', texto)

    with open(archivo_salida, "w", encoding="utf-8") as f:
        f.write(texto)
    print("Archivo optimizado para velocidad.")

limpiar_contexto_para_ia('tu_archivo_riopaila.txt', 'contexto_optimizado.txt')