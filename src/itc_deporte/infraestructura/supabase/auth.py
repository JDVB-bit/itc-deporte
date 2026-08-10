"""Supabase Auth como proveedor de identidad.

Sustituye a la tabla `usuarios` con bcrypt propio, que obligaba a mantener a mano
el hasheo, el alta y la recuperación de contraseña, y no ofrecía forma de invitar
a nadie por correo —justo lo que el panel de Registradores necesita.

Lo que se gana además del correo: `auth.uid()` disponible dentro de Postgres, que
es lo que permite escribir las políticas RLS de `permisos.sql` como segunda línea
de defensa por debajo de la capa de servicio.

**Estado de verificación.** La lógica de traducción está cubierta con un doble
del cliente, y la forma de la API —`list_users`, `create_user`, `.user.id`— quedó
confirmada contra una instancia real al montar las fixtures de contrato. El
adaptador completo se ejercita en `tests/infraestructura/test_auth_supabase.py`
bajo el marcador `supabase`.

`invitar` y `por_email` usan la API de administración, que exige la clave
`service_role`. No debe llegar nunca al navegador.

**Sobre el límite de invitaciones.** `invite_user_by_email` envía un correo de
verdad, y Supabase limita cuántos se pueden mandar por hora —unos cuatro en el
plan gratuito. Un Admin que dé de alta varios registradores seguidos se topará
con ello. Se traduce a `LimiteDeInvitaciones` para que la interfaz pueda decir
"espera un rato" en lugar de mostrar un error de red.
"""

from __future__ import annotations

from typing import Any, Protocol

from ...aplicacion.permisos import Identidad, Sesion


class LimiteDeInvitaciones(RuntimeError):
    """Supabase rechazó la invitación por exceso de correos enviados.

    No es un fallo del sistema: es una cuota del proveedor. Reintentar más tarde
    funciona, y dar de alta por usuario (`otorgar_por_usuario`) la evita.
    """


class ClienteSupabase(Protocol):
    """Lo mínimo que este adaptador necesita del cliente.

    Declararlo permite probar la traducción sin arrastrar la biblioteca entera.
    """

    auth: Any


class AutenticadorSupabase:
    def __init__(self, cliente: ClienteSupabase) -> None:
        self._cliente = cliente

    def iniciar_sesion(self, email: str, contrasena: str) -> Sesion | None:
        """Correo y contraseña contra Supabase Auth.

        Unas credenciales que no valen no son un error del sistema: son alguien
        que se equivocó al escribir.

        Devuelve el `access_token` de la sesión, que es lo único que
        `identificar` sabe leer. Antes solo devolvía la identidad y quien
        llamaba guardaba el UUID; `get_user` lo rechazaba y el usuario quedaba
        como anónimo desde la primera recarga.
        """
        try:
            respuesta = self._cliente.auth.sign_in_with_password(
                {"email": email.strip(), "password": contrasena}
            )
        except Exception:
            return None
        identidad = _a_identidad(getattr(respuesta, "user", None))
        token = getattr(getattr(respuesta, "session", None), "access_token", None)
        if identidad is None or not token:
            return None
        return Sesion(identidad, token=token)

    def identificar(self, token: str) -> Identidad | None:
        """Identidad tras un JWT de sesión, o `None` si no vale."""
        if not token:
            return None
        try:
            respuesta = self._cliente.auth.get_user(token)
        except Exception:
            # Un token caducado o falsificado no es un error del sistema: es
            # sencillamente alguien sin identificar.
            return None
        return _a_identidad(getattr(respuesta, "user", None))

    def por_email(self, email: str) -> Identidad | None:
        for usuario in self._listar_usuarios():
            if getattr(usuario, "email", None) == email:
                return _a_identidad(usuario)
        return None

    def por_id(self, usuario_id: str) -> Identidad | None:
        """Quién es ese id. Un id que ya no existe no es un error del sistema.

        Una concesión sobrevive a su usuario el tiempo que tarde el `on delete
        cascade`, y el panel tiene que poder pintar esa fila igual.
        """
        try:
            respuesta = self._cliente.auth.admin.get_user_by_id(usuario_id)
        except Exception:
            return None
        return _a_identidad(getattr(respuesta, "user", None))

    def invitar(self, email: str) -> Identidad:
        """Da de alta por correo. Si ya existe, devuelve al de siempre."""
        existente = self.por_email(email)
        if existente is not None:
            return existente
        try:
            respuesta = self._cliente.auth.admin.invite_user_by_email(email)
        except Exception as error:
            if _es_limite_de_correos(error):
                raise LimiteDeInvitaciones(
                    f"Supabase no aceptó invitar a {email!r}: se ha alcanzado el "
                    "límite de correos por hora. Inténtalo más tarde, o concede "
                    "el permiso por usuario si ya tiene cuenta."
                ) from error
            raise
        identidad = _a_identidad(getattr(respuesta, "user", None))
        if identidad is None:
            raise RuntimeError(f"Supabase no devolvió un usuario al invitar a {email!r}.")
        return identidad

    def _listar_usuarios(self) -> list[Any]:
        respuesta = self._cliente.auth.admin.list_users()
        # `list_users` ha devuelto tanto una lista como un objeto con `.users`
        # según la versión de la biblioteca; se aceptan ambas formas.
        if isinstance(respuesta, list):
            return respuesta
        return list(getattr(respuesta, "users", []))


def _es_limite_de_correos(error: Exception) -> bool:
    """Distingue la cuota de envío de cualquier otro fallo de la API."""
    if getattr(error, "status", None) == 429:
        return True
    return "rate limit" in str(error).lower()


def _a_identidad(usuario: Any) -> Identidad | None:
    if usuario is None:
        return None
    usuario_id = getattr(usuario, "id", None)
    if not usuario_id:
        return None
    return Identidad(usuario_id=str(usuario_id), email=getattr(usuario, "email", None))
