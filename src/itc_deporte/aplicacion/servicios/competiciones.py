"""Crear y consultar competiciones."""

from __future__ import annotations

from ...domain.competicion import Competicion, EstadoCompeticion
from ...domain.identidades import CompeticionId
from ...domain.plantilla import PlantillaDeCompeticion
from ..errores import NoEncontrado, OperacionInvalida
from ..puertos import RepositorioDeCompeticiones, RepositorioDePlantillas


class ServicioDeCompeticiones:
    def __init__(
        self,
        competiciones: RepositorioDeCompeticiones,
        plantillas: RepositorioDePlantillas,
    ) -> None:
        self._competiciones = competiciones
        self._plantillas = plantillas

    # ── Consultas ───────────────────────────────────────────────────────────

    def listar(self) -> tuple[Competicion, ...]:
        return self._competiciones.listar()

    def obtener(self, competicion_id: CompeticionId) -> Competicion:
        competicion = self._competiciones.obtener(competicion_id)
        if competicion is None:
            raise NoEncontrado(f"No existe la competición {competicion_id!r}.")
        return competicion

    def catalogo_de_plantillas(self) -> tuple[PlantillaDeCompeticion, ...]:
        """Lo que alimenta la pestaña "Plantillas" al crear una competición."""
        return self._plantillas.listar()

    # ── Comandos ────────────────────────────────────────────────────────────

    def crear_desde_plantilla(
        self,
        plantilla_id: str,
        competicion_id: CompeticionId,
        nombre: str | None = None,
        temporada: str | None = None,
    ) -> Competicion:
        plantilla = self._plantillas.obtener(plantilla_id)
        if plantilla is None:
            raise NoEncontrado(f"No existe la plantilla {plantilla_id!r}.")
        return self.crear(plantilla.instanciar(competicion_id, nombre, temporada))

    def crear(self, competicion: Competicion) -> Competicion:
        """Da de alta una competición ya armada, venga de plantilla o de cero."""
        if self._competiciones.obtener(competicion.id) is not None:
            raise OperacionInvalida(f"Ya existe la competición {competicion.id!r}.")
        self._competiciones.guardar(competicion)
        return competicion

    def cambiar_estado(
        self, competicion_id: CompeticionId, estado: EstadoCompeticion
    ) -> Competicion:
        from dataclasses import replace

        competicion = replace(self.obtener(competicion_id), estado=estado)
        self._competiciones.guardar(competicion)
        return competicion
