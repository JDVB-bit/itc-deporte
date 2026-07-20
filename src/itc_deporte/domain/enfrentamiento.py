"""Enfrentamiento y Marcador.

`Marcador` separa el **total** de los **parciales**, y esa separación es lo que
hace expresable el voleibol. En el sistema anterior todo partido se puntuaba por
"goles" y admitía empates, de modo que un 3-1 en sets y un 3-1 en goles eran
indistinguibles y un partido de voleibol podía terminar empatado.

Aquí el total es el resultado que decide el partido (sets ganados en voleibol,
goles en fútbol) y los parciales son el detalle opcional (puntos de cada set).
Deliberadamente el total **no** se deriva de los parciales: en fútbol sería la
suma de los tiempos, en voleibol es el recuento de sets ganados. Cuál de las dos
cosas es, lo dice el deporte, no el marcador. Para los dos casos frecuentes hay
constructores explícitos: `por_sets` y `por_suma`.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, replace
from enum import Enum
from typing import NewType, Sequence

from .errores import ErrorDeDominio
from .participante import ParticipanteId

EnfrentamientoId = NewType("EnfrentamientoId", str)


@dataclass(frozen=True, slots=True)
class Parcial:
    """Un tramo del partido: un set, un cuarto, un tiempo."""

    local: int
    visitante: int

    def __post_init__(self) -> None:
        if self.local < 0 or self.visitante < 0:
            raise ErrorDeDominio(
                f"Un parcial no admite valores negativos: {self.local}-{self.visitante}"
            )


@dataclass(frozen=True, slots=True)
class Marcador:
    local: int
    visitante: int
    parciales: tuple[Parcial, ...] = ()

    def __post_init__(self) -> None:
        if self.local < 0 or self.visitante < 0:
            raise ErrorDeDominio(
                f"Un marcador no admite valores negativos: "
                f"{self.local}-{self.visitante}"
            )

    @classmethod
    def por_sets(cls, parciales: Sequence[Parcial]) -> Marcador:
        """Total = sets ganados. Los sets empatados no cuentan para nadie."""
        local = sum(1 for p in parciales if p.local > p.visitante)
        visitante = sum(1 for p in parciales if p.visitante > p.local)
        return cls(local, visitante, tuple(parciales))

    @classmethod
    def por_suma(cls, parciales: Sequence[Parcial]) -> Marcador:
        """Total = suma de los parciales. Tiempos de fútbol, cuartos de baloncesto."""
        return cls(
            sum(p.local for p in parciales),
            sum(p.visitante for p in parciales),
            tuple(parciales),
        )

    @property
    def gana_local(self) -> bool:
        return self.local > self.visitante

    @property
    def gana_visitante(self) -> bool:
        return self.visitante > self.local

    @property
    def es_empate(self) -> bool:
        return self.local == self.visitante

    @property
    def diferencia(self) -> int:
        """Positiva si gana el local."""
        return self.local - self.visitante

    def invertido(self) -> Marcador:
        """El mismo marcador visto desde el otro lado."""
        return Marcador(
            self.visitante,
            self.local,
            tuple(Parcial(p.visitante, p.local) for p in self.parciales),
        )


class EstadoEnfrentamiento(Enum):
    PENDIENTE = "Pendiente"
    FINALIZADO = "Finalizado"


@dataclass(frozen=True, slots=True, eq=False)
class Enfrentamiento:
    """Entidad: la igualdad se define por `id`, como en `Participante`."""

    id: EnfrentamientoId
    local: ParticipanteId
    visitante: ParticipanteId
    marcador: Marcador | None = None
    estado: EstadoEnfrentamiento = EstadoEnfrentamiento.PENDIENTE
    fecha: dt.datetime | None = None
    jornada: int | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ErrorDeDominio("Un enfrentamiento necesita un id.")
        if self.local == self.visitante:
            raise ErrorDeDominio(
                f"Un participante no puede enfrentarse a sí mismo: {self.local!r}"
            )
        if self.esta_finalizado and self.marcador is None:
            raise ErrorDeDominio(
                f"El enfrentamiento {self.id!r} está finalizado y no tiene marcador."
            )

    def __eq__(self, otro: object) -> bool:
        if not isinstance(otro, Enfrentamiento):
            return NotImplemented
        return self.id == otro.id

    def __hash__(self) -> int:
        return hash(self.id)

    @property
    def esta_finalizado(self) -> bool:
        return self.estado is EstadoEnfrentamiento.FINALIZADO

    def participa(self, participante_id: ParticipanteId) -> bool:
        return participante_id in (self.local, self.visitante)

    def rival_de(self, participante_id: ParticipanteId) -> ParticipanteId | None:
        if participante_id == self.local:
            return self.visitante
        if participante_id == self.visitante:
            return self.local
        return None

    def finalizar(self, marcador: Marcador) -> Enfrentamiento:
        """Devuelve el enfrentamiento cerrado con ese marcador."""
        return replace(
            self, marcador=marcador, estado=EstadoEnfrentamiento.FINALIZADO
        )

    def ganador(self) -> ParticipanteId | None:
        """`None` si no ha terminado o si terminó en empate."""
        if not self.esta_finalizado or self.marcador is None:
            return None
        if self.marcador.gana_local:
            return self.local
        if self.marcador.gana_visitante:
            return self.visitante
        return None

    def perdedor(self) -> ParticipanteId | None:
        ganador = self.ganador()
        if ganador is None:
            return None
        return self.visitante if ganador == self.local else self.local

    def marcador_de(self, participante_id: ParticipanteId) -> Marcador | None:
        """El marcador orientado hacia `participante_id`: su total primero."""
        if self.marcador is None or not self.participa(participante_id):
            return None
        if participante_id == self.local:
            return self.marcador
        return self.marcador.invertido()
