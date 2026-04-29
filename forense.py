import os
import json
import hashlib
from datetime import datetime
from playwright.sync_api import sync_playwright

def calcular_sha256(filepath):
    """Calcula el hash SHA-256 de un archivo dado."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Lee el archivo en bloques para no saturar memoria en archivos grandes
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def preservar_evidencia(url):
    """
    Toma una captura de pantalla completa de una URL dada, guarda la imagen
    en la carpeta 'evidencia_forense', calcula su hash SHA-256 y guarda
    un registro estructurado en 'cadena_custodia.log'
    """
    carpeta_evidencia = "evidencia_forense"
    archivo_log = "cadena_custodia.log"

    # Crear carpeta si no existe
    if not os.path.exists(carpeta_evidencia):
        os.makedirs(carpeta_evidencia)

    # Generar timestamp para el nombre de archivo y el registro
    # Formato: YYYY-MM-DD_HH-MM-SS_microsegundos para evitar colisiones
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
    nombre_archivo = f"captura_{timestamp}.png"
    ruta_imagen = os.path.join(carpeta_evidencia, nombre_archivo)

    registro = {
        "timestamp": timestamp,
        "url": url,
        "accion": "preservar_evidencia",
    }

    try:
        with sync_playwright() as p:
            # Lanzar el navegador en modo headless
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                # Agregar user agent para simular navegación real
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # Navegar a la URL esperando hasta que se cargue la página
            page.goto(url, wait_until="networkidle", timeout=30000)

            # Tomar la captura de pantalla completa
            page.screenshot(path=ruta_imagen, full_page=True)

            # Cerrar el navegador
            browser.close()

        # Calcular el hash de la imagen guardada
        hash_sha256 = calcular_sha256(ruta_imagen)

        # Actualizar el registro con éxito
        registro["estado"] = "exito"
        registro["archivo_evidencia"] = ruta_imagen
        registro["sha256"] = hash_sha256

    except Exception as e:
        # Actualizar el registro con error
        registro["estado"] = "error"
        registro["mensaje_error"] = str(e)

    # Guardar el registro en el archivo de log (usando JSON lines para estructura y agregar secuencialmente)
    with open(archivo_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro) + "\n")

    return registro

if __name__ == "__main__":
    # Prueba rápida del archivo
    print("Probando función forense en https://example.com")
    resultado = preservar_evidencia("https://example.com")
    print(json.dumps(resultado, indent=2))
