import os
import json
import pytest
import responses
from dorks_pastebin import buscar_alias_pastebins

@pytest.fixture
def mock_env_vars():
    os.environ["GOOGLE_API_KEY"] = "fake_api_key"
    os.environ["GOOGLE_CSE_ID"] = "fake_cse_id"
    yield
    del os.environ["GOOGLE_API_KEY"]
    del os.environ["GOOGLE_CSE_ID"]

@responses.activate
def test_búsqueda_sin_credenciales():
    # Asegurar que el entorno no tenga las variables
    if "GOOGLE_API_KEY" in os.environ:
         del os.environ["GOOGLE_API_KEY"]

    resultado = buscar_alias_pastebins("hacker123")
    assert resultado["estado"] == "error"
    assert "Faltan credenciales" in resultado["mensaje_error"]

@responses.activate
def test_búsqueda_exitosa(mock_env_vars):
    url = "https://www.googleapis.com/customsearch/v1"

    mock_response = {
        "items": [
            {"title": "hacker123 leak", "link": "https://pastebin.com/abcd123"},
            {"title": "Ghostbin data", "link": "https://ghostbin.com/xyz987"}
        ]
    }

    responses.add(responses.GET, url, json=mock_response, status=200)

    resultado = buscar_alias_pastebins("hacker123")
    assert resultado["estado"] == "exito"
    assert len(resultado["sitios_encontrados"]) == 2
    assert resultado["sitios_encontrados"][0]["url"] == "https://pastebin.com/abcd123"

@responses.activate
def test_rate_limit_y_falla(mock_env_vars, monkeypatch):
    # Hacer que time.sleep no haga nada real para no demorar la prueba
    import time
    monkeypatch.setattr(time, "sleep", lambda x: None)

    url = "https://www.googleapis.com/customsearch/v1"

    # Simular que todas las peticiones devuelven 429
    responses.add(responses.GET, url, body="Rate Limit Exceeded", status=429)
    responses.add(responses.GET, url, body="Rate Limit Exceeded", status=429)
    responses.add(responses.GET, url, body="Rate Limit Exceeded", status=429)

    resultado = buscar_alias_pastebins("hacker123")
    assert resultado["estado"] == "error"
    assert "Rate Limit" in resultado["mensaje_error"]
    assert len(responses.calls) == 3 # Verifica que se reintentó 3 veces

@responses.activate
def test_rate_limit_y_exito_posterior(mock_env_vars, monkeypatch):
    import time
    monkeypatch.setattr(time, "sleep", lambda x: None)

    url = "https://www.googleapis.com/customsearch/v1"

    # Primera falla 429, Segunda éxito 200
    responses.add(responses.GET, url, body="Rate Limit Exceeded", status=429)
    mock_response = {"items": [{"title": "Leak", "link": "https://pastebin.com/leak"}]}
    responses.add(responses.GET, url, json=mock_response, status=200)

    resultado = buscar_alias_pastebins("hacker123")
    assert resultado["estado"] == "exito"
    assert len(responses.calls) == 2 # Solo necesitó dos llamadas
    assert resultado["sitios_encontrados"][0]["url"] == "https://pastebin.com/leak"
