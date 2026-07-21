"""Implementaciones en memoria de concesiones e identidad.

Son con las que corre la suite. El adaptador real de Supabase Auth vive en
`supabase/auth.py` y cumple el mismo contrato.
"""

from __future__ import annotations

from typing import Iterable

from ..aplicacion.permisos import Concesion, Identidad
from ..domain.identidades import CompeticionId


class ConcesionesEnMemoria:
    def __init__(self, concesiones: Iterable[Concesion] = ()) -> None:
        self._concesiones: list[Concesion] = list(concesiones)

    def de_usuario(self, usuario_id: str) -> tuple[Concesion, ...]:
        return tuple(c for c in self._concesiones if c.usuario_id == usuario_id)

    def de_competicion(self, competicion_id: CompeticionId) -> tuple[Concesion, ...]:
        return tuple(
            c for c in self._concesiones if c.competicion_id == competicion_id
        )

    def otorgar(self, concesion: Concesion) -> None:
        self.revocar(concesion.usuario_id, concesion.competicion_id)
        self._concesiones.append(concesion)

    def revocar(
        self, usuario_id: str, competicion_id: CompeticionId | None = None
    ) -> None:
        self._concesiones = [
            c
            for c in self._concesiones
            if not (c.usuario_id == usuario_id and c.competicion_id == competicion_id)
        ]


class AutenticadorEnMemoria:
    """Un directorio de identidades sin contraseñas: los tests no las necesitan."""

    def __init__(self, identidades: Iterable[Identidad] = ()) -> None:
        self._por_id = {i.usuario_id: i for i in identidades}

    def iniciar_sesion(self, email: str, contrasena: str) -> Identidad | None:
        """Sin contraseñas: basta con que el correo exista.

        Los tests prueban permisos, no criptografía; comprobar una contraseña
        aquí solo añadiría ruido.
        """
        return self.por_email(email.strip())

    def identificar(self, token: str) -> Identidad | None:
        """El token es el propio id de usuario, que basta para probar permisos."""
        return self._por_id.get(token)

    def por_email(self, email: str) -> Identidad | None:
        return next((i for i in self._por_id.values() if i.email == email), None)

    def invitar(self, email: str) -> Identidad:
        existente = self.por_email(email)
        if existente is not None:
            return existente
        identidad = Identidad(usuario_id=f"usuario-{len(self._por_id) + 1}", email=email)
        self._por_id[identidad.usuario_id] = identidad
        return identidad
