"""Resolución de reglas por nombre.

Una plantilla tiene que poder viajar como JSON, y un objeto `PorSets()` no cabe
en un fichero de texto. Lo que se guarda es el nombre de la regla y sus
parámetros; este módulo los convierte en la estrategia correspondiente.

Es también el registro de lo que existe: dar de alta una regla nueva es añadir
una entrada aquí, y a partir de ese momento cualquier plantilla puede pedirla
sin que nada más cambie.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Callable, Mapping

from ..errores import ReglaInvalida
from .desempate import (
    CriterioDeDesempate,
    PorAFavor,
    PorDiferencia,
    PorEnContra,
    PorEnfrentamientoDirecto,
    PorPartidosGanados,
    PorPuntos,
)
from .fixture import EliminacionDirecta, GeneradorDeFixture, RoundRobin
from .puntuacion import PorSets, SistemaDePuntuacion, VictoriaDerrota

PUNTUACIONES: Mapping[str, Callable[..., SistemaDePuntuacion]] = {
    "victoria_derrota": VictoriaDerrota,
    "por_sets": PorSets,
}

#: Cada criterio se construye a partir del sistema de puntuación, porque el
#: enfrentamiento directo lo necesita y los demás pueden ignorarlo.
DESEMPATES: Mapping[str, Callable[[SistemaDePuntuacion], CriterioDeDesempate]] = {
    "puntos": lambda _: PorPuntos(),
    "diferencia": lambda _: PorDiferencia(),
    "a_favor": lambda _: PorAFavor(),
    "en_contra": lambda _: PorEnContra(),
    "partidos_ganados": lambda _: PorPartidosGanados(),
    "enfrentamiento_directo": PorEnfrentamientoDirecto,
}

FIXTURES: Mapping[str, Callable[[], GeneradorDeFixture]] = {
    "round_robin": RoundRobin,
    "eliminacion_directa": EliminacionDirecta,
}


def _buscar(registro: Mapping[str, object], tipo: str, familia: str):
    try:
        return registro[tipo]
    except KeyError:
        disponibles = ", ".join(sorted(registro))
        raise ReglaInvalida(
            f"No existe {familia} de tipo {tipo!r}. Disponibles: {disponibles}."
        ) from None


def crear_puntuacion(
    tipo: str, parametros: Mapping[str, object] | None = None
) -> SistemaDePuntuacion:
    constructor = _buscar(PUNTUACIONES, tipo, "un sistema de puntuación")
    try:
        return constructor(**(parametros or {}))
    except TypeError as error:
        raise ReglaInvalida(
            f"Parámetros inválidos para la puntuación {tipo!r}: {error}"
        ) from error


def crear_desempate(
    tipo: str, puntuacion: SistemaDePuntuacion
) -> CriterioDeDesempate:
    constructor = _buscar(DESEMPATES, tipo, "un criterio de desempate")
    return constructor(puntuacion)


def crear_fixture(tipo: str) -> GeneradorDeFixture:
    return _buscar(FIXTURES, tipo, "un generador de fixture")()


# ── El camino de vuelta ─────────────────────────────────────────────────────
# Crear una regla desde su nombre no basta: para guardar una competición hay que
# convertir sus reglas —que son objetos— de nuevo en nombre y parámetros. Las
# dos direcciones se prueban juntas con un round-trip, de modo que registrar una
# regla nueva y olvidarse de una de las dos mitades se detecta.

NOMBRES_DE_PUNTUACION: Mapping[type, str] = {
    VictoriaDerrota: "victoria_derrota",
    PorSets: "por_sets",
}

NOMBRES_DE_DESEMPATE: Mapping[type, str] = {
    PorPuntos: "puntos",
    PorDiferencia: "diferencia",
    PorAFavor: "a_favor",
    PorEnContra: "en_contra",
    PorPartidosGanados: "partidos_ganados",
    PorEnfrentamientoDirecto: "enfrentamiento_directo",
}

NOMBRES_DE_FIXTURE: Mapping[type, str] = {
    RoundRobin: "round_robin",
    EliminacionDirecta: "eliminacion_directa",
}


def _nombrar(registro: Mapping[type, str], objeto: object, familia: str) -> str:
    nombre = registro.get(type(objeto))
    if nombre is None:
        raise ReglaInvalida(
            f"{type(objeto).__name__} no está registrada como {familia}, así que "
            "no se puede guardar. Añádela al catálogo."
        )
    return nombre


def nombre_de_puntuacion(puntuacion: SistemaDePuntuacion) -> str:
    return _nombrar(NOMBRES_DE_PUNTUACION, puntuacion, "sistema de puntuación")


def nombre_de_desempate(criterio: CriterioDeDesempate) -> str:
    return _nombrar(NOMBRES_DE_DESEMPATE, criterio, "criterio de desempate")


def nombre_de_fixture(generador: GeneradorDeFixture) -> str:
    return _nombrar(NOMBRES_DE_FIXTURE, generador, "generador de fixture")


def parametros_de(regla: object) -> dict[str, Any]:
    """Los parámetros de una regla, listos para JSON.

    Se descartan los que sean a su vez reglas: el enfrentamiento directo compone
    un sistema de puntuación, y ese no se guarda dos veces —se reconstruye desde
    el de la competición.
    """
    if not is_dataclass(regla):
        return {}
    crudos = asdict(regla)
    return {
        clave: valor
        for clave, valor in crudos.items()
        if isinstance(valor, (int, float, str, bool, type(None)))
    }
