"""Registrar el resultado de un enfrentamiento.

El marcador se contrasta con las reglas de la competición **antes** de
guardarlo. Antes no se contrastaba con nada, y un 2-2 en una competición por
sets entraba sin queja para reventar después en la pestaña de la tabla, con el
dato ya dentro.
"""

from __future__ import annotations

from ...domain.competicion import Competicion
from ...domain.enfrentamiento import Enfrentamiento, Marcador
from ...domain.identidades import EnfrentamientoId
from ..errores import NoEncontrado
from ..permisos import Accion, Identidad, Politica
from ..puertos import RepositorioDeCompeticiones, RepositorioDeEnfrentamientos


class ServicioDeResultados:
    def __init__(
        self,
        enfrentamientos: RepositorioDeEnfrentamientos,
        competiciones: RepositorioDeCompeticiones,
        politica: Politica,
    ) -> None:
        self._enfrentamientos = enfrentamientos
        self._competiciones = competiciones
        self._politica = politica

    def registrar(
        self,
        actor: Identidad,
        enfrentamiento_id: EnfrentamientoId,
        marcador: Marcador,
    ) -> Enfrentamiento:
        """Cierra el partido con ese marcador. Volver a llamarlo lo corrige.

        El permiso se acota a la competición del propio partido, no a la que
        diga quien llama: un registrador no puede tocar los de otra. Y por el
        mismo camino se recuperan sus reglas, que son las que dicen si el
        marcador es siquiera posible en ese deporte.
        """
        partido = self._enfrentamientos.obtener(enfrentamiento_id)
        if partido is None:
            raise NoEncontrado(f"No existe el enfrentamiento {enfrentamiento_id!r}.")
        self._politica.exigir(
            actor, Accion.REGISTRAR_RESULTADO, partido.competicion_id
        )
        self._competicion(partido.competicion_id).reglas.exigir_que_admita(marcador)
        cerrado = partido.finalizar(marcador)
        self._enfrentamientos.guardar(cerrado)
        return cerrado

    def _competicion(self, competicion_id) -> Competicion:
        competicion = self._competiciones.obtener(competicion_id)
        if competicion is None:
            raise NoEncontrado(f"No existe la competición {competicion_id!r}.")
        return competicion

    def de_fase(self, fase_id: str) -> tuple[Enfrentamiento, ...]:
        return self._enfrentamientos.de_fase(fase_id)
