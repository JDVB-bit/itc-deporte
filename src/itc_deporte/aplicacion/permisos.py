"""Quién puede hacer qué.

Tres roles. El Registrador es una **concesión con alcance**, no un rol global:
se otorga sobre una competición concreta, y fuera de ella su portador es un
visitante más. El Admin sí es global.

Esa distinción está impuesta por el tipo, no por convención: `Concesion` rechaza
un registrador sin competición y un admin con ella.

La comprobación vive aquí y la invocan los servicios. En el sistema anterior el
rol solo escondía botones (`app.py:350`, `app.py:414`), así que llegar a la
función por otro camino —o recargar con otro estado de sesión— saltaba el
control por completo.

Solo los **comandos** exigen actor. Las consultas no lo piden porque no hay nada
que restringir: el Visitante puede leerlo todo, y pedir una identidad para
devolver una tabla pública sería teatro.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..domain.identidades import CompeticionId
from .errores import ErrorDeAplicacion


class PermisoDenegado(ErrorDeAplicacion, PermissionError):
    """El actor no tiene permiso para la operación pedida."""


class Rol(Enum):
    VISITANTE = "visitante"
    REGISTRADOR = "registrador"
    ADMIN = "admin"


class Accion(Enum):
    """Lo que se puede pedirle al sistema."""

    LEER = "leer"
    INSCRIBIR_PARTICIPANTE = "inscribir_participante"
    REGISTRAR_RESULTADO = "registrar_resultado"
    SORTEAR = "sortear"
    CREAR_COMPETICION = "crear_competicion"
    ADMINISTRAR_COMPETICION = "administrar_competicion"
    GESTIONAR_REGISTRADORES = "gestionar_registradores"


#: Acciones que un registrador puede ejecutar en las competiciones que le fueron
#: asignadas. Todo lo demás —sortear, cambiar el estado, repartir permisos— es
#: del Admin.
DE_REGISTRADOR = frozenset(
    {Accion.LEER, Accion.INSCRIBIR_PARTICIPANTE, Accion.REGISTRAR_RESULTADO}
)

#: Lo que un registrador puede hacer **sin** estar dentro de una competición.
#:
#: Crear la suya. Va aparte porque su concesión es *por competición*, así que
#: preguntar por sus roles sin ámbito no encuentra ninguna y la acción quedaba
#: fuera de su alcance por construcción. Quien la crea queda como registrador de
#: ella —lo hace `ServicioDeCompeticiones.crear`—, y ahí se acaba: sortearla y
#: cambiarle el estado siguen siendo del Admin.
DE_REGISTRADOR_SIN_AMBITO = frozenset({Accion.CREAR_COMPETICION})


@dataclass(frozen=True, slots=True)
class Identidad:
    """Quién está pidiendo algo. Sus roles no viven aquí: se consultan."""

    usuario_id: str
    email: str | None = None

    def __post_init__(self) -> None:
        if not self.usuario_id:
            raise ErrorDeAplicacion("Una identidad necesita un usuario.")


#: Quien no se ha identificado. Puede leer y nada más.
ANONIMO = Identidad(usuario_id="anonimo")


@dataclass(frozen=True, slots=True)
class Sesion:
    """Quién entró y con qué se le vuelve a reconocer.

    El token existe como campo aparte porque **no es** el id de usuario. Con
    Supabase es un JWT, y pasarle un UUID a `identificar` devuelve `None`: la
    sesión se acepta y en la recarga siguiente el usuario aparece como anónimo.
    Es el fallo que se coló en producción, y venía de que el doble en memoria
    sí aceptaba el id como token, así que la suite entera lo daba por bueno.

    Devolver los dos juntos obliga a quien inicia sesión a guardar el que sirve.
    """

    identidad: Identidad
    token: str

    def __post_init__(self) -> None:
        if not self.token:
            raise ErrorDeAplicacion("Una sesión necesita un token.")


@dataclass(frozen=True, slots=True)
class Concesion:
    """`competicion_id` en `None` significa alcance global."""

    usuario_id: str
    rol: Rol
    competicion_id: CompeticionId | None = None

    def __post_init__(self) -> None:
        if not self.usuario_id:
            raise ErrorDeAplicacion("Una concesión necesita un usuario.")
        if self.rol is Rol.REGISTRADOR and self.competicion_id is None:
            raise ErrorDeAplicacion(
                "El registrador es una concesión por competición, no un rol global."
            )
        if self.rol is Rol.ADMIN and self.competicion_id is not None:
            raise ErrorDeAplicacion(
                "El rol de administrador es global: no se otorga por competición."
            )
        if self.rol is Rol.VISITANTE:
            raise ErrorDeAplicacion(
                "Visitante es lo que se es sin concesión alguna; no se otorga."
            )

    @property
    def es_global(self) -> bool:
        return self.competicion_id is None


class Politica:
    """Decide si una identidad puede ejecutar una acción."""

    def __init__(self, concesiones) -> None:
        self._concesiones = concesiones

    def roles_de(
        self, identidad: Identidad, competicion_id: CompeticionId | None = None
    ) -> frozenset[Rol]:
        """Roles efectivos de la identidad en el ámbito indicado.

        A quien no se ha identificado no se le preguntan sus concesiones: no
        puede tener ninguna, y `ANONIMO` no lleva un id de usuario de verdad.
        Preguntarlo tumbó la aplicación en producción —`usuario_id` es `uuid`
        en la base y Postgres rechaza `'anonimo'`—, y el fallo solo aparecía
        con la base vacía, que es cuando un visitante llega a este camino.
        """
        if identidad is ANONIMO:
            return frozenset({Rol.VISITANTE})
        otorgados = {
            concesion.rol
            for concesion in self._concesiones.de_usuario(identidad.usuario_id)
            if concesion.es_global or concesion.competicion_id == competicion_id
        }
        return frozenset(otorgados | {Rol.VISITANTE})

    def es_registrador_en_alguna(self, identidad: Identidad) -> bool:
        """Si tiene concesión de registrador en alguna competición, la que sea.

        `roles_de` no sirve para esto: filtra por ámbito, y la concesión de un
        registrador siempre lleva competición, así que preguntando sin ámbito
        nunca aparece. A quien no se ha identificado no se le pregunta, por lo
        mismo que en `roles_de`.
        """
        if identidad is ANONIMO:
            return False
        return any(
            concesion.rol is Rol.REGISTRADOR
            for concesion in self._concesiones.de_usuario(identidad.usuario_id)
        )

    def puede(
        self,
        identidad: Identidad,
        accion: Accion,
        competicion_id: CompeticionId | None = None,
    ) -> bool:
        roles = self.roles_de(identidad, competicion_id)
        if Rol.ADMIN in roles:
            return True
        if Rol.REGISTRADOR in roles and accion in DE_REGISTRADOR:
            return True
        if accion in DE_REGISTRADOR_SIN_AMBITO and self.es_registrador_en_alguna(
            identidad
        ):
            return True
        return accion is Accion.LEER

    def exigir(
        self,
        identidad: Identidad,
        accion: Accion,
        competicion_id: CompeticionId | None = None,
    ) -> None:
        """Lanza `PermisoDenegado` si la identidad no puede."""
        if self.puede(identidad, accion, competicion_id):
            return
        ambito = (
            f" en la competición {competicion_id!r}" if competicion_id else ""
        )
        raise PermisoDenegado(
            f"{identidad.usuario_id!r} no puede {accion.value}{ambito}."
        )
