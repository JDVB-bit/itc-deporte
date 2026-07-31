"""Los puertos: qué necesita la aplicación del mundo exterior.

Son protocolos, no clases base. Los servicios dependen de ellos y nunca de
Supabase, que es lo que permite ejecutar la suite entera sin red.

Un puerto estrecho por agregado, no un repositorio-dios: quien solo necesita
leer participantes no arrastra los métodos de enfrentamientos.

Sobre `guardar_muchos`: existe porque el sistema anterior escribía un `INSERT`
por partido al sortear y un `UPDATE` por casilla al propagar el cuadro. El
puerto admite el lote para que el adaptador pueda hacerlo de una vez; que lo
haga o no es cosa suya.
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from ..domain.competicion import Competicion
from ..domain.enfrentamiento import Enfrentamiento
from ..domain.identidades import (
    CompeticionId,
    EnfrentamientoId,
    FaseId,
    ParticipanteId,
)
from ..domain.participante import Participante
from .permisos import Concesion, Identidad, Sesion


@runtime_checkable
class RepositorioDeCompeticiones(Protocol):
    def obtener(self, competicion_id: CompeticionId) -> Competicion | None: ...

    def listar(self) -> tuple[Competicion, ...]: ...

    def guardar(self, competicion: Competicion) -> None: ...

    def eliminar(self, competicion_id: CompeticionId) -> None: ...


@runtime_checkable
class RepositorioDeParticipantes(Protocol):
    def obtener(self, participante_id: ParticipanteId) -> Participante | None: ...

    def de_competicion(
        self, competicion_id: CompeticionId
    ) -> tuple[Participante, ...]: ...

    def guardar(self, participante: Participante) -> None: ...

    def eliminar(self, participante_id: ParticipanteId) -> None: ...

from ..domain.division import Division

@runtime_checkable
class RepositorioDeDivisiones(Protocol):
    """Existe porque `participantes.division_id` referencia esta tabla por FK:
    guardar un participante con una división que no está aquí todavía revienta
    contra Supabase, aunque el repositorio en memoria lo tolere."""

    def obtener(
        self, competicion_id: CompeticionId, division_id: DivisionId
    ) -> Division | None: ...

    def de_competicion(self, competicion_id: CompeticionId) -> tuple[Division, ...]: ...

    def guardar(self, competicion_id: CompeticionId, division: Division) -> None: ...


@runtime_checkable
class RepositorioDeEnfrentamientos(Protocol):
    def obtener(self, enfrentamiento_id: EnfrentamientoId) -> Enfrentamiento | None: ...

    def de_fase(self, fase_id: FaseId) -> tuple[Enfrentamiento, ...]: ...

    def guardar(self, enfrentamiento: Enfrentamiento) -> None: ...

    def guardar_muchos(self, enfrentamientos: Sequence[Enfrentamiento]) -> None: ...

    def eliminar_de_fase(self, fase_id: FaseId) -> None: ...



@runtime_checkable
class RepositorioDeConcesiones(Protocol):
    def de_usuario(self, usuario_id: str) -> tuple[Concesion, ...]: ...

    def de_competicion(
        self, competicion_id: CompeticionId
    ) -> tuple[Concesion, ...]: ...

    def otorgar(self, concesion: Concesion) -> None: ...

    def revocar(
        self, usuario_id: str, competicion_id: CompeticionId | None = None
    ) -> None: ...


@runtime_checkable
class Autenticador(Protocol):
    """Quién es quien pide algo, y cómo se le invita.

    Sustituye a la tabla `usuarios` con bcrypt propio. La invitación por correo
    es lo que necesita el panel de Registradores: el Admin escribe un correo y
    el proveedor se encarga del resto.
    """

    def iniciar_sesion(self, email: str, contrasena: str) -> Sesion | None:
        """Sesión de quien acierta sus credenciales, o `None`.

        Devuelve el token además de la identidad porque es lo único que
        `identificar` acepta después. Quien implemente esto debe cumplir que
        `identificar(iniciar_sesion(...).token)` devuelva la misma identidad.
        """
        ...

    def identificar(self, token: str) -> Identidad | None:
        """Identidad tras un token de sesión, o `None` si no vale.

        El token es el de `Sesion`, no el id de usuario.
        """
        ...

    def por_email(self, email: str) -> Identidad | None: ...

    def invitar(self, email: str) -> Identidad:
        """Da de alta a alguien por correo y devuelve su identidad."""
        ...
