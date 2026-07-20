"""Verifica la regla de dependencia de Clean Architecture.

> El código fuente solo puede apuntar hacia adentro.

La Clean Architecture se erosiona por descuido, no por decisión: por eso la regla
se comprueba con la suite y no queda a criterio de quien escribe el import.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PAQUETE = RAIZ / "itc_deporte"

# Capas de dentro hacia afuera. Cada una puede importar las anteriores.
CAPAS = ["domain", "aplicacion", "infraestructura", "ui"]


def _modulos_de(capa: str) -> list[Path]:
    directorio = PAQUETE / capa
    if not directorio.is_dir():
        return []
    return sorted(directorio.rglob("*.py"))


def _imports_de(archivo: Path) -> list[str]:
    """Módulos raíz importados por `archivo`, en notación punteada completa."""
    arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
    nombres: list[str] = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres.extend(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.level:  # import relativo: siempre dentro del propio paquete
                continue
            if nodo.module:
                nombres.append(nodo.module)
    return nombres


def _es_stdlib(modulo: str) -> bool:
    return modulo.split(".")[0] in sys.stdlib_module_names


def _capa_importada(modulo: str) -> str | None:
    """Capa de `itc_deporte` a la que apunta el import, si apunta a alguna."""
    partes = modulo.split(".")
    if partes[0] != "itc_deporte" or len(partes) < 2:
        return None
    return partes[1] if partes[1] in CAPAS else None


def test_el_dominio_solo_importa_la_biblioteca_estandar():
    """`domain/` es código puro: sin Streamlit, sin Supabase, sin bcrypt."""
    infracciones = [
        f"{archivo.relative_to(RAIZ)} importa {modulo}"
        for archivo in _modulos_de("domain")
        for modulo in _imports_de(archivo)
        if not _es_stdlib(modulo) and _capa_importada(modulo) != "domain"
    ]
    assert not infracciones, "El dominio depende de código externo:\n" + "\n".join(
        infracciones
    )


def test_ninguna_capa_importa_una_capa_exterior():
    """Cada capa solo puede apuntar hacia adentro."""
    infracciones = []
    for indice, capa in enumerate(CAPAS):
        permitidas = set(CAPAS[: indice + 1])
        for archivo in _modulos_de(capa):
            for modulo in _imports_de(archivo):
                importada = _capa_importada(modulo)
                if importada is not None and importada not in permitidas:
                    infracciones.append(
                        f"{archivo.relative_to(RAIZ)} ({capa}) importa {importada}"
                    )
    assert not infracciones, "Dependencias hacia afuera:\n" + "\n".join(infracciones)


def test_el_dominio_existe_y_tiene_modulos():
    """Guarda contra un falso verde: si `domain/` desaparece, los tests de arriba
    pasarían vacíos."""
    assert _modulos_de("domain"), "No se encontró ningún módulo en itc_deporte/domain/"
