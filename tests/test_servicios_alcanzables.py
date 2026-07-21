"""Ningún servicio sin quien lo llame.

> Un método de servicio que la interfaz no invoca es una función que el sistema
> no tiene.

Esto no es purismo. Pasó de verdad, y en producción: `crear`, `cambiar_estado`
y `retirar` estaban escritos, probados y verdes en CI, y **nada** en la interfaz
los llamaba. Con la base recién montada, un administrador no podía crear su
primera competición. La suite no lo vio porque medía el código, no el sistema:
las pruebas de interfaz corrían sobre datos de muestra que ya venían sembrados
justo por el camino que faltaba.

Es el mismo antipatrón del bracket muerto de `data.py` que motivó el refactor.
Se comprueba aquí para que no dependa de que alguien se acuerde.

**Lo que este test NO garantiza:** que la llamada sea correcta, ni que esté al
alcance del usuario que la necesita. Solo que existe. Es un suelo, no un techo.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
PAQUETE = RAIZ / "src" / "itc_deporte"
SERVICIOS = PAQUETE / "aplicacion" / "servicios"
#: Dónde puede vivir una llamada: las vistas y el guion de Streamlit.
INTERFAZ = [*(PAQUETE / "ui").rglob("*.py"), RAIZ / "app.py"]

#: Consultas que la interfaz usa por otros caminos, o que existen para el resto
#: de la capa de aplicación. Cada exención se justifica una por una: una lista
#: sin motivos es una forma elegante de desactivar el test.
EXENTOS = {
    # Alternativa a `otorgar_por_email` para quien ya tiene cuenta. La interfaz
    # ofrece solo el correo, que cubre los dos casos.
    "otorgar_por_usuario",
    # Consulta que usa la propia capa de aplicación: `cambiar_estado` la llama
    # para releer la competición antes de modificarla. La interfaz recibe las
    # competiciones ya compuestas por `listar`, así que no la necesita.
    "obtener",
}


def _metodos_publicos() -> dict[str, str]:
    """Nombre del método -> módulo donde vive."""
    encontrados = {}
    for archivo in sorted(SERVICIOS.glob("*.py")):
        if archivo.name == "__init__.py":
            continue
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        for clase in [n for n in ast.walk(arbol) if isinstance(n, ast.ClassDef)]:
            for nodo in clase.body:
                if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not nodo.name.startswith("_"):
                        encontrados[nodo.name] = archivo.name
    return encontrados


def _nombres_citados() -> set[str]:
    """Todo atributo que la interfaz menciona, se llame o se pase como valor.

    Se miran los atributos y no las llamadas porque las vistas pasan el método
    sin invocar —`_ejecutar(servicios.sorteo.sortear, ...)`— y buscar solo
    `ast.Call` daría por muerto lo que sí está conectado.
    """
    citados = set()
    for archivo in INTERFAZ:
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Attribute):
                citados.add(nodo.attr)
    return citados


@pytest.mark.parametrize(
    "metodo, modulo", sorted(_metodos_publicos().items())
)
def test_la_interfaz_llama_al_servicio(metodo: str, modulo: str) -> None:
    if metodo in EXENTOS:
        pytest.skip(f"{metodo} está exento a propósito; ver EXENTOS")
    assert metodo in _nombres_citados(), (
        f"`{modulo}.{metodo}` no lo invoca nadie en la interfaz.\n"
        "Un servicio sin quien lo llame es una función que el sistema no tiene: "
        "pasa los tests y no existe para quien usa la aplicación.\n"
        "Conéctalo desde una vista, o añádelo a EXENTOS con su motivo."
    )
