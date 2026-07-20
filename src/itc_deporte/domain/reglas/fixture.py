"""Cómo se arma el calendario de una fase.

Un fixture es un **plan de emparejamientos**, no una lista de entidades: dice
quién juega contra quién y en qué jornada, y deja para la capa de aplicación el
asignarle ids y fechas. Por eso produce `Cruce` y no `Enfrentamiento`.

Tres cosas que estaban cableadas pasan aquí a ser configuración explícita:

- **Las 7 jornadas.** El generador anterior repetía o truncaba el round-robin
  hasta dejar exactamente 7, viniera de donde viniera. Ahora produce las n-1
  jornadas naturales, y quien necesite un número fijo lo pide con
  `jornadas_forzadas`.
- **El BYE.** Antes era la cadena `"BYE"` colada entre los equipos, que luego se
  filtraba comparando strings. Ahora la jornada dice explícitamente quién
  descansa.
- **El tope de 16.** El cuadro crece con los participantes en vez de recortarse.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence, runtime_checkable

from ..errores import ReglaInvalida
from ..participante import ParticipanteId


@dataclass(frozen=True, slots=True)
class Cruce:
    local: ParticipanteId
    visitante: ParticipanteId

    def __post_init__(self) -> None:
        if self.local == self.visitante:
            raise ReglaInvalida(
                f"Un participante no puede enfrentarse a sí mismo: {self.local!r}"
            )

    def invertido(self) -> Cruce:
        return Cruce(self.visitante, self.local)


@dataclass(frozen=True, slots=True)
class Jornada:
    """`descansan` recoge a quienes no juegan: el impar del round-robin o los
    que entran con bye a un cuadro incompleto."""

    numero: int
    cruces: tuple[Cruce, ...] = ()
    descansan: tuple[ParticipanteId, ...] = ()

    def __post_init__(self) -> None:
        if self.numero < 1:
            raise ReglaInvalida(f"Número de jornada inválido: {self.numero}")

    @property
    def participantes(self) -> tuple[ParticipanteId, ...]:
        jugando = tuple(p for c in self.cruces for p in (c.local, c.visitante))
        return jugando + self.descansan


@dataclass(frozen=True, slots=True)
class ConfigFixture:
    """`jornadas_forzadas` es el antiguo `range(7)`, ahora explícito y opcional."""

    vueltas: int = 1
    jornadas_forzadas: int | None = None

    def __post_init__(self) -> None:
        if self.vueltas < 1:
            raise ReglaInvalida(f"Se necesita al menos una vuelta, no {self.vueltas}.")
        if self.jornadas_forzadas is not None and self.jornadas_forzadas < 1:
            raise ReglaInvalida(
                f"No se puede forzar un calendario de {self.jornadas_forzadas} jornadas."
            )


@runtime_checkable
class GeneradorDeFixture(Protocol):
    def generar(
        self,
        participantes: Sequence[ParticipanteId],
        config: ConfigFixture,
    ) -> tuple[Jornada, ...]: ...


def _validar(participantes: Sequence[ParticipanteId]) -> list[ParticipanteId]:
    lista = list(participantes)
    if len(set(lista)) != len(lista):
        raise ReglaInvalida("Hay participantes repetidos en el sorteo.")
    return lista


@dataclass(frozen=True, slots=True)
class RoundRobin:
    """Todos contra todos, por el método del círculo.

    Con un número impar de participantes se añade un hueco que rota, de modo que
    en cada jornada descansa uno distinto. La localía se alterna entre jornadas
    para que nadie juegue siempre en el mismo rol.
    """

    def generar(
        self,
        participantes: Sequence[ParticipanteId],
        config: ConfigFixture = ConfigFixture(),
    ) -> tuple[Jornada, ...]:
        lista = _validar(participantes)
        if len(lista) < 2:
            return ()

        rueda: list[ParticipanteId | None] = list(lista)
        if len(rueda) % 2:
            rueda.append(None)  # el hueco que hace descansar a uno por jornada

        n = len(rueda)
        fijo, rotativos = rueda[0], rueda[1:]
        vuelta_base: list[tuple[tuple[Cruce, ...], tuple[ParticipanteId, ...]]] = []

        for ronda in range(n - 1):
            circulo = [fijo] + rotativos
            cruces: list[Cruce] = []
            descansan: list[ParticipanteId] = []
            for i in range(n // 2):
                uno, otro = circulo[i], circulo[n - 1 - i]
                if uno is None or otro is None:
                    descansan.append(otro if uno is None else uno)
                    continue
                cruces.append(
                    Cruce(uno, otro) if ronda % 2 == 0 else Cruce(otro, uno)
                )
            vuelta_base.append((tuple(cruces), tuple(descansan)))
            rotativos = [rotativos[-1]] + rotativos[:-1]

        calendario: list[tuple[tuple[Cruce, ...], tuple[ParticipanteId, ...]]] = []
        for vuelta in range(config.vueltas):
            for cruces, descansan in vuelta_base:
                if vuelta % 2:  # la vuelta de regreso invierte la localía
                    cruces = tuple(c.invertido() for c in cruces)
                calendario.append((cruces, descansan))

        if config.jornadas_forzadas is not None:
            calendario = [
                calendario[i % len(calendario)]
                for i in range(config.jornadas_forzadas)
            ]

        return tuple(
            Jornada(numero, cruces, descansan)
            for numero, (cruces, descansan) in enumerate(calendario, start=1)
        )


def tamano_de_cuadro(participantes: int) -> int:
    """Potencia de dos que acoge a todos. Sin el tope de 16 del bracket anterior."""
    if participantes < 2:
        raise ReglaInvalida(
            f"Un cuadro necesita al menos 2 participantes, no {participantes}."
        )
    size = 2
    while size < participantes:
        size *= 2
    return size


def orden_de_siembra(tamano: int) -> tuple[int, ...]:
    """Siembra estándar: el 1 se cruza con el último, el 2 con el penúltimo…

    Las parejas quedan en posiciones consecutivas, y cada una suma `tamano + 1`.
    Así los mejores clasificados no se eliminan entre sí antes de tiempo.
    """
    if tamano < 2 or tamano & (tamano - 1):
        raise ReglaInvalida(f"El tamaño del cuadro debe ser potencia de dos: {tamano}")
    siembra = [1]
    while len(siembra) < tamano:
        limite = len(siembra) * 2
        siembra = [s for actual in siembra for s in (actual, limite + 1 - actual)]
    return tuple(siembra)


@dataclass(frozen=True, slots=True)
class EliminacionDirecta:
    """Primera ronda de un cuadro, sembrada por orden de clasificación.

    Espera a los participantes ya ordenados: el primero es el mejor sembrado. Si
    no llenan una potencia de dos, los mejores entran con bye y aparecen en
    `descansan`; la propagación por el cuadro es cosa del motor (Fase 3).
    """

    def generar(
        self,
        participantes: Sequence[ParticipanteId],
        config: ConfigFixture = ConfigFixture(),
    ) -> tuple[Jornada, ...]:
        lista = _validar(participantes)
        if len(lista) < 2:
            return ()

        tamano = tamano_de_cuadro(len(lista))
        siembra = orden_de_siembra(tamano)
        cruces: list[Cruce] = []
        descansan: list[ParticipanteId] = []

        for i in range(0, tamano, 2):
            pareja = [
                sembrado
                for posicion in (siembra[i], siembra[i + 1])
                if (sembrado := self._sembrado(lista, posicion)) is not None
            ]
            if len(pareja) == 2:
                cruces.append(Cruce(*pareja))
            elif pareja:
                descansan.append(pareja[0])

        return (Jornada(1, tuple(cruces), tuple(descansan)),)

    @staticmethod
    def _sembrado(
        lista: Sequence[ParticipanteId], posicion: int
    ) -> ParticipanteId | None:
        return lista[posicion - 1] if posicion <= len(lista) else None
