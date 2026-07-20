"""De enfrentamientos a tabla de posiciones.

Una función pura, frente al `calcular_tabla` anterior que empezaba lanzando dos
consultas a la base y terminaba devolviendo diccionarios sueltos con las claves
en castellano abreviado.

Los participantes se pasan explícitamente: son ellos quienes definen quién sale
en la tabla. Un enfrentamiento que involucre a alguien de fuera se ignora, que
es lo que permite calcular la tabla de un grupo sin arrastrar los partidos de
los demás.
"""

from __future__ import annotations

from typing import Iterable, Sequence

from ..clasificacion import FilaClasificacion
from ..competicion import ReglasDeCompeticion
from ..enfrentamiento import Enfrentamiento
from ..participante import ParticipanteId
from ..reglas.desempate import ordenar_clasificacion


def calcular_clasificacion(
    participantes: Iterable[ParticipanteId],
    enfrentamientos: Sequence[Enfrentamiento] = (),
    reglas: ReglasDeCompeticion = ReglasDeCompeticion(),
) -> tuple[FilaClasificacion, ...]:
    """Tabla ordenada según las reglas de la competición.

    Los participantes sin partidos jugados aparecen en cero, no desaparecen.
    """
    inscritos = list(dict.fromkeys(participantes))  # sin duplicados, en orden
    acumulado: dict[ParticipanteId, dict[str, int]] = {
        p: dict(
            jugados=0, ganados=0, empatados=0, perdidos=0, a_favor=0, en_contra=0, puntos=0
        )
        for p in inscritos
    }

    computados: list[Enfrentamiento] = []
    for enfrentamiento in enfrentamientos:
        if not enfrentamiento.esta_finalizado or enfrentamiento.marcador is None:
            continue
        if enfrentamiento.local not in acumulado:
            continue
        if enfrentamiento.visitante not in acumulado:
            continue
        computados.append(enfrentamiento)

        marcador = enfrentamiento.marcador
        local = acumulado[enfrentamiento.local]
        visitante = acumulado[enfrentamiento.visitante]
        puntos_local, puntos_visitante = reglas.puntuacion.puntos(marcador)

        for fila in (local, visitante):
            fila["jugados"] += 1
        local["a_favor"] += marcador.local
        local["en_contra"] += marcador.visitante
        visitante["a_favor"] += marcador.visitante
        visitante["en_contra"] += marcador.local
        local["puntos"] += puntos_local
        visitante["puntos"] += puntos_visitante

        if marcador.gana_local:
            local["ganados"] += 1
            visitante["perdidos"] += 1
        elif marcador.gana_visitante:
            visitante["ganados"] += 1
            local["perdidos"] += 1
        else:
            local["empatados"] += 1
            visitante["empatados"] += 1

    filas = [
        FilaClasificacion(participante_id=p, **acumulado[p]) for p in inscritos
    ]
    return ordenar_clasificacion(filas, reglas.desempate, computados)
