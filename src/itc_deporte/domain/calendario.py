"""Cuándo se juega.

Antes: `dias = (5 - hoy.weekday()) % 7 or 7` y la cadena `"15:00"` escritas a
mano dentro del sorteo. Sábado y las tres de la tarde eran una decisión del
código, no del organizador.

Vive en su propio módulo porque lo necesitan tanto la competición como la
plantilla, y si colgara de cualquiera de las dos se formaría un ciclo.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from .errores import ErrorDeDominio


@dataclass(frozen=True, slots=True)
class Calendario:
    """`dia_de_la_semana` sigue el convenio de `date.weekday()`: 0 es lunes y 5
    sábado. En `None`, la primera jornada cae en la fecha de arranque."""

    dia_de_la_semana: int | None = None
    hora: dt.time = dt.time(15, 0)
    cadencia_dias: int = 7

    def __post_init__(self) -> None:
        if self.dia_de_la_semana is not None and not 0 <= self.dia_de_la_semana <= 6:
            raise ErrorDeDominio(
                f"Día de la semana inválido: {self.dia_de_la_semana}. Va de 0 a 6."
            )
        if self.cadencia_dias < 1:
            raise ErrorDeDominio(f"Cadencia inválida: {self.cadencia_dias} días.")

    def fechas(self, desde: dt.date, cantidad: int) -> tuple[dt.datetime, ...]:
        """Las `cantidad` primeras fechas de juego a partir de `desde`.

        Si hay día fijado, la primera cae en el siguiente que corresponda, nunca
        el mismo `desde`: es el comportamiento del sorteo actual, que estando en
        sábado programaba para el sábado siguiente.
        """
        if cantidad < 0:
            raise ErrorDeDominio(f"No se pueden generar {cantidad} fechas.")
        inicio = desde
        if self.dia_de_la_semana is not None:
            avance = (self.dia_de_la_semana - desde.weekday()) % 7
            inicio = desde + dt.timedelta(days=avance or 7)
        return tuple(
            dt.datetime.combine(
                inicio + dt.timedelta(days=self.cadencia_dias * i), self.hora
            )
            for i in range(cantidad)
        )
