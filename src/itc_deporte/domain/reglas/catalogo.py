"""Resolución de reglas por nombre.

Una plantilla tiene que poder viajar como JSON, y un objeto `PorSets()` no cabe
en un fichero de texto. Lo que se guarda es el nombre de la regla y sus
parámetros; este módulo los convierte en la estrategia correspondiente.

Es también el registro de lo que existe: dar de alta una regla nueva es añadir
una entrada aquí, y a partir de ese momento cualquier plantilla puede pedirla
sin que nada más cambie.
"""

from __future__ import annotations

from typing import Callable, Mapping

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
