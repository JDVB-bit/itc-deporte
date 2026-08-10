"""Crear y consultar competiciones.

Crear una competición es armarla y darla de alta. El deporte y el sistema de
puntuación se eligen del catálogo de reglas (`domain/reglas/catalogo.py`), que
es lo que los mantiene como dato configurable.
"""

from __future__ import annotations

from ...domain.competicion import Competicion, EstadoCompeticion
from ...domain.identidades import CompeticionId
from ..errores import NoEncontrado, OperacionInvalida
from ..permisos import Accion, Concesion, Identidad, Politica, Rol
from ..puertos import RepositorioDeCompeticiones, RepositorioDeConcesiones


class ServicioDeCompeticiones:
    def __init__(
        self,
        competiciones: RepositorioDeCompeticiones,
        concesiones: RepositorioDeConcesiones,
        politica: Politica,
    ) -> None:
        self._competiciones = competiciones
        self._concesiones = concesiones
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
        self._conceder_al_creador(actor, competicion.id)
        return competicion

    def _conceder_al_creador(
        self, actor: Identidad, competicion_id: CompeticionId
    ) -> None:
        """Quien crea una competición queda como registrador de ella.

        Sin esto, un registrador podía dar de alta una competición y quedarse
        sin poder inscribir a nadie: su concesión es *por competición*, y la
        recién creada no estaba en ninguna. Habría que pedirle a un admin
        permiso sobre algo que uno acaba de crear.

        Al admin no se le otorga nada: su rol ya es global, y una concesión de
        admin con competición está prohibida por el propio tipo.
        """
        if Rol.ADMIN in self._politica.roles_de(actor):
            return
        self._concesiones.otorgar(
            Concesion(actor.usuario_id, Rol.REGISTRADOR, competicion_id)
        )

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
