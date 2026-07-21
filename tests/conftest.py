"""Apoyo compartido por toda la suite.

Las credenciales de Supabase se validan **antes** de usarlas: una clave mal
pegada —truncada, o con caracteres que el terminal sustituyó— no falla donde uno
la escribe, sino en el fondo de httpx, con un `UnicodeEncodeError` por test y
veinte marcos de pila que no dicen nada del problema real.

Vive aquí y como fixture, no como función importable, porque `tests/ui/` y
`tests/contratos/` tienen cada uno su `conftest.py` y un `from conftest import`
resuelve al que pytest haya cargado primero.
"""

from __future__ import annotations

import os

import pytest

#: Un JWT de Supabase ronda los 200 caracteres. Por debajo está cortado.
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


def _url() -> str:
    valor = os.getenv("SUPABASE_URL")
    if not valor:
        pytest.skip("Falta SUPABASE_URL.")
    valor = valor.strip()
    _sin_caracteres_ajenos("SUPABASE_URL", valor)
    if not valor.startswith("http"):
        pytest.fail(f"SUPABASE_URL no parece una URL: {valor[:40]!r}", pytrace=False)
    return valor


def _clave(nombre: str) -> str:
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


@pytest.fixture(scope="session")
def crear_cliente_supabase():
    """Devuelve una función que arma un cliente con la clave que se le pida.

    `SUPABASE_KEY` es la `service_role` —salta RLS— y `SUPABASE_ANON_KEY` la
    pública, que es la única con la que tiene sentido comprobar las políticas.
    """

    def crear(clave_env: str = "SUPABASE_KEY"):
        supabase = pytest.importorskip("supabase")
        return supabase.create_client(_url(), _clave(clave_env))

    return crear
