"""Participante: la unidad que compite.

Cubre con un solo tipo las competiciones por equipos (un participante con varios
miembros) y las individuales (atletismo, ajedrez: un participante sin miembros o
con uno solo).

La decisión central de este módulo es que **la identidad es el `id`**, no el
nombre ni ninguna composición de campos. El sistema anterior identificaba a un
equipo por el texto `"Nombre (Curso)"`, lo volvía a parsear con expresiones
regulares y arrastraba una rutina de limpieza de filas corruptas. Aquí un
participante puede renombrarse o cambiar de división sin dejar de ser el mismo.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .errores import ErrorDeDominio
from .identidades import CompeticionId, DivisionId, MiembroId, ParticipanteId


__all__ = ["DivisionId", "Miembro", "MiembroId", "Participante", "ParticipanteId"]


@dataclass(frozen=True, slots=True)
class Miembro:
    """Integrante de un participante. Antes: `jugadores`."""

    id: MiembroId
    nombre: str
    dorsal: int | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ErrorDeDominio("Un miembro necesita un id.")
        if not self.nombre.strip():
            raise ErrorDeDominio("Un miembro necesita un nombre no vacío.")
        if self.dorsal is not None and self.dorsal < 0:
            raise ErrorDeDominio(f"Dorsal inválido: {self.dorsal}")


@dataclass(frozen=True, slots=True, eq=False)
class Participante:
    """Entidad con identidad propia.

    `eq=False` es deliberado: la igualdad se define por `id`, como corresponde a
    una entidad. Dos instancias con el mismo id son el mismo participante aunque
    difieran en nombre, división o plantilla de miembros.
    """

    id: ParticipanteId
    nombre: str
    competicion_id: CompeticionId | None = None
    division_id: DivisionId | None = None
    miembros: tuple[Miembro, ...] = ()

    def __post_init__(self) -> None:
        if not self.id:
            raise ErrorDeDominio("Un participante necesita un id.")
        if not self.nombre.strip():
            raise ErrorDeDominio("Un participante necesita un nombre no vacío.")
        ids = [m.id for m in self.miembros]
        if len(ids) != len(set(ids)):
            raise ErrorDeDominio(
                f"Miembros con id repetido en el participante {self.id!r}."
            )

    def __eq__(self, otro: object) -> bool:
        if not isinstance(otro, Participante):
            return NotImplemented
        return self.id == otro.id

    def __hash__(self) -> int:
        return hash(self.id)

    @property
    def es_individual(self) -> bool:
        return len(self.miembros) <= 1

    def miembro(self, miembro_id: MiembroId) -> Miembro | None:
        return next((m for m in self.miembros if m.id == miembro_id), None)

    def con_miembro(self, miembro: Miembro) -> Participante:
        """Devuelve un participante nuevo con `miembro` añadido."""
        if self.miembro(miembro.id) is not None:
            raise ErrorDeDominio(f"El miembro {miembro.id!r} ya está inscrito.")
        return replace(self, miembros=self.miembros + (miembro,))

    def sin_miembro(self, miembro_id: MiembroId) -> Participante:
        """Devuelve un participante nuevo sin el miembro indicado."""
        if self.miembro(miembro_id) is None:
            raise ErrorDeDominio(f"El miembro {miembro_id!r} no está inscrito.")
        restantes = tuple(m for m in self.miembros if m.id != miembro_id)
        return replace(self, miembros=restantes)

    def renombrado(self, nombre: str) -> Participante:
        return replace(self, nombre=nombre)
