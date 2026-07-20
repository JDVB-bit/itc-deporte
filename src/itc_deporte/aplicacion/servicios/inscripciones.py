"""Inscribir y retirar participantes.

Las comprobaciones viven aquí, no en la interfaz. El sistema anterior decidía si
un equipo podía añadirse dentro del formulario de Streamlit, así que invocar la
función por otro camino se saltaba la validación.
"""

from __future__ import annotations

from ...domain.competicion import EstadoCompeticion
from ...domain.identidades import CompeticionId, DivisionId, ParticipanteId
from ...domain.participante import Participante
from ..errores import NoEncontrado, OperacionInvalida
from ..puertos import RepositorioDeCompeticiones, RepositorioDeParticipantes


class ServicioDeInscripciones:
    def __init__(
        self,
        competiciones: RepositorioDeCompeticiones,
        participantes: RepositorioDeParticipantes,
    ) -> None:
        self._competiciones = competiciones
        self._participantes = participantes

    def inscritos(self, competicion_id: CompeticionId) -> tuple[Participante, ...]:
        return self._participantes.de_competicion(competicion_id)

    def inscribir(
        self,
        competicion_id: CompeticionId,
        participante_id: ParticipanteId,
        nombre: str,
        division_id: DivisionId | None = None,
    ) -> Participante:
        competicion = self._competiciones.obtener(competicion_id)
        if competicion is None:
            raise NoEncontrado(f"No existe la competición {competicion_id!r}.")
        if competicion.estado is EstadoCompeticion.FINALIZADA:
            raise OperacionInvalida(
                f"La competición {competicion.nombre!r} ya terminó."
            )
        if self._participantes.obtener(participante_id) is not None:
            raise OperacionInvalida(f"Ya existe el participante {participante_id!r}.")

        limpio = nombre.strip()
        if any(p.nombre == limpio for p in self.inscritos(competicion_id)):
            raise OperacionInvalida(
                f"Ya hay un participante llamado {limpio!r} en esta competición."
            )

        participante = Participante(
            id=participante_id,
            nombre=limpio,
            competicion_id=competicion_id,
            division_id=division_id,
        )
        self._participantes.guardar(participante)
        return participante

    def retirar(self, participante_id: ParticipanteId) -> None:
        if self._participantes.obtener(participante_id) is None:
            raise NoEncontrado(f"No existe el participante {participante_id!r}.")
        self._participantes.eliminar(participante_id)
