"""Repositorios en memoria.

No son un juguete de test: son la implementación contra la que corre toda la
suite de casos de uso, y la que permite que no haya una sola llamada de red en
las pruebas. El contrato que cumplen está escrito una vez en
`tests/contratos/` y se ejecutará también contra el adaptador de Supabase, de
modo que estos no puedan divergir en silencio.

Guardan copias por valor —las entidades del dominio son inmutables—, así que
quien tenga una referencia antigua no ve los cambios de otro.
"""

from __future__ import annotations

from typing import Iterable, Sequence

from ..domain.competicion import Competicion
from ..domain.enfrentamiento import Enfrentamiento
from ..domain.identidades import (
    CompeticionId,
    EnfrentamientoId,
    FaseId,
    ParticipanteId,
)
from ..domain.participante import Participante


class CompeticionesEnMemoria:
    def __init__(self, competiciones: Iterable[Competicion] = ()) -> None:
        self._por_id: dict[CompeticionId, Competicion] = {c.id: c for c in competiciones}

    def obtener(self, competicion_id: CompeticionId) -> Competicion | None:
        return self._por_id.get(competicion_id)

    def listar(self) -> tuple[Competicion, ...]:
        return tuple(self._por_id.values())

    def guardar(self, competicion: Competicion) -> None:
        self._por_id[competicion.id] = competicion

    def eliminar(self, competicion_id: CompeticionId) -> None:
        self._por_id.pop(competicion_id, None)


class ParticipantesEnMemoria:
    def __init__(self, participantes: Iterable[Participante] = ()) -> None:
        self._por_id: dict[ParticipanteId, Participante] = {
            p.id: p for p in participantes
        }

    def obtener(self, participante_id: ParticipanteId) -> Participante | None:
        return self._por_id.get(participante_id)

    def de_competicion(self, competicion_id: CompeticionId) -> tuple[Participante, ...]:
        return tuple(
            p for p in self._por_id.values() if p.competicion_id == competicion_id
        )

    def guardar(self, participante: Participante) -> None:
        self._por_id[participante.id] = participante

    def eliminar(self, participante_id: ParticipanteId) -> None:
        self._por_id.pop(participante_id, None)


class EnfrentamientosEnMemoria:
    def __init__(self) -> None:
        self._por_fase: dict[FaseId, dict[EnfrentamientoId, Enfrentamiento]] = {}

    def obtener(self, enfrentamiento_id: EnfrentamientoId) -> Enfrentamiento | None:
        for fase in self._por_fase.values():
            if enfrentamiento_id in fase:
                return fase[enfrentamiento_id]
        return None

    def de_fase(self, fase_id: FaseId) -> tuple[Enfrentamiento, ...]:
        return tuple(self._por_fase.get(fase_id, {}).values())

    def guardar(self, enfrentamiento: Enfrentamiento) -> None:
        self._por_fase.setdefault(enfrentamiento.fase_id, {})[
            enfrentamiento.id
        ] = enfrentamiento

    def guardar_muchos(self, enfrentamientos: Sequence[Enfrentamiento]) -> None:
        for enfrentamiento in enfrentamientos:
            self.guardar(enfrentamiento)

    def eliminar_de_fase(self, fase_id: FaseId) -> None:
        self._por_fase.pop(fase_id, None)

from ..domain.division import Division
from ..domain.identidades import DivisionId

class DivisionesEnMemoria:
    def __init__(self) -> None:
        self._por_clave: dict[tuple[CompeticionId, DivisionId], Division] = {}

    def obtener(self, competicion_id, division_id):
        return self._por_clave.get((competicion_id, division_id))

    def de_competicion(self, competicion_id):
        return tuple(
            d for (c, _), d in self._por_clave.items() if c == competicion_id
        )

    def guardar(self, competicion_id, division):
        self._por_clave[(competicion_id, division.id)] = division
