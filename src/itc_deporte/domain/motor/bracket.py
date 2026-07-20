"""Cuadro de eliminación directa, con propagación en memoria.

El bracket anterior (`data.py:487-679`) llevaba desde su commit sin conectar a
la interfaz, y propagaba a los ganadores con una escritura por casilla: cada
resultado disparaba una cascada de `UPDATE`s. Aquí el cuadro entero es un valor
inmutable; cargar un resultado devuelve un cuadro nuevo ya propagado, y quien lo
persista decide si eso son una escritura o cien.

Dos reglas del cuadro que antes estaban implícitas y ahora son explícitas:

- **Bye.** Una casilla con un solo participante lo hace avanzar sin jugar.
- **Un empate no resuelve.** El cuadro se queda esperando, porque no hay forma
  de avanzar a nadie. Antes esto devolvía silenciosamente "sin ganador" y el
  cuadro quedaba encallado sin decir por qué.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Sequence

from ..enfrentamiento import Marcador
from ..errores import ErrorDeDominio
from ..participante import ParticipanteId
from ..reglas.fixture import orden_de_siembra, tamano_de_cuadro

_NOMBRES = {1: "Final", 2: "Semifinal", 4: "Cuartos de final", 8: "Octavos de final"}


def nombre_de_ronda(partidos: int) -> str:
    """Cómo se llama una ronda de `partidos` cruces."""
    if partidos < 1:
        raise ErrorDeDominio(f"Una ronda no puede tener {partidos} partidos.")
    if partidos in _NOMBRES:
        return _NOMBRES[partidos]
    if partidos == 16:
        return "Dieciseisavos de final"
    return f"Ronda de {partidos * 2}"


@dataclass(frozen=True, slots=True)
class SlotDeBracket:
    """Una casilla del cuadro: un cruce con su posición."""

    ronda: int
    posicion: int
    local: ParticipanteId | None = None
    visitante: ParticipanteId | None = None
    marcador: Marcador | None = None

    @property
    def es_bye(self) -> bool:
        return (self.local is None) != (self.visitante is None)

    @property
    def listo(self) -> bool:
        """Tiene a los dos contendientes y se puede jugar."""
        return self.local is not None and self.visitante is not None

    def ganador(self) -> ParticipanteId | None:
        if self.es_bye:
            return self.local if self.local is not None else self.visitante
        if not self.listo or self.marcador is None:
            return None
        if self.marcador.gana_local:
            return self.local
        if self.marcador.gana_visitante:
            return self.visitante
        return None  # empate: el cuadro no puede avanzar a nadie


@dataclass(frozen=True, slots=True)
class Bracket:
    rondas: tuple[tuple[SlotDeBracket, ...], ...]

    def __post_init__(self) -> None:
        if not self.rondas:
            raise ErrorDeDominio("Un cuadro necesita al menos una ronda.")
        if len(self.rondas[-1]) != 1:
            raise ErrorDeDominio("La última ronda del cuadro debe ser una final.")

    @classmethod
    def desde_clasificados(cls, participantes: Sequence[ParticipanteId]) -> Bracket:
        """Arma el cuadro sembrando a los participantes por orden de clasificación.

        El primero es el mejor sembrado. Si no llenan una potencia de dos, los
        mejores entran con bye.
        """
        lista = list(participantes)
        if len(set(lista)) != len(lista):
            raise ErrorDeDominio("Hay participantes repetidos en el cuadro.")
        if len(lista) < 2:
            raise ErrorDeDominio(
                f"Un cuadro necesita al menos 2 participantes, no {len(lista)}."
            )

        tamano = tamano_de_cuadro(len(lista))
        siembra = orden_de_siembra(tamano)
        sembrado = lambda pos: lista[pos - 1] if pos <= len(lista) else None

        primera = tuple(
            SlotDeBracket(
                ronda=0,
                posicion=i // 2,
                local=sembrado(siembra[i]),
                visitante=sembrado(siembra[i + 1]),
            )
            for i in range(0, tamano, 2)
        )

        rondas = [primera]
        partidos = len(primera) // 2
        numero = 1
        while partidos >= 1:
            rondas.append(
                tuple(SlotDeBracket(ronda=numero, posicion=p) for p in range(partidos))
            )
            partidos //= 2
            numero += 1

        return cls(_propagar(tuple(rondas)))

    @property
    def total_rondas(self) -> int:
        return len(self.rondas)

    def nombre_de(self, ronda: int) -> str:
        return nombre_de_ronda(len(self._ronda(ronda)))

    def _ronda(self, ronda: int) -> tuple[SlotDeBracket, ...]:
        if not 0 <= ronda < len(self.rondas):
            raise ErrorDeDominio(
                f"El cuadro no tiene ronda {ronda}: va de 0 a {len(self.rondas) - 1}."
            )
        return self.rondas[ronda]

    def slot(self, ronda: int, posicion: int) -> SlotDeBracket:
        casillas = self._ronda(ronda)
        if not 0 <= posicion < len(casillas):
            raise ErrorDeDominio(
                f"La ronda {ronda} no tiene casilla {posicion}: "
                f"va de 0 a {len(casillas) - 1}."
            )
        return casillas[posicion]

    def con_resultado(
        self, ronda: int, posicion: int, marcador: Marcador
    ) -> Bracket:
        """Devuelve un cuadro nuevo con ese resultado y ya propagado."""
        casilla = self.slot(ronda, posicion)
        if not casilla.listo:
            raise ErrorDeDominio(
                f"La casilla {posicion} de la ronda {ronda} todavía no tiene "
                "a sus dos contendientes."
            )
        rondas = [list(r) for r in self.rondas]
        rondas[ronda][posicion] = replace(casilla, marcador=marcador)
        return Bracket(_propagar(tuple(tuple(r) for r in rondas)))

    def campeon(self) -> ParticipanteId | None:
        return self.rondas[-1][0].ganador()

    def pendientes(self) -> tuple[SlotDeBracket, ...]:
        """Cruces jugables cuyo resultado falta."""
        return tuple(
            casilla
            for ronda in self.rondas
            for casilla in ronda
            if casilla.listo and casilla.ganador() is None
        )


def _propagar(rondas: tuple[tuple[SlotDeBracket, ...], ...]) -> tuple[tuple[SlotDeBracket, ...], ...]:
    """Lleva a cada ganador a su casilla de la ronda siguiente, en cascada.

    Si al recalcular una casilla cambian sus contendientes, se descarta su
    marcador: ya no es el mismo partido. Es lo que hace que corregir un
    resultado de octavos no deje resultados fantasma en cuartos.
    """
    resultado = [tuple(rondas[0])]
    for numero in range(1, len(rondas)):
        previa = resultado[numero - 1]
        actual = []
        for casilla in rondas[numero]:
            local = previa[casilla.posicion * 2].ganador()
            visitante = previa[casilla.posicion * 2 + 1].ganador()
            cambio = (local, visitante) != (casilla.local, casilla.visitante)
            actual.append(
                replace(
                    casilla,
                    local=local,
                    visitante=visitante,
                    marcador=None if cambio else casilla.marcador,
                )
            )
        resultado.append(tuple(actual))
    return tuple(resultado)
