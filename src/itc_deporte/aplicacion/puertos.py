"""Los puertos: qué necesita la aplicación del mundo exterior.

Son protocolos, no clases base. Los servicios dependen de ellos y nunca de
Supabase, que es lo que permite ejecutar la suite entera sin red.

Un puerto estrecho por agregado, no un repositorio-dios: quien solo necesita
leer participantes no arrastra los métodos de enfrentamientos.

Sobre `guardar_muchos`: existe porque el sistema anterior escribía un `INSERT`
por partido al sortear y un `UPDATE` por casilla al propagar el cuadro. El
puerto admite el lote para que el adaptador pueda hacerlo de una vez; que lo
haga o no es cosa suya.
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from ..domain.competicion import Competicion
from ..domain.enfrentamiento import Enfrentamiento
from ..domain.identidades import (
    CompeticionId,
    EnfrentamientoId,
    FaseId,
    ParticipanteId,
)
from ..domain.participante import Participante
from ..domain.plantilla import PlantillaDeCompeticion


class NoEncontrado(LookupError):
    """Se pidió algo que el repositorio no tiene."""


@runtime_checkable
class RepositorioDeCompeticiones(Protocol):
    def obtener(self, competicion_id: CompeticionId) -> Competicion | None: ...

    def listar(self) -> tuple[Competicion, ...]: ...

    def guardar(self, competicion: Competicion) -> None: ...

    def eliminar(self, competicion_id: CompeticionId) -> None: ...


@runtime_checkable
class RepositorioDeParticipantes(Protocol):
    def obtener(self, participante_id: ParticipanteId) -> Participante | None: ...

    def de_competicion(
        self, competicion_id: CompeticionId
    ) -> tuple[Participante, ...]: ...

    def guardar(self, participante: Participante) -> None: ...

    def eliminar(self, participante_id: ParticipanteId) -> None: ...


@runtime_checkable
class RepositorioDeEnfrentamientos(Protocol):
    def obtener(self, enfrentamiento_id: EnfrentamientoId) -> Enfrentamiento | None: ...

    def de_fase(self, fase_id: FaseId) -> tuple[Enfrentamiento, ...]: ...

    def guardar(self, enfrentamiento: Enfrentamiento) -> None: ...

    def guardar_muchos(self, enfrentamientos: Sequence[Enfrentamiento]) -> None: ...

    def eliminar_de_fase(self, fase_id: FaseId) -> None: ...


@runtime_checkable
class RepositorioDePlantillas(Protocol):
    def obtener(self, plantilla_id: str) -> PlantillaDeCompeticion | None: ...

    def listar(self) -> tuple[PlantillaDeCompeticion, ...]: ...
