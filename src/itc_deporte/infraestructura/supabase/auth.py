"""Supabase Auth como proveedor de identidad.

Sustituye a la tabla `usuarios` con bcrypt propio, que obligaba a mantener a mano
el hasheo, el alta y la recuperación de contraseña, y no ofrecía forma de invitar
a nadie por correo —justo lo que el panel de Registradores necesita.

Lo que se gana además del correo: `auth.uid()` disponible dentro de Postgres, que
es lo que permite escribir las políticas RLS de `permisos.sql` como segunda línea
de defensa por debajo de la capa de servicio.

**Estado de verificación.** La lógica de traducción de este módulo está cubierta
por tests con un doble del cliente. Lo que ningún test de este repositorio
comprueba es que las llamadas coincidan con la API real de `supabase-py`: eso
exige una instancia de verdad y son los tests marcados con `@pytest.mark.supabase`,
que no se han ejecutado nunca. Antes de confiar en este adaptador en producción,
hay que correrlos contra un proyecto real.

`invitar` y `por_email` usan la API de administración, que exige la clave
`service_role`. No debe llegar nunca al navegador.
"""

from __future__ import annotations

from typing import Any, Protocol

from ...aplicacion.permisos import Identidad


class ClienteSupabase(Protocol):
    """Lo mínimo que este adaptador necesita del cliente.

    Declararlo permite probar la traducción sin arrastrar la biblioteca entera.
    """

    auth: Any


class AutenticadorSupabase:
    def __init__(self, cliente: ClienteSupabase) -> None:
        self._cliente = cliente

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

    def invitar(self, email: str) -> Identidad:
        """Da de alta por correo. Si ya existe, devuelve al de siempre."""
        existente = self.por_email(email)
        if existente is not None:
            return existente
        respuesta = self._cliente.auth.admin.invite_user_by_email(email)
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


def _a_identidad(usuario: Any) -> Identidad | None:
    if usuario is None:
        return None
    usuario_id = getattr(usuario, "id", None)
    if not usuario_id:
        return None
    return Identidad(usuario_id=str(usuario_id), email=getattr(usuario, "email", None))
