"""Inscribir y retirar participantes.

Las comprobaciones viven aquí, no en la interfaz. El sistema anterior decidía si
un equipo podía añadirse dentro del formulario de Streamlit, así que invocar la
función por otro camino se saltaba la validación.
"""

from __future__ import annotations

from ...domain.competicion import EstadoCompeticion
from ...domain.division import Division
from ...domain.identidades import CompeticionId, DivisionId, ParticipanteId
from ...domain.participante import Participante
from ..errores import NoEncontrado, OperacionInvalida
from ..permisos import Accion, Identidad, Politica
from ..puertos import (
    RepositorioDeCompeticiones,
    RepositorioDeDivisiones,
    RepositorioDeParticipantes,
)


class ServicioDeInscripciones:
    def __init__(
        self,
        competiciones: RepositorioDeCompeticiones,
        participantes: RepositorioDeParticipantes,
        politica: Politica,
        divisiones: RepositorioDeDivisiones | None = None,
    ) -> None:
        self._competiciones = competiciones
        self._participantes = participantes
        self._politica = politica
        #: Opcional: el repositorio en memoria no tiene FK que proteger, así
        #: que los tests que no lo pasan siguen funcionando igual.
        self._divisiones = divisiones

    def inscritos(self, competicion_id: CompeticionId) -> tuple[Participante, ...]:
        return self._participantes.de_competicion(competicion_id)

    def inscribir(
        self,
        actor: Identidad,
        competicion_id: CompeticionId,
        participante_id: ParticipanteId,
        nombre: str,
        division_id: DivisionId | None = None,
    ) -> Participante:
        self._politica.exigir(
            actor, Accion.INSCRIBIR_PARTICIPANTE, competicion_id
        )
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

        if division_id:
            self._asegurar_division(competicion_id, division_id)

        participante = Participante(
            id=participante_id,
            nombre=limpio,
            competicion_id=competicion_id,
            division_id=division_id,
        )
        self._participantes.guardar(participante)
        return participante

    def retirar(self, actor: Identidad, participante_id: ParticipanteId) -> None:
        participante = self._participantes.obtener(participante_id)
        if participante is None:
            raise NoEncontrado(f"No existe el participante {participante_id!r}.")
        self._politica.exigir(
            actor, Accion.INSCRIBIR_PARTICIPANTE, participante.competicion_id
        )
        self._participantes.eliminar(participante_id)

    def _asegurar_division(
        self, competicion_id: CompeticionId, division_id: DivisionId
    ) -> None:
        """Crea la división si todavía no existe.

        `participantes.division_id` la referencia por FK en Supabase: guardar
        el participante sin esto primero revienta contra la base real, aunque
        el repositorio en memoria —sin integridad referencial— lo tolere.
        """
        if self._divisiones is None:
            return
        if self._divisiones.obtener(competicion_id, division_id) is None:
            self._divisiones.guardar(
                competicion_id, Division(id=division_id, nombre=division_id)
            )
