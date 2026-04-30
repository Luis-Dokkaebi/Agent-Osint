import os
import json
import time
import random
import requests
from datetime import datetime

# Lista de User-Agents genéricos para rotar
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/113.0"
]

def obtener_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json"
    }

def buscar_alias_pastebins(alias):
    """
    Realiza una búsqueda Dork automatizada usando la API de Google Custom Search.
    Busca el alias dentro de sitios de paste (pastebin.com, ghostbin.com).
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
    archivo_log = "cadena_custodia.log"

    registro = {
        "timestamp": timestamp,
        "alias_objetivo": alias,
        "accion": "busqueda_dorks",
        "sitios_encontrados": []
    }

    # Obtener credenciales del entorno
    api_key = os.environ.get("GOOGLE_API_KEY")
    cse_id = os.environ.get("GOOGLE_CSE_ID")

    if not api_key or not cse_id:
        mensaje_error = "Faltan credenciales de Google Custom Search. Debes establecer GOOGLE_API_KEY y GOOGLE_CSE_ID como variables de entorno."
        print(f"[!] {mensaje_error}")
        registro["estado"] = "error"
        registro["mensaje_error"] = mensaje_error
        _guardar_log(archivo_log, registro)
        return registro

    # Construir la consulta (Dork)
    dork_query = f'site:pastebin.com OR site:ghostbin.com "{alias}"'
    url = "https://www.googleapis.com/customsearch/v1"

    parametros = {
        "key": api_key,
        "cx": cse_id,
        "q": dork_query
    }

    intentos_maximos = 3
    retraso_base = 5  # Segundos

    for intento in range(intentos_maximos):
        try:
            print(f"[*] Ejecutando búsqueda Dork para '{alias}' (Intento {intento + 1})...")
            respuesta = requests.get(url, headers=obtener_headers(), params=parametros, timeout=10)

            if respuesta.status_code == 200:
                datos = respuesta.json()
                items = datos.get("items", [])

                if not items:
                    print(f"[-] No se encontraron menciones en pastebins para '{alias}'.")
                    registro["estado"] = "sin_resultados"
                else:
                    print(f"[+] Se encontraron posibles filtraciones o menciones:")
                    for item in items:
                        enlace = item.get("link")
                        titulo = item.get("title")
                        print(f"  -> {titulo}: {enlace}")
                        registro["sitios_encontrados"].append({"titulo": titulo, "url": enlace})
                    registro["estado"] = "exito"
                break  # Éxito, salir del bucle de reintentos

            elif respuesta.status_code == 429:
                # Rate limit excedido
                espera = retraso_base * (2 ** intento) # Backoff exponencial (5s, 10s, 20s...)
                print(f"[!] Límite de cuota de API excedido (HTTP 429). Esperando {espera} segundos antes de reintentar...")
                time.sleep(espera)
                if intento == intentos_maximos - 1:
                    registro["estado"] = "error"
                    registro["mensaje_error"] = "Se excedió el límite de cuota (Rate Limit) repetidamente."
            else:
                mensaje = f"Error en la API de Google: HTTP {respuesta.status_code} - {respuesta.text}"
                print(f"[x] {mensaje}")
                registro["estado"] = "error"
                registro["mensaje_error"] = mensaje
                break # Errores no relacionados con rate limit no se reintentan

        except requests.exceptions.RequestException as e:
            mensaje = f"Error de red al consultar la API: {e}"
            print(f"[x] {mensaje}")
            registro["estado"] = "error"
            registro["mensaje_error"] = mensaje
            break

    _guardar_log(archivo_log, registro)
    return registro

def _guardar_log(archivo, registro):
    with open(archivo, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro) + "\n")

if __name__ == "__main__":
    alias_test = input("Ingresa un alias de prueba para buscar en pastebins: ")
    if alias_test:
        resultado = buscar_alias_pastebins(alias_test.strip())
