import io
import json
import requests
from datetime import datetime
from PIL import Image, ExifTags

def convertir_a_grados_decimales(coordenadas, referencia):
    """
    Convierte tuplas de grados, minutos y segundos a formato decimal para Maps.
    """
    if not coordenadas or not referencia:
        return None

    grados, minutos, segundos = coordenadas

    # En versiones viejas de Pillow, los valores pueden ser IFDRational (que actúan como fracciones o tuplas)
    grados = float(grados)
    minutos = float(minutos)
    segundos = float(segundos)

    decimal = grados + (minutos / 60.0) + (segundos / 3600.0)

    # Si la referencia es Sur u Oeste, el valor es negativo
    if referencia in ['S', 'W']:
        decimal = -decimal

    return decimal

def extraer_gps_info(exif_raw):
    """
    Busca y extrae la información GPS utilizando el método IFD moderno de Pillow.
    """
    try:
        gps_ifd = exif_raw.get_ifd(ExifTags.IFD.GPSInfo)
    except Exception:
        # En caso de versiones antiguas o problemas extrayendo el IFD
        gps_ifd = None

    if not gps_ifd:
        return None

    gps_data = {}
    for tag, value in gps_ifd.items():
        tag_name = ExifTags.GPSTAGS.get(tag, tag)
        gps_data[tag_name] = value

    latitud_coordenadas = gps_data.get('GPSLatitude')
    latitud_referencia = gps_data.get('GPSLatitudeRef')
    longitud_coordenadas = gps_data.get('GPSLongitude')
    longitud_referencia = gps_data.get('GPSLongitudeRef')

    if latitud_coordenadas and latitud_referencia and longitud_coordenadas and longitud_referencia:
        lat_decimal = convertir_a_grados_decimales(latitud_coordenadas, latitud_referencia)
        lon_decimal = convertir_a_grados_decimales(longitud_coordenadas, longitud_referencia)
        return {
            "latitud": round(lat_decimal, 6),
            "longitud": round(lon_decimal, 6),
            "maps_url": f"https://www.google.com/maps?q={lat_decimal},{lon_decimal}"
        }

    return None

def analizar_exif_imagen(url, timeout=10):
    """
    Descarga una imagen en memoria desde una URL directa, valida que sea una imagen,
    extrae sus metadatos EXIF (Marca, Modelo, y GPS) y registra los resultados forenses.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
    archivo_log = "cadena_custodia.log"

    registro = {
        "timestamp": timestamp,
        "url": url,
        "accion": "analisis_exif",
        "hallazgos": {}
    }

    try:
        # Petición HTTP usando streaming para no cargar todo de golpe antes de validar
        respuesta = requests.get(url, stream=True, timeout=timeout)
        respuesta.raise_for_status() # Lanza excepción si el status no es 200

        # Validar Content-Type
        content_type = respuesta.headers.get("Content-Type", "")
        if not content_type.startswith("image/"):
            raise ValueError(f"La URL no apunta a una imagen válida. Content-Type: {content_type}")

        # Descargar el resto a memoria (io.BytesIO)
        imagen_bytes = io.BytesIO(respuesta.content)
        imagen = Image.open(imagen_bytes)

        # Extraer EXIF
        exif_raw = imagen.getexif()
        if not exif_raw:
             print("[!] No se encontraron metadatos EXIF en la imagen. Probablemente han sido limpiados por la red social.")
             registro["estado"] = "sin_exif"
        else:
             print("[+] Metadatos EXIF encontrados. Analizando...")
             # Convertir las etiquetas (tags) crudas a sus nombres legibles
             exif_data = {}
             for tag, value in exif_raw.items():
                 tag_name = ExifTags.TAGS.get(tag, tag)
                 exif_data[tag_name] = value

             # Buscar Marca y Modelo
             marca = exif_data.get('Make')
             modelo = exif_data.get('Model')
             gps_info = extraer_gps_info(exif_raw)

             hay_hallazgos_relevantes = False

             if marca or modelo:
                 hay_hallazgos_relevantes = True
                 registro["hallazgos"]["camara"] = {"marca": str(marca).strip(), "modelo": str(modelo).strip()}
                 print(f"  [-] Cámara: Marca: {marca} | Modelo: {modelo}")

             if gps_info:
                 hay_hallazgos_relevantes = True
                 registro["hallazgos"]["gps"] = gps_info
                 print(f"  [-] Coordenadas GPS: {gps_info['latitud']}, {gps_info['longitud']}")
                 print(f"  [-] Ver en Maps: {gps_info['maps_url']}")

             if not hay_hallazgos_relevantes:
                 print("[!] Se encontraron metadatos, pero no contienen información de Cámara ni de GPS (pueden ser resolución, software, etc).")
                 registro["estado"] = "exif_sin_datos_relevantes"
             else:
                 registro["estado"] = "exito"

    except requests.exceptions.RequestException as e:
        print(f"[x] Error de conexión al intentar descargar la imagen: {e}")
        registro["estado"] = "error"
        registro["mensaje_error"] = f"Error de conexion: {e}"
    except Exception as e:
        print(f"[x] Error durante el análisis EXIF: {e}")
        registro["estado"] = "error"
        registro["mensaje_error"] = str(e)

    # Guardar en la cadena de custodia
    with open(archivo_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro) + "\n")

    return registro

if __name__ == "__main__":
    # Una URL de prueba (esta imagen probablemente no tenga EXIF, pero sirve para probar la lógica de descarga)
    url_test = "https://github.com/fluidicon.png"
    print(f"=== Prueba de Analizador EXIF en {url_test} ===")
    analizar_exif_imagen(url_test)
