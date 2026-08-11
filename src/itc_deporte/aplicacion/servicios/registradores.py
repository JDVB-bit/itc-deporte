"""El panel de Registradores: quién puede cargar resultados en qué competición.

El Admin añade a alguien por correo —y el proveedor de identidad se encarga de
invitarlo si aún no existe— o por usuario si no hay correo. La concesión es
siempre sobre una competición concreta.

Aviso sobre invitar por correo: el proveedor limita cuántos correos se envían
por hora (unos cuatro en el plan gratuito de Supabase). Dar de alta a varios
registradores seguidos puede toparse con ese tope; el adaptador lo traduce a
`LimiteDeInvitaciones`. A quien ya tenga cuenta se le concede sin enviar nada,
y `otorgar_por_usuario` no envía correo en ningún caso.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...domain.identidades import CompeticionId
from ..errores import NoEncontrado
from ..permisos import Accion, Concesion, Identidad, Politica, Rol
from ..puertos import (
    Autenticador,
    RepositorioDeCompeticiones,
    RepositorioDeConcesiones,
)


@dataclass(frozen=True, slots=True)
class RegistradorConcedido:
    """Quién tiene el permiso, con el correo por el que se le reconoce.

    El panel concede por correo y listaba por id, así que enseñaba UUID crudos:
    no había manera de saber a quién se le estaba revocando el permiso. El
    correo puede faltar —un usuario borrado, una cuenta sin dirección—, y en ese
    caso queda el id, que es mejor que nada.
    """

    usuario_id: str
    email: str | None = None

    @property
    def etiqueta(self) -> str:
        return self.email or self.usuario_id


class ServicioDeRegistradores:
    def __init__(
        self,
        competiciones: RepositorioDeCompeticiones,
        concesiones: RepositorioDeConcesiones,
        autenticador: Autenticador,
        politica: Politica,
    ) -> None:
        self._competiciones = competiciones
        self._concesiones = concesiones
        self._autenticador = autenticador
        self._politica = politica

    def de_competicion(
        self, competicion_id: CompeticionId
    ) -> tuple[RegistradorConcedido, ...]:
        """Quién puede registrar en esta competición, por su correo."""
        return tuple(
            RegistradorConcedido(concesion.usuario_id, self._correo(concesion.usuario_id))
            for concesion in self._concesiones.de_competicion(competicion_id)
            if concesion.rol is Rol.REGISTRADOR
        )

    def _correo(self, usuario_id: str) -> str | None:
        identidad = self._autenticador.por_id(usuario_id)
        return identidad.email if identidad else None

    def otorgar_por_email(
        self, actor: Identidad, competicion_id: CompeticionId, email: str
    ) -> Concesion:
        """Invita al correo si hace falta y le concede el registro."""
        self._exigir(actor, competicion_id)
        identidad = self._autenticador.invitar(email.strip())
        return self._otorgar(identidad.usuario_id, competicion_id)

    def otorgar_por_usuario(
        self, actor: Identidad, competicion_id: CompeticionId, usuario_id: str
    ) -> Concesion:
        """Para cuando no hay correo con el que invitar."""
        self._exigir(actor, competicion_id)
        return self._otorgar(usuario_id, competicion_id)

    def revocar(
        self, actor: Identidad, competicion_id: CompeticionId, usuario_id: str
    ) -> None:
        self._exigir(actor, competicion_id)
        self._concesiones.revocar(usuario_id, competicion_id)

    # ── Interno ─────────────────────────────────────────────────────────────

    def _exigir(self, actor: Identidad, competicion_id: CompeticionId) -> None:
        if self._competiciones.obtener(competicion_id) is None:
            raise NoEncontrado(f"No existe la competición {competicion_id!r}.")
        self._politica.exigir(
            actor, Accion.GESTIONAR_REGISTRADORES, competicion_id
        )

    def _otorgar(self, usuario_id: str, competicion_id: CompeticionId) -> Concesion:
        concesion = Concesion(
            usuario_id=usuario_id, rol=Rol.REGISTRADOR, competicion_id=competicion_id
        )
        self._concesiones.otorgar(concesion)
        return concesion
