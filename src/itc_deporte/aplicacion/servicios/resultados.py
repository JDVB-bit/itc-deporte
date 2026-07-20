"""Registrar el resultado de un enfrentamiento."""

from __future__ import annotations

from ...domain.enfrentamiento import Enfrentamiento, Marcador
from ...domain.identidades import EnfrentamientoId
from ..errores import NoEncontrado
from ..puertos import RepositorioDeEnfrentamientos


class ServicioDeResultados:
    def __init__(self, enfrentamientos: RepositorioDeEnfrentamientos) -> None:
        self._enfrentamientos = enfrentamientos

    def registrar(
        self, enfrentamiento_id: EnfrentamientoId, marcador: Marcador
    ) -> Enfrentamiento:
        """Cierra el partido con ese marcador. Volver a llamarlo lo corrige."""
        partido = self._enfrentamientos.obtener(enfrentamiento_id)
        if partido is None:
            raise NoEncontrado(f"No existe el enfrentamiento {enfrentamiento_id!r}.")
        cerrado = partido.finalizar(marcador)
        self._enfrentamientos.guardar(cerrado)
        return cerrado

    def de_fase(self, fase_id: str) -> tuple[Enfrentamiento, ...]:
        return self._enfrentamientos.de_fase(fase_id)
