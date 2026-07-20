"""Lectura de plantillas desde JSON.

Un fichero de catálogo lleva una lista de plantillas y, opcionalmente, un bloque
`divisiones` compartido que se aplica a las que no traigan el suyo: las cuatro
plantillas del ITC comparten los mismos cursos y no tiene sentido repetirlos.

Este es el mecanismo por el que ITC deja de ser código privilegiado. Su semilla
—`itc.json`, versionada junto al código— se carga por la misma vía que
cualquier plantilla que escriba un usuario.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from ...domain.calendario import Calendario
from ...domain.competicion import Deporte
from ...domain.division import Division
from ...domain.errores import ErrorDeDominio
from ...domain.plantilla import (
    EspecificacionDeFase,
    EspecificacionDeRegla,
    PlantillaDeCompeticion,
    TipoDeFase,
)
from ...domain.reglas.fixture import ConfigFixture

SEMILLAS = Path(__file__).parent


class CatalogoIlegible(ErrorDeDominio):
    """El fichero de plantillas no tiene la forma esperada."""


def _exigir(datos: Mapping[str, Any], clave: str, donde: str) -> Any:
    if clave not in datos:
        raise CatalogoIlegible(f"Falta {clave!r} en {donde}.")
    return datos[clave]


def _division(datos: Mapping[str, Any]) -> Division:
    return Division(
        id=_exigir(datos, "id", "una división"),
        nombre=_exigir(datos, "nombre", "una división"),
        padre_id=datos.get("padre_id"),
    )


def _deporte(datos: Mapping[str, Any]) -> Deporte:
    return Deporte(
        id=_exigir(datos, "id", "un deporte"),
        nombre=_exigir(datos, "nombre", "un deporte"),
        icono=datos.get("icono", ""),
    )


def _regla(datos: Mapping[str, Any]) -> EspecificacionDeRegla:
    return EspecificacionDeRegla(
        tipo=_exigir(datos, "tipo", "una regla"),
        parametros=datos.get("parametros", {}),
    )


def _tipo_de_fase(valor: str) -> TipoDeFase:
    try:
        return TipoDeFase(valor)
    except ValueError:
        opciones = ", ".join(t.value for t in TipoDeFase)
        raise CatalogoIlegible(
            f"Tipo de fase desconocido: {valor!r}. Opciones: {opciones}."
        ) from None


def _fase(datos: Mapping[str, Any]) -> EspecificacionDeFase:
    config = datos.get("config_fixture", {})
    return EspecificacionDeFase(
        tipo=_tipo_de_fase(_exigir(datos, "tipo", "una fase")),
        nombre=_exigir(datos, "nombre", "una fase"),
        orden=_exigir(datos, "orden", "una fase"),
        fixture=datos.get("fixture", "round_robin"),
        config_fixture=ConfigFixture(
            vueltas=config.get("vueltas", 1),
            jornadas_forzadas=config.get("jornadas_forzadas"),
        ),
        cupos=datos.get("cupos", 2),
    )


def _hora(texto: str) -> dt.time:
    try:
        return dt.time.fromisoformat(texto)
    except ValueError:
        raise CatalogoIlegible(f"Hora inválida: {texto!r}. Se espera HH:MM.") from None


def _calendario(datos: Mapping[str, Any]) -> Calendario:
    return Calendario(
        dia_de_la_semana=datos.get("dia_de_la_semana"),
        hora=_hora(datos.get("hora", "15:00")),
        cadencia_dias=datos.get("cadencia_dias", 7),
    )


def _plantilla(
    datos: Mapping[str, Any], divisiones_comunes: Sequence[Division]
) -> PlantillaDeCompeticion:
    propias = datos.get("divisiones")
    divisiones = (
        tuple(_division(d) for d in propias)
        if propias is not None
        else tuple(divisiones_comunes)
    )
    return PlantillaDeCompeticion(
        id=_exigir(datos, "id", "una plantilla"),
        nombre=_exigir(datos, "nombre", "una plantilla"),
        deporte=_deporte(_exigir(datos, "deporte", "una plantilla")),
        descripcion=datos.get("descripcion", ""),
        divisiones=divisiones,
        puntuacion=_regla(datos.get("puntuacion", {"tipo": "victoria_derrota"})),
        desempate=tuple(datos.get("desempate", ("puntos", "diferencia", "a_favor"))),
        fases=tuple(_fase(f) for f in datos.get("fases", ())),
        calendario=_calendario(datos.get("calendario", {})),
        es_semilla=datos.get("es_semilla", False),
    )


def cargar_catalogo(ruta: Path) -> tuple[PlantillaDeCompeticion, ...]:
    """Lee un fichero de catálogo y devuelve sus plantillas ya validadas."""
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise CatalogoIlegible(f"{ruta.name} no es JSON válido: {error}") from error

    comunes = tuple(_division(d) for d in datos.get("divisiones", ()))
    plantillas = _exigir(datos, "plantillas", ruta.name)
    return tuple(_plantilla(p, comunes) for p in plantillas)


def cargar_semillas() -> tuple[PlantillaDeCompeticion, ...]:
    """Todas las plantillas precargadas del repositorio, ITC incluida."""
    return tuple(
        plantilla
        for fichero in sorted(SEMILLAS.glob("*.json"))
        for plantilla in cargar_catalogo(fichero)
    )
