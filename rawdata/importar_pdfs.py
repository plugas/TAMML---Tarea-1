import os
from pypdf import PdfReader
from pdf2image import convert_from_path
import pytesseract

def extraer_texto_de_carpeta(carpeta_input, archivo_salida):
    contenido_total = []
    
    # Listar todos los archivos PDF en la carpeta
    archivos_pdf = [f for f in os.listdir(carpeta_input) if f.endswith('.pdf')]
    print(f"Se encontraron {len(archivos_pdf)} archivos para procesar.")

    for pdf in archivos_pdf:
        ruta_pdf = os.path.join(carpeta_input, pdf)
        print(f"Procesando: {pdf}...")
        
        texto_documento = f"\n--- ORIGEN: {pdf} ---\n"
        
        try:
            # 1. Intentar extracción de texto digital (Ideal para la convocatoria de la AGA)
            reader = PdfReader(ruta_pdf)
            texto_digital = ""
            for pagina in reader.pages:
                reserva_texto = pagina.extract_text()
                if reserva_texto:
                    texto_digital += reserva_texto + "\n"

            # 2. Validación: Si el texto extraído es suficiente (ej. > 100 caracteres)
            if len(texto_digital.strip()) > 100:
                print(f"Extracción digital exitosa para {pdf}.")
                texto_documento += texto_digital
            else:
                # 3. Solo si falla lo digital, intentar OCR (Requiere Poppler instalado)
                print(f"Texto insuficiente en {pdf}. Intentando OCR (Requiere Poppler)...")
                try:
                    imagenes = convert_from_path(ruta_pdf)
                    for img in imagenes:
                        texto_ocr = pytesseract.image_to_string(img, lang='spa')
                        texto_documento += texto_ocr + "\n"
                except Exception as e_ocr:
                    print(f"ALERTA: No se pudo realizar OCR en {pdf} porque Poppler no está configurado: {e_ocr}")
                    texto_documento += "\n[Error de OCR: Documento requiere Poppler para ser leído]\n"
            
            contenido_total.append(texto_documento)
            
        except Exception as e:
            print(f"Error crítico procesando {pdf}: {e}")

    # Guardar el insumo final para el chatbot
    with open(archivo_salida, "w", encoding="utf-8") as f:
        f.write("\n".join(contenido_total))
    
    print(f"\n¡Éxito! El contexto de Riopaila se ha guardado en: {archivo_salida}")

# --- CONFIGURACIÓN ---
# Coloca aquí la ruta de tu carpeta con los PDFs de Riopaila Castilla
ruta_pdfs = "F:\\OneDrive\\Documentos\\ESTUDIO\\Maestria Inteligencia Artificial\\Tecnicas avanzadas de IA aplicadas a modelos de lenguaje\\Tarea 1\\Valentina\\proyecto_chatbot\\PDFS SIMEV RIOAPILA" 
nombre_salida = "F:\\OneDrive\\Documentos\\ESTUDIO\\Maestria Inteligencia Artificial\\Tecnicas avanzadas de IA aplicadas a modelos de lenguaje\\Tarea 1\\contexto_riopaila_castilla2.txt"

extraer_texto_de_carpeta(ruta_pdfs, nombre_salida)