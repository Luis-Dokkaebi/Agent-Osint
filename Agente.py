import requests
import time

def buscar_alias(alias):
    """
    Busca la existencia de un alias en distintas plataformas públicas evaluando
    los códigos de respuesta HTTP.
    """
    # Diccionario de plataformas. Se usan endpoints públicos que tienden a no bloquear
    # la verificación de existencia a la primera.
    # Nota sobre Instagram/Facebook/TikTok: Estas plataformas tienen sistemas antibot agresivos
    # que a menudo devuelven código 200 (pantalla de login genérica) o 429/403, por lo que es
    # posible que arrojen falsos positivos o falsos negativos si se consultan mediante scraping básico.
    plataformas = {
        "GitHub": f"https://github.com/{alias}",
        "Reddit": f"https://www.reddit.com/user/{alias}/about.json",
        "Vimeo": f"https://vimeo.com/{alias}",
        "Patreon": f"https://www.patreon.com/{alias}",
        "Linktree": f"https://linktr.ee/{alias}",
        "SoundCloud": f"https://soundcloud.com/{alias}",
        "Facebook": f"https://www.facebook.com/{alias}",
        "Instagram": f"https://www.instagram.com/{alias}/",
        "TikTok": f"https://www.tiktok.com/@{alias}",
        "Twitter": f"https://twitter.com/{alias}",
        "Telegram": f"https://t.me/{alias}",
        "YouTube": f"https://www.youtube.com/@{alias}",
        "Pinterest": f"https://www.pinterest.com/{alias}/",
        "Twitch": f"https://www.twitch.tv/{alias}"
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

            preservar = input("\n¿Deseas preservar evidencia forense de los enlaces encontrados? (s/n): ")
            if preservar.lower() == 's':
                # Importar la función solo si es requerida
                from forense import preservar_evidencia
                print("\n[+] Iniciando preservación de evidencia...")
                for sitio, url in hallazgos.items():
                    print(f"[*] Capturando evidencia de {sitio} ({url})...")
                    resultado = preservar_evidencia(url)
                    if resultado["estado"] == "exito":
                        print(f"  [✓] Evidencia guardada. SHA-256: {resultado['sha256']}")
                    else:
                        print(f"  [✗] Error al capturar: {resultado.get('mensaje_error')}")
                print("[+] Preservación de evidencia finalizada.")

    else:
        print("[!] No se ingresó ningún alias.")
