"""Crear y consultar competiciones.

Crear una competición es armarla y darla de alta. El deporte y el sistema de
puntuación se eligen del catálogo de reglas (`domain/reglas/catalogo.py`), que
es lo que los mantiene como dato configurable.
"""

from __future__ import annotations

from ...domain.competicion import Competicion, EstadoCompeticion
from ...domain.identidades import CompeticionId
from ..errores import NoEncontrado, OperacionInvalida
from ..permisos import Accion, Identidad, Politica
from ..puertos import RepositorioDeCompeticiones


class ServicioDeCompeticiones:
    def __init__(
        self,
        competiciones: RepositorioDeCompeticiones,
        politica: Politica,
    ) -> None:
        self._competiciones = competiciones
        self._politica = politica

    # ── Consultas ───────────────────────────────────────────────────────────

    def listar(self) -> tuple[Competicion, ...]:
        return self._competiciones.listar()

    def obtener(self, competicion_id: CompeticionId) -> Competicion:
        competicion = self._competiciones.obtener(competicion_id)
        if competicion is None:
            raise NoEncontrado(f"No existe la competición {competicion_id!r}.")
        return competicion

    # ── Comandos ────────────────────────────────────────────────────────────

    def crear(self, actor: Identidad, competicion: Competicion) -> Competicion:
        """Da de alta una competición ya armada."""
        self._politica.exigir(actor, Accion.CREAR_COMPETICION)
        if self._competiciones.obtener(competicion.id) is not None:
            raise OperacionInvalida(f"Ya existe la competición {competicion.id!r}.")
        self._competiciones.guardar(competicion)
        return competicion

    def cambiar_estado(
        self,
        actor: Identidad,
        competicion_id: CompeticionId,
        estado: EstadoCompeticion,
    ) -> Competicion:
        from dataclasses import replace

        self._politica.exigir(
            actor, Accion.ADMINISTRAR_COMPETICION, competicion_id
        )
        competicion = replace(self.obtener(competicion_id), estado=estado)
        self._competiciones.guardar(competicion)
        return competicion
