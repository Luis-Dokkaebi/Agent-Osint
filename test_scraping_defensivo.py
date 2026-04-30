import os
import pytest
import responses
import base64
from scraping_defensivo import extraer_urls_externas, consultar_virustotal, analizar_perfil
from unittest.mock import patch

# --- Datos de prueba ---
HTML_MOCK = """
<html>
    <body>
        <a href="/about">Acerca de (Interno relativo)</a>
        <a href="https://ejemplo.com/contact">Contacto (Interno absoluto)</a>
        <a href="https://malicioso.com/descarga">Enlace externo 1</a>
        <a href="http://otro-externo.org">Enlace externo 2</a>
        <a href="mailto:test@ejemplo.com">Email (Ignorar)</a>
        <a href="javascript:void(0)">JS (Ignorar)</a>
        <a>Sin href</a>
    </body>
</html>
"""

URL_PERFIL = "https://ejemplo.com"

@responses.activate
def test_extraer_urls_externas():
    # Simular la respuesta HTTP del perfil
    responses.add(
        responses.GET,
        URL_PERFIL,
        body=HTML_MOCK,
        status=200,
        content_type='text/html'
    )

    urls = extraer_urls_externas(URL_PERFIL)

    # Debe extraer solo los dominios diferentes a "ejemplo.com"
    assert len(urls) == 2
    assert "https://malicioso.com/descarga" in urls
    assert "http://otro-externo.org" in urls
    assert "https://ejemplo.com/contact" not in urls
    assert "https://ejemplo.com/about" not in urls


@responses.activate
@patch.dict(os.environ, {"VIRUSTOTAL_API_KEY": "fake_api_key"})
def test_consultar_virustotal_limpio():
    url_test = "http://limpio.com"
    url_id = base64.urlsafe_b64encode(url_test.encode()).decode().strip("=")
    api_url = f"https://www.virustotal.com/api/v3/urls/{url_id}"

    mock_response = {
        "data": {
            "attributes": {
                "last_analysis_stats": {
                    "harmless": 80,
                    "malicious": 0,
                    "suspicious": 0,
                    "undetected": 10
                }
            }
        }
    }

    responses.add(responses.GET, api_url, json=mock_response, status=200)

    resultado = consultar_virustotal(url_test)
    assert resultado["status"] == "scanned"
    assert resultado["malicious"] == 0
    assert resultado["harmless"] == 80


@responses.activate
@patch.dict(os.environ, {"VIRUSTOTAL_API_KEY": "fake_api_key"})
def test_consultar_virustotal_no_escaneado():
    url_test = "http://nuevo-sitio.com"
    url_id = base64.urlsafe_b64encode(url_test.encode()).decode().strip("=")
    api_url = f"https://www.virustotal.com/api/v3/urls/{url_id}"

    responses.add(responses.GET, api_url, status=404)

    resultado = consultar_virustotal(url_test)
    assert resultado["status"] == "unscanned"


@responses.activate
@patch.dict(os.environ, {"VIRUSTOTAL_API_KEY": "fake_api_key"})
@patch('scraping_defensivo.time.sleep', return_value=None) # Ignorar sleep en el test
def test_analizar_perfil(mock_sleep):
    # Setup del perfil
    responses.add(
        responses.GET,
        URL_PERFIL,
        body=HTML_MOCK, # Contiene 2 urls externas: malicioso.com y otro-externo.org
        status=200,
        content_type='text/html'
    )

    # Setup para url 1
    url1 = "https://malicioso.com/descarga"
    url_id1 = base64.urlsafe_b64encode(url1.encode()).decode().strip("=")
    responses.add(
        responses.GET,
        f"https://www.virustotal.com/api/v3/urls/{url_id1}",
        json={"data": {"attributes": {"last_analysis_stats": {"malicious": 5, "harmless": 10}}}},
        status=200
    )

    # Setup para url 2
    url2 = "http://otro-externo.org"
    url_id2 = base64.urlsafe_b64encode(url2.encode()).decode().strip("=")
    responses.add(
        responses.GET,
        f"https://www.virustotal.com/api/v3/urls/{url_id2}",
        json={"data": {"attributes": {"last_analysis_stats": {"malicious": 0, "harmless": 90}}}},
        status=200
    )

    resultados = analizar_perfil(URL_PERFIL)

    assert resultados is not None
    assert url1 in resultados or url2 in resultados # Usamos 'in' porque es un set (el orden puede variar)
    assert len(resultados) == 2
    # El sleep se debió llamar al menos 1 vez (porque hay 2 links)
    mock_sleep.assert_called()
