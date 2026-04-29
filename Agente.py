import requests
import time

def buscar_alias(alias):
    """
    Busca la existencia de un alias en distintas plataformas públicas evaluando
    los códigos de respuesta HTTP.
    """
    # Diccionario de plataformas. Se usan endpoints públicos que tienden a no bloquear
    # la verificación de existencia a la primera.
    # Nota sobre Instagram/Facebook: Estas plataformas tienen sistemas antibot agresivos
    # que a menudo devuelven código 200 (pantalla de login) o 429, por lo que es 
    # mejor depender de APIs oficiales o herramientas especializadas para ellas.
    plataformas = {
        "GitHub": f"https://github.com/{alias}",
        "Reddit": f"https://www.reddit.com/user/{alias}/about.json",
        "Vimeo": f"https://vimeo.com/{alias}",
        "Patreon": f"https://www.patreon.com/{alias}",
        "Linktree": f"https://linktr.ee/{alias}",
        "SoundCloud": f"https://soundcloud.com/{alias}"
    }

    # Header para simular que la petición viene de un navegador web real
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    resultados = {}
    print(f"[*] Iniciando fase de reconocimiento para el alias: '{alias}'...\n")

    for nombre_sitio, url in plataformas.items():
        try:
            # Se realiza la petición GET con un tiempo límite de espera
            respuesta = requests.get(url, headers=headers, timeout=5)
            
            # Evaluación del código de estado
            if respuesta.status_code == 200:
                print(f"[+] ENCONTRADO en {nombre_sitio}: {url}")
                resultados[nombre_sitio] = url
            elif respuesta.status_code == 404:
                print(f"[-] No encontrado en {nombre_sitio}")
            else:
                print(f"[?] Estado {respuesta.status_code} en {nombre_sitio} (Posible bloqueo, rate limit o redirección)")
                
        except requests.exceptions.RequestException as e:
            # Captura errores de red, timeouts o problemas de resolución DNS
            print(f"[!] Error de conexión al consultar {nombre_sitio}: {e}")
        
        # Pausa de 1 segundo entre peticiones para ser sigilosos y evitar bloqueos (WAF)
        time.sleep(1)

    print("\n[*] Escaneo de reconocimiento finalizado.")
    return resultados

if __name__ == "__main__":
    print("=== Herramienta Básica de Reconocimiento OSINT ===")
    objetivo = input("Ingresa el alias o nombre de usuario a investigar: ")
    
    if objetivo.strip():
        hallazgos = buscar_alias(objetivo.strip())
        
        # Opcional: Aquí podrías implementar la lógica para guardar 'hallazgos' 
        # en un archivo JSON o en una base de datos para tu reporte.
        if hallazgos:
            print(f"\nResumen: Se encontraron {len(hallazgos)} posibles coincidencias. Verifica manualmente para confirmar suplantación o conexión.")
    else:
        print("[!] No se ingresó ningún alias.")
