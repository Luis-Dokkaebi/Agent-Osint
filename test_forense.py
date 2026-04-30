import os
import json
import pytest
from forense import preservar_evidencia, calcular_sha256

def test_preservar_evidencia_exito():
    # URL de prueba rápida que debería cargar sin problemas
    url_prueba = "https://example.com"
    resultado = preservar_evidencia(url_prueba)

    # Validar estructura del resultado
    assert resultado["estado"] == "exito"
    assert "timestamp" in resultado
    assert resultado["url"] == url_prueba
    assert "archivo_evidencia" in resultado
    assert "sha256" in resultado

    ruta_imagen = resultado["archivo_evidencia"]
    hash_esperado = resultado["sha256"]

    # Verificar que el archivo de imagen se creó
    assert os.path.exists(ruta_imagen)

    # Verificar que el cálculo del hash del archivo creado coincide con el registro
    hash_calculado = calcular_sha256(ruta_imagen)
    assert hash_calculado == hash_esperado

    # Verificar que el log contiene la entrada
    encontrado_en_log = False
    with open("cadena_custodia.log", "r", encoding="utf-8") as f:
        for linea in f:
            registro_log = json.loads(linea)
            if registro_log.get("timestamp") == resultado["timestamp"]:
                encontrado_en_log = True
                assert registro_log["estado"] == "exito"
                assert registro_log["sha256"] == hash_esperado
                break

    assert encontrado_en_log

def test_preservar_evidencia_error():
    # URL inválida para forzar error (ej. dominio que no existe)
    url_invalida = "http://un-dominio-que-seguramente-no-existe-123456789.com"
    resultado = preservar_evidencia(url_invalida)

    # Validar estructura del error
    assert resultado["estado"] == "error"
    assert "timestamp" in resultado
    assert resultado["url"] == url_invalida
    assert "mensaje_error" in resultado

    # Verificar que el log contiene el error
    encontrado_en_log = False
    with open("cadena_custodia.log", "r", encoding="utf-8") as f:
        for linea in f:
            registro_log = json.loads(linea)
            if registro_log.get("timestamp") == resultado["timestamp"]:
                encontrado_en_log = True
                assert registro_log["estado"] == "error"
                assert "mensaje_error" in registro_log
                break

    assert encontrado_en_log
