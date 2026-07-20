"""La fila de una tabla de posiciones.

Aquí solo vive la estructura: quién es y qué acumuló. Cómo se construye a partir
de los enfrentamientos es la Fase 3, y cómo se ordena cuando hay igualdad son
los criterios de `reglas/desempate.py`.

A diferencia de los diccionarios sueltos que producía `calcular_tabla`, la fila
identifica al participante por id y valida su propia coherencia.
"""

from __future__ import annotations

from dataclasses import dataclass

from .errores import ErrorDeDominio
from .participante import ParticipanteId


@dataclass(frozen=True, slots=True)
class FilaClasificacion:
    """`a_favor` y `en_contra` son genéricos a propósito: goles en fútbol, sets
    en voleibol, carreras en béisbol. El motor no necesita saber cuál."""

    participante_id: ParticipanteId
    jugados: int = 0
    ganados: int = 0
    empatados: int = 0
    perdidos: int = 0
    a_favor: int = 0
    en_contra: int = 0
    puntos: int = 0

    def __post_init__(self) -> None:
        if not self.participante_id:
            raise ErrorDeDominio("Una fila necesita un participante.")
        negativos = {
            "jugados": self.jugados,
            "ganados": self.ganados,
            "empatados": self.empatados,
            "perdidos": self.perdidos,
            "a_favor": self.a_favor,
            "en_contra": self.en_contra,
        }
        for campo, valor in negativos.items():
            if valor < 0:
                raise ErrorDeDominio(f"{campo} no puede ser negativo: {valor}")
        resultados = self.ganados + self.empatados + self.perdidos
        if resultados != self.jugados:
            raise ErrorDeDominio(
                f"Los resultados de {self.participante_id!r} no cuadran con los "
                f"partidos jugados: {resultados} != {self.jugados}"
            )

    @property
    def diferencia(self) -> int:
        return self.a_favor - self.en_contra
