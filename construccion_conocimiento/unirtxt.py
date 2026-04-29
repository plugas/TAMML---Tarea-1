import os

# Lista de archivos a unir
# path_trabajo = 'F:\\OneDrive\\Documentos\\ESTUDIO\\Maestria Inteligencia Artificial\\Tecnicas avanzadas de IA aplicadas a modelos de lenguaje\\Tarea 1'
path_trabajo = 'C:\\Users\mrplu\\OneDrive\\Documentos\\ESTUDIO\Maestria Inteligencia Artificial\\Tecnicas avanzadas de IA aplicadas a modelos de lenguaje\\Tarea 1'
archivos_insumo = [
    'reporte_web_riopaila.txt',
    'reporte_linkedin_posts_riopaila.txt',
    'reporte_simev_riopaila.txt',
    'contexto_riopaila_castilla2.txt',
    'reporte_historia_riopaila.txt'
]

archivo_final = 'tu_archivo_riopaila.txt'

def consolidar_contexto(lista_archivos, salida):
    with open(path_trabajo + '\\' +salida, 'w', encoding='utf-8') as outfile:
        for nombre_archivo in lista_archivos:
            if os.path.exists(path_trabajo + '\\' + nombre_archivo):
                with open(path_trabajo + '\\' + nombre_archivo, 'r', encoding='utf-8') as infile:
                    # Añadimos un encabezado para separar las fuentes
                    outfile.write(f"\n{'='*30}\n")
                    outfile.write(f"FUENTE: {nombre_archivo}\n")
                    outfile.write(f"{'='*30}\n\n")
                    
                    # Escribimos el contenido
                    outfile.write(infile.read())
                    outfile.write("\n")
                print(f"Agregado: {nombre_archivo}")
            else:
                print(f"Advertencia: No se encontró el archivo {nombre_archivo}")

    print(f"\nProceso terminado. Archivo final creado: {salida}")

# Ejecutar la unión
consolidar_contexto(archivos_insumo, archivo_final)