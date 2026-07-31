"""Traducción entre entidades del dominio y filas de Supabase.

Están separados de los repositorios a propósito. Los repositorios hacen llamadas
de red que no se pueden probar desde aquí; esto es una función pura de
diccionario a entidad y viceversa, y sí se prueba —con round-trip, de modo que
un campo que se guarde y no se lea salta solo.

Los datos cruzan hacia adentro como entidades del dominio, nunca como `dict`
crudos de la API. Es la regla de §4 del plan, y este módulo es donde se cumple.
"""

from __future__ import annotations

import datetime as dt
import json
from typing import Any, Mapping

from ...domain.calendario import Calendario
from ...domain.competicion import (
    Competicion,
    Deporte,
    EstadoCompeticion,
    Fase,
    FaseDeGrupos,
    FaseEliminatoria,
    ReglasDeCompeticion,
)
from ...domain.division import Division
from ...domain.enfrentamiento import (
    Enfrentamiento,
    EstadoEnfrentamiento,
    Marcador,
    Parcial,
)
from ...domain.participante import Miembro, Participante
from ...domain.reglas.catalogo import (
    crear_desempate,
    crear_puntuacion,
    nombre_de_desempate,
    nombre_de_puntuacion,
    parametros_de,
)
from ...domain.reglas.fixture import ConfigFixture

# ── Reglas ──────────────────────────────────────────────────────────────────


def reglas_a_json(reglas: ReglasDeCompeticion) -> dict[str, Any]:
    return {
        "puntuacion": {
            "tipo": nombre_de_puntuacion(reglas.puntuacion),
            "parametros": parametros_de(reglas.puntuacion),
        },
        "desempate": [nombre_de_desempate(c) for c in reglas.desempate],
    }


def reglas_desde_json(datos: Mapping[str, Any] | None) -> ReglasDeCompeticion:
    if not datos:
        return ReglasDeCompeticion()
    spec = datos.get("puntuacion") or {"tipo": "victoria_derrota"}
    puntuacion = crear_puntuacion(spec["tipo"], spec.get("parametros", {}))
    nombres = datos.get("desempate") or ["puntos", "diferencia", "a_favor"]
    return ReglasDeCompeticion(
        puntuacion=puntuacion,
        desempate=tuple(crear_desempate(n, puntuacion) for n in nombres),
    )


# ── Calendario ──────────────────────────────────────────────────────────────


def calendario_a_json(calendario: Calendario) -> dict[str, Any]:
    return {
        "dia_de_la_semana": calendario.dia_de_la_semana,
        "hora": calendario.hora.isoformat(timespec="minutes"),
        "cadencia_dias": calendario.cadencia_dias,
    }


def calendario_desde_json(datos: Mapping[str, Any] | None) -> Calendario:
    if not datos:
        return Calendario()
    return Calendario(
        dia_de_la_semana=datos.get("dia_de_la_semana"),
        hora=dt.time.fromisoformat(datos.get("hora", "15:00")),
        cadencia_dias=datos.get("cadencia_dias", 7),
    )


# ── Fases ───────────────────────────────────────────────────────────────────


def fase_a_fila(fase: Fase, competicion_id: str) -> dict[str, Any]:
    return {
        "id": fase.id,
        "competicion_id": competicion_id,
        "tipo": "eliminatoria" if isinstance(fase, FaseEliminatoria) else "grupos",
        "nombre": fase.nombre,
        "orden": fase.orden,
        "cupos": getattr(fase, "cupos", None),
        "fixture": fase.fixture,
        "config_fixture": {
            "vueltas": fase.config_fixture.vueltas,
            "jornadas_forzadas": fase.config_fixture.jornadas_forzadas,
        },
    }


def fase_desde_fila(fila: Mapping[str, Any]) -> Fase:
    config = fila.get("config_fixture") or {}
    if isinstance(config, str):
        config = json.loads(config)
    comunes = dict(
        nombre=fila["nombre"],
        orden=fila["orden"],
        fixture=fila.get("fixture") or "round_robin",
        config_fixture=ConfigFixture(
            vueltas=config.get("vueltas", 1),
            jornadas_forzadas=config.get("jornadas_forzadas"),
        ),
    )
    if fila["tipo"] == "eliminatoria":
        return FaseEliminatoria(fila["id"], **comunes, cupos=fila.get("cupos") or 2)
    return FaseDeGrupos(fila["id"], **comunes)


# ── Competición ─────────────────────────────────────────────────────────────


def competicion_a_fila(competicion: Competicion) -> dict[str, Any]:
    return {
        "id": competicion.id,
        "nombre": competicion.nombre,
        "deporte_id": competicion.deporte.id,
        "temporada": competicion.temporada,
        "estado": competicion.estado.value,
        "reglas": {
            **reglas_a_json(competicion.reglas),
            "calendario": calendario_a_json(competicion.calendario),
        },
    }


