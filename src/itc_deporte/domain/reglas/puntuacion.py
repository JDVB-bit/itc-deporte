"""Cómo un marcador se convierte en puntos de clasificación.

El sistema anterior tenía una sola regla, escrita a mano dentro del bucle que
armaba la tabla: 3 puntos al que metiera más goles, 1 a cada uno si empataban.
Se aplicaba igual a los cuatro deportes, y por eso el voleibol era inexpresable.

Aquí la regla es un objeto que se elige por competición. Añadir una forma nueva
de puntuar no obliga a tocar ninguna de las que ya existen.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from ..enfrentamiento import Marcador
from ..errores import ReglaInvalida


@runtime_checkable
class SistemaDePuntuacion(Protocol):
    """Puntos de clasificación que reparte un marcador, en orden (local, visitante)."""

    def puntos(self, marcador: Marcador) -> tuple[int, int]: ...


@dataclass(frozen=True, slots=True)
class VictoriaDerrota:
    """Reparto clásico por resultado. Con los valores por defecto es el 3/1/0
    que el sistema aplicaba a todo."""

    victoria: int = 3
    empate: int = 1
    derrota: int = 0

    def __post_init__(self) -> None:
        if self.victoria < self.empate or self.empate < self.derrota:
            raise ReglaInvalida(
                "Ganar debe puntuar al menos como empatar, y empatar al menos "
                f"como perder: {self.victoria}/{self.empate}/{self.derrota}"
            )

    def puntos(self, marcador: Marcador) -> tuple[int, int]:
        if marcador.gana_local:
            return (self.victoria, self.derrota)
        if marcador.gana_visitante:
            return (self.derrota, self.victoria)
        return (self.empate, self.empate)


@dataclass(frozen=True, slots=True)
class PorSets:
    """Reparto según lo ajustado del resultado en sets.

    Es la regla de voleibol: ganar 3-0 o 3-1 da 3 puntos y 0 al rival, pero un
    3-2 da 2 al ganador y 1 al perdedor, porque un partido a cinco sets no es lo
    mismo que un paseo. `umbral_ajustado` es cuántos sets debe ganar el perdedor
    para que el resultado cuente como ajustado.

    Aquí no hay empate posible: si un marcador reparte los sets por igual, el
    dato está mal, no es un resultado legítimo.
    """

    victoria: int = 3
    victoria_ajustada: int = 2
    derrota_ajustada: int = 1
    derrota: int = 0
    umbral_ajustado: int = 2

    def __post_init__(self) -> None:
        if self.victoria < self.victoria_ajustada:
            raise ReglaInvalida(
                "Una victoria holgada no puede puntuar menos que una ajustada: "
                f"{self.victoria} < {self.victoria_ajustada}"
            )
        if self.derrota_ajustada < self.derrota:
            raise ReglaInvalida(
                "Una derrota ajustada no puede puntuar menos que una holgada: "
                f"{self.derrota_ajustada} < {self.derrota}"
            )
        if self.umbral_ajustado < 1:
            raise ReglaInvalida(
                f"El umbral de resultado ajustado debe ser al menos 1, "
                f"no {self.umbral_ajustado}."
            )

    def puntos(self, marcador: Marcador) -> tuple[int, int]:
        if marcador.es_empate:
            raise ReglaInvalida(
                f"Un partido por sets no puede quedar empatado: "
                f"{marcador.local}-{marcador.visitante}"
            )
        sets_perdedor = min(marcador.local, marcador.visitante)
        ajustado = sets_perdedor >= self.umbral_ajustado
        gana = self.victoria_ajustada if ajustado else self.victoria
        pierde = self.derrota_ajustada if ajustado else self.derrota
        if marcador.gana_local:
            return (gana, pierde)
        return (pierde, gana)
