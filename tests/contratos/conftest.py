"""Credenciales de Supabase, validadas antes de usarlas.

Una clave mal pegada —truncada, con un salto de línea dentro, o con caracteres
que el terminal sustituyó— no falla donde uno la escribe: viaja hasta el fondo
de httpx y revienta con un `UnicodeEncodeError` en cada test, con veinte marcos
de pila que no dicen nada del problema real.

Aquí se comprueba antes, y el mensaje dice qué pasa.
"""

from __future__ import annotations

import os

import pytest


#: Un JWT de Supabase ronda los 200 caracteres. Por debajo de esto está cortado.
MINIMO_DE_CLAVE = 100


def _sin_caracteres_ajenos(nombre: str, valor: str) -> None:
    ajenos = [(i, c) for i, c in enumerate(valor) if ord(c) > 127]
    if not ajenos:
        return
    posicion, caracter = ajenos[0]
    pytest.fail(
        f"{nombre} tiene {len(ajenos)} caracteres que no son ASCII, el primero "
        f"en la posición {posicion} ({caracter!r}).\n"
        f"Un JWT de Supabase es base64: solo letras, dígitos, '-', '_' y '.'.\n"
        f"Empieza por {valor[:12]!r} y mide {len(valor)} caracteres.\n"
        "Se pegó mal. Cópiala otra vez desde Project Settings → API, en una sola "
        "línea y sin comillas.",
        pytrace=False,
    )


def url_de_supabase() -> str:
    valor = os.getenv("SUPABASE_URL")
    if not valor:
        pytest.skip("Falta SUPABASE_URL.")
    valor = valor.strip()
    _sin_caracteres_ajenos("SUPABASE_URL", valor)
    if not valor.startswith("http"):
        pytest.fail(f"SUPABASE_URL no parece una URL: {valor[:40]!r}", pytrace=False)
    return valor


def clave_de_supabase(nombre: str) -> str:
    valor = os.getenv(nombre)
    if not valor:
        pytest.skip(f"Falta {nombre}.")
    valor = valor.strip()
    _sin_caracteres_ajenos(nombre, valor)
    if len(valor) < MINIMO_DE_CLAVE:
        pytest.fail(
            f"{nombre} mide solo {len(valor)} caracteres. Las claves de Supabase "
            f"rondan los 200: la que hay está truncada.\n"
            f"Empieza por {valor[:12]!r}.",
            pytrace=False,
        )
    return valor


def cliente_supabase(clave_env: str):
    """Crea un cliente con la clave indicada, tras validar url y clave."""
    supabase = pytest.importorskip("supabase")
    return supabase.create_client(url_de_supabase(), clave_de_supabase(clave_env))
