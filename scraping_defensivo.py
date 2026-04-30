import os
import time
import base64
import logging
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup

# Configurar el logger
logging.basicConfig(
    filename='reporte_reputacion.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger('').addHandler(console_handler)


def extraer_urls_externas(url_perfil):
    """
    Descarga el HTML del perfil y extrae únicamente las URLs externas.
    """
    try:
        response = requests.get(url_perfil, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Error al descargar la página del perfil {url_perfil}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    enlaces = soup.find_all('a')

    dominio_base = urlparse(url_perfil).netloc

    urls_externas = set()

    for enlace in enlaces:
        href = enlace.get('href')
        if not href:
            continue

        # Convertir URLs relativas a absolutas para poder analizarlas
        href_absoluto = urljoin(url_perfil, href)
        parsed_href = urlparse(href_absoluto)

        # Filtrar: Nos interesan protocolos HTTP/HTTPS y dominios distintos al base
        if parsed_href.scheme in ('http', 'https'):
            if parsed_href.netloc and parsed_href.netloc != dominio_base:
                urls_externas.add(href_absoluto)

    return list(urls_externas)


def consultar_virustotal(url):
    """
    Consulta la URL en VirusTotal usando la API v3 y retorna el resultado de reputación.
    """
    api_key = os.environ.get("VIRUSTOTAL_API_KEY")
    if not api_key:
        logging.error("No se encontró la clave VIRUSTOTAL_API_KEY en las variables de entorno.")
        return None

    # VirusTotal v3 URL API requiere codificar la URL en base64 sin padding para el ID
    url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
    api_url = f"https://www.virustotal.com/api/v3/urls/{url_id}"

    headers = {
        "accept": "application/json",
        "x-apikey": api_key
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=10)

        if response.status_code == 404:
            logging.info(f"URL no encontrada en VirusTotal (nunca escaneada): {url}")
            return {"status": "unscanned", "malicious": 0, "suspicious": 0, "harmless": 0, "undetected": 0}

        response.raise_for_status()

        data = response.json()
        stats = data.get('data', {}).get('attributes', {}).get('last_analysis_stats', {})

        return {
            "status": "scanned",
            "malicious": stats.get('malicious', 0),
            "suspicious": stats.get('suspicious', 0),
            "harmless": stats.get('harmless', 0),
            "undetected": stats.get('undetected', 0)
        }

    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            logging.error(f"Rate limit excedido en VirusTotal al consultar {url}.")
        else:
            logging.error(f"Error HTTP al consultar VirusTotal para {url}: {e}")
        return None
    except requests.RequestException as e:
        logging.error(f"Error de conexión con VirusTotal para {url}: {e}")
        return None


def analizar_perfil(url_perfil):
    """
    Función principal que orquesta la extracción y el análisis de reputación.
    """
    logging.info(f"Iniciando análisis del perfil: {url_perfil}")

    urls_externas = extraer_urls_externas(url_perfil)

    if not urls_externas:
        logging.info("No se encontraron URLs externas en el perfil.")
        return

    logging.info(f"Se encontraron {len(urls_externas)} URLs externas. Iniciando validación en VirusTotal...")

    resultados = {}

    for i, url in enumerate(urls_externas):
        logging.info(f"Consultando [{i+1}/{len(urls_externas)}]: {url}")

        resultado = consultar_virustotal(url)
        resultados[url] = resultado

        if resultado and resultado.get("status") == "scanned":
            mal = resultado.get("malicious", 0)
            susp = resultado.get("suspicious", 0)
            if mal > 0 or susp > 0:
                logging.warning(f"¡ALERTA! URL potencialmente peligrosa: {url} (Malicious: {mal}, Suspicious: {susp})")
            else:
                logging.info(f"URL limpia: {url}")

        # Manejo de Rate Limit (4 peticiones por minuto en la capa gratuita)
        # 60 segundos / 4 requests = 15 segundos entre requests, por seguridad usamos 16s.
        # No esperamos después del último request
        if i < len(urls_externas) - 1:
            espera = 16
            logging.info(f"Esperando {espera} segundos para respetar el Rate Limit de VirusTotal...")
            time.sleep(espera)

    logging.info("Análisis de perfil finalizado.")
    return resultados

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        analizar_perfil(sys.argv[1])
    else:
        print("Uso: python scraping_defensivo.py <URL_DEL_PERFIL>")
