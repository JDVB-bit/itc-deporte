"""Plantilla de competición: una descripción serializable de cómo se arma una.

Es la pieza que evita que la configuración del ITC quede cableada como caso
especial. Una plantilla dice qué deporte, qué divisiones, cómo se puntúa, cómo
se desempata, qué fases hay y cada cuánto se juega. Instanciarla produce una
`Competicion` normal y editable: la plantilla es un punto de partida, no un
candado.

ITC es la primera del catálogo, no una rama de código. Quien cree la suya usa
exactamente el mismo mecanismo.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from .competicion import (
    Competicion,
    CompeticionId,
    Deporte,
    Fase,
    FaseDeGrupos,
    FaseEliminatoria,
    ReglasDeCompeticion,
)
from .division import CatalogoDeDivisiones, Division
from .errores import ErrorDeDominio
from .reglas.catalogo import crear_desempate, crear_fixture, crear_puntuacion
from .reglas.fixture import ConfigFixture, GeneradorDeFixture


@dataclass(frozen=True, slots=True)
class EspecificacionDeRegla:
    """El nombre de una regla y sus parámetros, tal como viajan en JSON."""

    tipo: str
    parametros: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.tipo:
            raise ErrorDeDominio("Una especificación de regla necesita un tipo.")
        object.__setattr__(self, "parametros", MappingProxyType(dict(self.parametros)))


class TipoDeFase(Enum):
    GRUPOS = "grupos"
    ELIMINATORIA = "eliminatoria"


@dataclass(frozen=True, slots=True)
class EspecificacionDeFase:
    tipo: TipoDeFase
    nombre: str
    orden: int
    fixture: str = "round_robin"
    config_fixture: ConfigFixture = ConfigFixture()
    cupos: int = 2

    def __post_init__(self) -> None:
        if not self.nombre.strip():
            raise ErrorDeDominio("Una fase de la plantilla necesita un nombre.")
        if self.orden < 0:
            raise ErrorDeDominio(f"Orden de fase inválido: {self.orden}")

    def generador(self) -> GeneradorDeFixture:
        return crear_fixture(self.fixture)

    def instanciar(self, fase_id: str) -> Fase:
        if self.tipo is TipoDeFase.GRUPOS:
            return FaseDeGrupos(fase_id, self.nombre, self.orden)
        return FaseEliminatoria(fase_id, self.nombre, self.orden, cupos=self.cupos)


@dataclass(frozen=True, slots=True)
class EspecificacionDeCalendario:
    """Cuándo se juega. Antes: sábado y 15:00 escritos a mano en el sorteo.

    `dia_de_la_semana` sigue el convenio de `date.weekday()`: 0 es lunes y 5
    sábado. En `None`, la primera jornada cae en la fecha de arranque.
    """

    dia_de_la_semana: int | None = None
    hora: dt.time = dt.time(15, 0)
    cadencia_dias: int = 7

    def __post_init__(self) -> None:
        if self.dia_de_la_semana is not None and not 0 <= self.dia_de_la_semana <= 6:
            raise ErrorDeDominio(
                f"Día de la semana inválido: {self.dia_de_la_semana}. Va de 0 a 6."
            )
        if self.cadencia_dias < 1:
            raise ErrorDeDominio(f"Cadencia inválida: {self.cadencia_dias} días.")

    def fechas(self, desde: dt.date, cantidad: int) -> tuple[dt.datetime, ...]:
        """Las `cantidad` primeras fechas de juego a partir de `desde`.

        Si hay día fijado, la primera cae en el siguiente que corresponda,
        nunca el mismo `desde`: es el comportamiento del sorteo actual, que
        estando en sábado programaba para el sábado siguiente.
        """
        if cantidad < 0:
            raise ErrorDeDominio(f"No se pueden generar {cantidad} fechas.")
        inicio = desde
        if self.dia_de_la_semana is not None:
            avance = (self.dia_de_la_semana - desde.weekday()) % 7
            inicio = desde + dt.timedelta(days=avance or 7)
        return tuple(
            dt.datetime.combine(inicio + dt.timedelta(days=self.cadencia_dias * i), self.hora)
            for i in range(cantidad)
        )


@dataclass(frozen=True, slots=True)
class PlantillaDeCompeticion:
    id: str
    nombre: str
    deporte: Deporte
    descripcion: str = ""
    divisiones: tuple[Division, ...] = ()
    puntuacion: EspecificacionDeRegla = EspecificacionDeRegla("victoria_derrota")
    desempate: tuple[str, ...] = ("puntos", "diferencia", "a_favor")
    fases: tuple[EspecificacionDeFase, ...] = ()
    calendario: EspecificacionDeCalendario = EspecificacionDeCalendario()
    es_semilla: bool = False

    def __post_init__(self) -> None:
        if not self.id:
            raise ErrorDeDominio("Una plantilla necesita un id.")
        if not self.nombre.strip():
            raise ErrorDeDominio("Una plantilla necesita un nombre no vacío.")
        if not self.desempate:
            raise ErrorDeDominio(
                f"La plantilla {self.id!r} no define ningún criterio de desempate."
            )
        ordenes = [f.orden for f in self.fases]
        if len(ordenes) != len(set(ordenes)):
            raise ErrorDeDominio(
                f"Dos fases comparten orden en la plantilla {self.id!r}: "
                f"{sorted(ordenes)}"
            )

    def catalogo_de_divisiones(self) -> CatalogoDeDivisiones:
        return CatalogoDeDivisiones(self.divisiones)

    def reglas(self) -> ReglasDeCompeticion:
        puntuacion = crear_puntuacion(self.puntuacion.tipo, self.puntuacion.parametros)
        return ReglasDeCompeticion(
            puntuacion=puntuacion,
            desempate=tuple(crear_desempate(t, puntuacion) for t in self.desempate),
        )

    def instanciar(
        self,
        competicion_id: CompeticionId,
        nombre: str | None = None,
        temporada: str | None = None,
    ) -> Competicion:
        """Produce una competición editable a partir de la plantilla."""
        fases = tuple(
            spec.instanciar(f"{competicion_id}:{spec.orden}")
            for spec in sorted(self.fases, key=lambda f: f.orden)
        )
        return Competicion(
            id=competicion_id,
            nombre=nombre or self.nombre,
            deporte=self.deporte,
            temporada=temporada,
            fases=fases,
            reglas=self.reglas(),
        )
