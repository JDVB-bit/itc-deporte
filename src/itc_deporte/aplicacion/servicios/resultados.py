"""Registrar el resultado de un enfrentamiento."""

from __future__ import annotations

from ...domain.enfrentamiento import Enfrentamiento, Marcador
from ...domain.identidades import EnfrentamientoId
from ..errores import NoEncontrado
from ..permisos import Accion, Identidad, Politica
from ..puertos import RepositorioDeEnfrentamientos


class ServicioDeResultados:
    def __init__(
        self, enfrentamientos: RepositorioDeEnfrentamientos, politica: Politica
    ) -> None:
        self._enfrentamientos = enfrentamientos
        self._politica = politica

    def registrar(
        self,
        actor: Identidad,
        enfrentamiento_id: EnfrentamientoId,
        marcador: Marcador,
    ) -> Enfrentamiento:
        """Cierra el partido con ese marcador. Volver a llamarlo lo corrige.

        El permiso se acota a la competición del propio partido, no a la que
        diga quien llama: un registrador no puede tocar los de otra.
        """
        partido = self._enfrentamientos.obtener(enfrentamiento_id)
        if partido is None:
            raise NoEncontrado(f"No existe el enfrentamiento {enfrentamiento_id!r}.")
        self._politica.exigir(
            actor, Accion.REGISTRAR_RESULTADO, partido.competicion_id
        )
        cerrado = partido.finalizar(marcador)
        self._enfrentamientos.guardar(cerrado)
        return cerrado

    def de_fase(self, fase_id: str) -> tuple[Enfrentamiento, ...]:
        return self._enfrentamientos.de_fase(fase_id)
