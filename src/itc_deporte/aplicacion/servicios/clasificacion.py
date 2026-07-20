"""Consultar la tabla de posiciones."""

from __future__ import annotations

from ...domain.clasificacion import FilaClasificacion
from ...domain.competicion import FaseDeGrupos
from ...domain.identidades import CompeticionId, FaseId, GrupoId
from ...domain.motor.clasificacion import calcular_clasificacion
from ..errores import NoEncontrado
from ..puertos import (
    RepositorioDeCompeticiones,
    RepositorioDeEnfrentamientos,
    RepositorioDeParticipantes,
)


class ServicioDeClasificacion:
    def __init__(
        self,
        competiciones: RepositorioDeCompeticiones,
        participantes: RepositorioDeParticipantes,
        enfrentamientos: RepositorioDeEnfrentamientos,
    ) -> None:
        self._competiciones = competiciones
        self._participantes = participantes
        self._enfrentamientos = enfrentamientos

    def de_fase(
        self, competicion_id: CompeticionId, fase_id: FaseId
    ) -> tuple[FilaClasificacion, ...]:
        competicion = self._competiciones.obtener(competicion_id)
        if competicion is None:
            raise NoEncontrado(f"No existe la competición {competicion_id!r}.")
        if competicion.fase(fase_id) is None:
            raise NoEncontrado(
                f"La competición {competicion_id!r} no tiene la fase {fase_id!r}."
            )
        inscritos = [p.id for p in self._participantes.de_competicion(competicion_id)]
        return calcular_clasificacion(
            inscritos, self._enfrentamientos.de_fase(fase_id), competicion.reglas
        )

    def de_grupo(
        self, competicion_id: CompeticionId, fase_id: FaseId, grupo_id: GrupoId
    ) -> tuple[FilaClasificacion, ...]:
        """Tabla de un grupo: solo sus inscritos y solo sus partidos."""
        competicion = self._competiciones.obtener(competicion_id)
        if competicion is None:
            raise NoEncontrado(f"No existe la competición {competicion_id!r}.")
        fase = competicion.fase(fase_id)
        if not isinstance(fase, FaseDeGrupos):
            raise NoEncontrado(
                f"La fase {fase_id!r} no es de grupos y no tiene grupos que consultar."
            )
        grupo = fase.grupo(grupo_id)
        if grupo is None:
            raise NoEncontrado(f"La fase {fase_id!r} no tiene el grupo {grupo_id!r}.")
        return calcular_clasificacion(
            grupo.participantes,
            self._enfrentamientos.de_fase(fase_id),
            competicion.reglas,
        )
