"""Resolución de reglas por nombre.

Una competición se guarda como filas, y un objeto `PorSets()` no cabe en una
columna. Lo que se persiste es el nombre de la regla y sus parámetros; este
módulo convierte en las dos direcciones.

Es también el registro de lo que existe: dar de alta un deporte con reglas
propias es añadir una entrada aquí, y a partir de ese momento cualquier
competición puede pedirla sin que nada más cambie. Es lo que mantiene deportes
y puntuaciones como dato configurable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
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


# ── Deportes ────────────────────────────────────────────────────────────────
# Un deporte no es solo un nombre y un icono: trae consigo cómo se puntúa. El
# voleibol no admite empates y el baloncesto no reparte punto por empatar, pero
# hasta ahora toda competición nacía con el 3/1/0 del fútbol viniera del deporte
# que viniera, porque la pantalla de crear no ofrecía elegir reglas y el
# constructor tomaba las de por defecto.
#
# Registrar un deporte aquí es darle sus reglas, y a partir de ese momento
# crear una competición suya las trae puestas. Se pueden ajustar antes de dar
# de alta la competición; lo que se guarda son las ajustadas.


@dataclass(frozen=True, slots=True)
class DeporteDelCatalogo:
    """Un deporte y las reglas que le corresponden por defecto.

    Los parámetros van como pares y no como `dict` para que la entrada sea
    inmutable y comparable, igual que las reglas que describe.
    """

    id: str
    nombre: str
    icono: str = ""
    puntuacion: str = "victoria_derrota"
    parametros: tuple[tuple[str, int], ...] = ()
    desempate: tuple[str, ...] = ("puntos", "diferencia", "a_favor")

    def deporte(self):
        """El `Deporte` del dominio que le corresponde."""
        from ..competicion import Deporte

        return Deporte(self.id, self.nombre, self.icono)

    def puntuacion_por_defecto(self) -> SistemaDePuntuacion:
        return crear_puntuacion(self.puntuacion, dict(self.parametros))

    def reglas(self, puntuacion: SistemaDePuntuacion | None = None):
        """Las reglas del deporte, o las mismas con la puntuación ajustada.

        El desempate se reconstruye siempre sobre la puntuación que se vaya a
        usar: el enfrentamiento directo la compone, y uno armado sobre el 3/1/0
        daría otra cosa dentro de una competición por sets.
        """
        from ..competicion import ReglasDeCompeticion

        elegida = puntuacion if puntuacion is not None else self.puntuacion_por_defecto()
        return ReglasDeCompeticion(
            puntuacion=elegida,
            desempate=tuple(crear_desempate(n, elegida) for n in self.desempate),
        )


#: Sin empate posible y con el desempate por partidos ganados: en voleibol la
#: diferencia de sets desempata después, no antes.
_DESEMPATE_POR_SETS = ("puntos", "partidos_ganados", "diferencia")

DEPORTES: Mapping[str, DeporteDelCatalogo] = {
    deporte.id: deporte
    for deporte in (
        DeporteDelCatalogo("microfutbol", "Microfútbol", "⚽"),
        DeporteDelCatalogo("futbol", "Fútbol", "⚽"),
        DeporteDelCatalogo("futbol_sala", "Fútbol sala", "🥅"),
        DeporteDelCatalogo(
            "baloncesto",
            "Baloncesto",
            "🏀",
            # 2/0/0: en baloncesto no hay empate que premiar, se juega prórroga.
            parametros=(("victoria", 2), ("empate", 0), ("derrota", 0)),
        ),
        DeporteDelCatalogo(
            "voleyball",
            "Voleibol",
            "🏐",
            puntuacion="por_sets",
            desempate=_DESEMPATE_POR_SETS,
        ),
        DeporteDelCatalogo(
            "tenis_de_mesa",
            "Tenis de mesa",
            "🏓",
            puntuacion="por_sets",
            desempate=_DESEMPATE_POR_SETS,
        ),
        DeporteDelCatalogo(
            "ajedrez",
            "Ajedrez",
            "♟️",
            # 2/1/0 y no 1/½/0: los puntos de la tabla son enteros. La escala
            # cambia, el orden que produce es el mismo.
            parametros=(("victoria", 2), ("empate", 1), ("derrota", 0)),
        ),
    )
}
