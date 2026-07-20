"""Cómo se ordena la tabla y cómo se rompen los empates.

El sistema anterior tenía un único desempate, incrustado en la clave de
ordenación: puntos, luego diferencia, luego goles a favor. Aquí los criterios
son objetos que se componen en una lista ordenada, configurable por competición.

**Un criterio recibe el grupo de empatados, no solo su fila.** Es lo que hace
posible el enfrentamiento directo, que por definición no puede decidirse mirando
una fila aislada: hay que saber contra quién se está empatado para consultar los
partidos entre ellos.

Los criterios se aplican por refinamiento sucesivo: el primero parte la tabla en
bloques, el segundo desempata dentro de cada bloque, y así. Un criterio solo ve
el bloque que le toca, de modo que el enfrentamiento directo recibe exactamente
a los participantes que siguen igualados a esa altura.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import groupby
from typing import Iterable, Protocol, Sequence, runtime_checkable

from ..clasificacion import FilaClasificacion
from ..enfrentamiento import Enfrentamiento
from ..participante import ParticipanteId
from .puntuacion import SistemaDePuntuacion


@dataclass(frozen=True, slots=True)
class ContextoDeDesempate:
    """Lo que un criterio necesita saber además de la fila que evalúa."""

    empatados: tuple[ParticipanteId, ...]
    enfrentamientos: tuple[Enfrentamiento, ...] = ()


@runtime_checkable
class CriterioDeDesempate(Protocol):
    """Devuelve un valor donde **más alto es mejor**."""

    def valor(self, fila: FilaClasificacion, contexto: ContextoDeDesempate) -> int: ...


@dataclass(frozen=True, slots=True)
class PorPuntos:
    def valor(self, fila: FilaClasificacion, contexto: ContextoDeDesempate) -> int:
        return fila.puntos


@dataclass(frozen=True, slots=True)
class PorDiferencia:
    def valor(self, fila: FilaClasificacion, contexto: ContextoDeDesempate) -> int:
        return fila.diferencia


@dataclass(frozen=True, slots=True)
class PorAFavor:
    def valor(self, fila: FilaClasificacion, contexto: ContextoDeDesempate) -> int:
        return fila.a_favor


@dataclass(frozen=True, slots=True)
class PorEnContra:
    """Menos encajado es mejor, de ahí el signo."""

    def valor(self, fila: FilaClasificacion, contexto: ContextoDeDesempate) -> int:
        return -fila.en_contra


@dataclass(frozen=True, slots=True)
class PorPartidosGanados:
    def valor(self, fila: FilaClasificacion, contexto: ContextoDeDesempate) -> int:
        return fila.ganados


@dataclass(frozen=True, slots=True)
class PorEnfrentamientoDirecto:
    """Puntos obtenidos solo en los partidos entre los empatados.

    Necesita saber cómo se puntúa, así que compone un `SistemaDePuntuacion`: el
    enfrentamiento directo de una liga 3/1/0 y el de una por sets no dan lo mismo.
    """

    puntuacion: SistemaDePuntuacion

    def valor(self, fila: FilaClasificacion, contexto: ContextoDeDesempate) -> int:
        total = 0
        for enfrentamiento in contexto.enfrentamientos:
            if not enfrentamiento.esta_finalizado or enfrentamiento.marcador is None:
                continue
            if not enfrentamiento.participa(fila.participante_id):
                continue
            if enfrentamiento.local not in contexto.empatados:
                continue
            if enfrentamiento.visitante not in contexto.empatados:
                continue
            local, visitante = self.puntuacion.puntos(enfrentamiento.marcador)
            total += (
                local
                if enfrentamiento.local == fila.participante_id
                else visitante
            )
        return total


def ordenar_clasificacion(
    filas: Iterable[FilaClasificacion],
    criterios: Sequence[CriterioDeDesempate],
    enfrentamientos: Sequence[Enfrentamiento] = (),
) -> tuple[FilaClasificacion, ...]:
    """Ordena la tabla aplicando los criterios en cascada.

    Los empates que ningún criterio logre romper conservan el orden de entrada,
    de modo que la función es determinista: la misma tabla produce siempre la
    misma clasificación.
    """
    partidos = tuple(enfrentamientos)
    bloques: list[tuple[FilaClasificacion, ...]] = [tuple(filas)]

    for criterio in criterios:
        refinados: list[tuple[FilaClasificacion, ...]] = []
        for bloque in bloques:
            if len(bloque) <= 1:
                refinados.append(bloque)
                continue
            contexto = ContextoDeDesempate(
                empatados=tuple(f.participante_id for f in bloque),
                enfrentamientos=partidos,
            )
            valores = {f.participante_id: criterio.valor(f, contexto) for f in bloque}
            ordenado = sorted(
                bloque, key=lambda f: valores[f.participante_id], reverse=True
            )
            for _, iguales in groupby(
                ordenado, key=lambda f: valores[f.participante_id]
            ):
                refinados.append(tuple(iguales))
        bloques = refinados

    return tuple(fila for bloque in bloques for fila in bloque)


#: Los criterios que el sistema aplicaba, ahora explícitos y sustituibles.
DESEMPATE_CLASICO: tuple[CriterioDeDesempate, ...] = (
    PorPuntos(),
    PorDiferencia(),
    PorAFavor(),
)