def competicion_desde_fila(
    fila: Mapping[str, Any],
    deporte: Deporte,
    fases: tuple[Fase, ...] = (),
) -> Competicion:
    reglas_json = fila.get("reglas") or {}
    if isinstance(reglas_json, str):
        reglas_json = json.loads(reglas_json)
    return Competicion(
        id=fila["id"],
        nombre=fila["nombre"],
        deporte=deporte,
        temporada=fila.get("temporada"),
        estado=EstadoCompeticion(fila.get("estado") or "Borrador"),
        fases=fases,
        reglas=reglas_desde_json(reglas_json),
        calendario=calendario_desde_json(reglas_json.get("calendario")),
    )


def deporte_a_fila(deporte: Deporte) -> dict[str, Any]:
    return {"id": deporte.id, "nombre": deporte.nombre, "icono": deporte.icono}


def deporte_desde_fila(fila: Mapping[str, Any]) -> Deporte:
    return Deporte(fila["id"], fila["nombre"], fila.get("icono") or "")


# ── Divisiones ──────────────────────────────────────────────────────────────


def division_a_fila(division: Division, competicion_id: str) -> dict[str, Any]:
    return {
        "id": division.id,
        "competicion_id": competicion_id,
        "nombre": division.nombre,
        "padre_id": division.padre_id,
    }


def division_desde_fila(fila: Mapping[str, Any]) -> Division:
    return Division(
        id=fila["id"], nombre=fila["nombre"], padre_id=fila.get("padre_id")
    )


# ── Participantes ───────────────────────────────────────────────────────────


def participante_a_fila(participante: Participante) -> dict[str, Any]:
    return {
        "id": participante.id,
        "competicion_id": participante.competicion_id,
        "division_id": participante.division_id,
        "nombre": participante.nombre,
    }


def miembros_a_filas(participante: Participante) -> list[dict[str, Any]]:
    return [
        {
            "id": m.id,
            "participante_id": participante.id,
            "nombre": m.nombre,
            "dorsal": m.dorsal,
        }
        for m in participante.miembros
    ]


def participante_desde_fila(
    fila: Mapping[str, Any], miembros: tuple[Mapping[str, Any], ...] = ()
) -> Participante:
    return Participante(
        id=fila["id"],
        nombre=fila["nombre"],
        competicion_id=fila.get("competicion_id"),
        division_id=fila.get("division_id"),
        miembros=tuple(
            Miembro(m["id"], m["nombre"], m.get("dorsal")) for m in miembros
        ),
    )


# ── Enfrentamientos ─────────────────────────────────────────────────────────


def enfrentamiento_a_fila(enfrentamiento: Enfrentamiento) -> dict[str, Any]:
    return {
        "id": enfrentamiento.id,
        "competicion_id": enfrentamiento.competicion_id,
        "fase_id": enfrentamiento.fase_id,
        "jornada": enfrentamiento.jornada,
        "ronda": enfrentamiento.ronda,
        "slot": enfrentamiento.slot,
        "local_id": enfrentamiento.local,
        "visitante_id": enfrentamiento.visitante,
        "fecha": enfrentamiento.fecha.isoformat() if enfrentamiento.fecha else None,
        "estado": enfrentamiento.estado.value,
    }


def marcador_a_fila(enfrentamiento: Enfrentamiento) -> dict[str, Any] | None:
    marcador = enfrentamiento.marcador
    if marcador is None:
        return None
    return {
        "enfrentamiento_id": enfrentamiento.id,
        "total_local": marcador.local,
        "total_visitante": marcador.visitante,
        "parciales": [
            {"local": p.local, "visitante": p.visitante} for p in marcador.parciales
        ],
    }


def enfrentamiento_desde_fila(
    fila: Mapping[str, Any], marcador: Mapping[str, Any] | None = None
) -> Enfrentamiento:
    return Enfrentamiento(
        id=fila["id"],
        local=fila.get("local_id"),
        visitante=fila.get("visitante_id"),
        competicion_id=fila.get("competicion_id"),
        fase_id=fila.get("fase_id"),
        marcador=_marcador_desde_fila(marcador),
        estado=EstadoEnfrentamiento(fila.get("estado") or "Pendiente"),
        fecha=_fecha(fila.get("fecha")),
        jornada=fila.get("jornada"),
        ronda=fila.get("ronda"),
        slot=fila.get("slot"),
    )


def _marcador_desde_fila(fila: Mapping[str, Any] | None) -> Marcador | None:
    if fila is None:
        return None
    parciales = fila.get("parciales") or []
    if isinstance(parciales, str):
        parciales = json.loads(parciales)
    return Marcador(
        fila["total_local"],
        fila["total_visitante"],
        tuple(Parcial(p["local"], p["visitante"]) for p in parciales),
    )


def _fecha(valor) -> dt.datetime | None:
    if not valor:
        return None
    if isinstance(valor, dt.datetime):
        return valor
    return dt.datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
