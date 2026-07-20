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

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from .calendario import Calendario
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
        comunes = dict(
            nombre=self.nombre,
            orden=self.orden,
            fixture=self.fixture,
            config_fixture=self.config_fixture,
        )
        if self.tipo is TipoDeFase.GRUPOS:
            return FaseDeGrupos(fase_id, **comunes)
        return FaseEliminatoria(fase_id, **comunes, cupos=self.cupos)


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
    calendario: Calendario = Calendario()
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
            calendario=self.calendario,
        )
