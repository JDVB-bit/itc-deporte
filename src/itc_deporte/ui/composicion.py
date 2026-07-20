"""Dónde se enchufan las piezas.

Es el único sitio del sistema que conoce a la vez los servicios y las
implementaciones concretas. Todo lo demás habla con protocolos, y por eso esta
función puede devolver los mismos servicios apoyados en Supabase o en memoria
sin que nada más se entere.

Esa sustitución no es un adorno: `streamlit run app.py` sin credenciales levanta
la aplicación entera sobre repositorios en memoria con datos de muestra, lo que
permite ver la interfaz funcionando sin tocar la red.
"""

from __future__ import annotations

import datetime as dt
import random
from dataclasses import dataclass
from typing import Any

from ..aplicacion.permisos import ANONIMO, Concesion, Identidad, Politica, Rol
from ..aplicacion.servicios import (
    ServicioDeClasificacion,
    ServicioDeCompeticiones,
    ServicioDeCuadroFinal,
    ServicioDeInscripciones,
    ServicioDeRegistradores,
    ServicioDeResultados,
    ServicioDeSorteo,
)
from ..domain.calendario import Calendario
from ..domain.competicion import (
    Competicion,
    Deporte,
    EstadoCompeticion,
    FaseDeGrupos,
    FaseEliminatoria,
    ReglasDeCompeticion,
)
from ..domain.reglas.fixture import ConfigFixture
from ..domain.reglas.puntuacion import PorSets


@dataclass(frozen=True, slots=True)
class Servicios:
    """Todo lo que la interfaz puede pedirle al sistema."""

    competiciones: ServicioDeCompeticiones
    inscripciones: ServicioDeInscripciones
    sorteo: ServicioDeSorteo
    resultados: ServicioDeResultados
    clasificacion: ServicioDeClasificacion
    cuadro: ServicioDeCuadroFinal
    registradores: ServicioDeRegistradores
    autenticador: Any
    politica: Politica
    #: `True` cuando corre sobre repositorios en memoria, para que la interfaz
    #: pueda avisar de que nada se guarda.
    es_demostracion: bool


def construir(secretos: Any = None) -> Servicios:
    """Arma los servicios. Sin credenciales usa memoria y datos de muestra."""
    url = _leer(secretos, "SUPABASE_URL")
    clave = _leer(secretos, "SUPABASE_KEY")

    if url and clave:
        repositorios, autenticador, demostracion = _sobre_supabase(url, clave)
    else:
        repositorios, autenticador, demostracion = _en_memoria()

    competiciones, participantes, enfrentamientos, concesiones = repositorios
    politica = Politica(concesiones)
    clasificacion = ServicioDeClasificacion(
        competiciones, participantes, enfrentamientos
    )
    return Servicios(
        competiciones=ServicioDeCompeticiones(competiciones, politica),
        inscripciones=ServicioDeInscripciones(competiciones, participantes, politica),
        sorteo=ServicioDeSorteo(
            competiciones, participantes, enfrentamientos, politica
        ),
        resultados=ServicioDeResultados(enfrentamientos, politica),
        clasificacion=clasificacion,
        cuadro=ServicioDeCuadroFinal(
            competiciones, enfrentamientos, clasificacion, politica
        ),
        registradores=ServicioDeRegistradores(
            competiciones, concesiones, autenticador, politica
        ),
        autenticador=autenticador,
        politica=politica,
        es_demostracion=demostracion,
    )


def _leer(secretos: Any, clave: str) -> str | None:
    import os

    if secretos is not None:
        try:
            if clave in secretos:
                return secretos[clave]
        except Exception:
            pass
    return os.getenv(clave)


def _sobre_supabase(url: str, clave: str):
    import supabase

    from ..infraestructura.supabase.auth import AutenticadorSupabase
    from ..infraestructura.supabase.repositorios import (
        CompeticionesSupabase,
        ConcesionesSupabase,
        EnfrentamientosSupabase,
        ParticipantesSupabase,
    )

    cliente = supabase.create_client(url, clave)
    repositorios = (
        CompeticionesSupabase(cliente),
        ParticipantesSupabase(cliente),
        EnfrentamientosSupabase(cliente),
        ConcesionesSupabase(cliente),
    )
    return repositorios, AutenticadorSupabase(cliente), False


def _en_memoria():
    """Un sistema completo en memoria, con una competición ya jugándose."""
    from ..infraestructura.autenticacion import (
        AutenticadorEnMemoria,
        ConcesionesEnMemoria,
    )
    from ..infraestructura.memoria import (
        CompeticionesEnMemoria,
        EnfrentamientosEnMemoria,
        ParticipantesEnMemoria,
    )

    profesora = Identidad("demo-admin", "demo@itc.edu.co")
    repositorios = (
        CompeticionesEnMemoria(),
        ParticipantesEnMemoria(),
        EnfrentamientosEnMemoria(),
        ConcesionesEnMemoria([Concesion("demo-admin", Rol.ADMIN)]),
    )
    autenticador = AutenticadorEnMemoria([profesora])
    _sembrar(repositorios, profesora)
    return repositorios, autenticador, True


def _sembrar(repositorios, admin: Identidad) -> None:
    """Deja una competición sorteada y a medio jugar, para que se vea algo."""
    competiciones, participantes, enfrentamientos, concesiones = repositorios
    politica = Politica(concesiones)

    servicio = ServicioDeCompeticiones(competiciones, politica)
    inscripciones = ServicioDeInscripciones(competiciones, participantes, politica)
    sorteo = ServicioDeSorteo(
        competiciones, participantes, enfrentamientos, politica, azar=random.Random(7)
    )
    resultados = ServicioDeResultados(enfrentamientos, politica)

    for datos in _COMPETICIONES_DE_MUESTRA:
        servicio.crear(admin, _competicion_de_muestra(**datos))

    equipos = [
        ("601", "Los Tigres"), ("602", "Las Panteras"), ("603", "Halcones"),
        ("701", "Titanes"), ("702", "Cóndores"), ("801", "Leones"),
    ]
    for indice, (curso, nombre) in enumerate(equipos, start=1):
        inscripciones.inscribir(admin, "demo-micro", f"e{indice}", nombre, curso)

    partidos = sorteo.sortear(admin, "demo-micro", "demo-micro:0", desde=dt.date.today())
    from ..domain.enfrentamiento import Marcador

    azar = random.Random(11)
    for partido in partidos[: len(partidos) // 2]:
        resultados.registrar(
            admin, partido.id, Marcador(azar.randint(0, 5), azar.randint(0, 5))
        )


_COMPETICIONES_DE_MUESTRA = [
    dict(
        id_="demo-micro",
        nombre="Intercursos — Microfútbol",
        deporte=Deporte("microfutbol", "Microfútbol", "⚽"),
    ),
    dict(
        id_="demo-voley",
        nombre="Intercursos — Voleyball",
        deporte=Deporte("voleyball", "Voleyball", "🏐"),
        puntuacion=PorSets(),
    ),
]


def _competicion_de_muestra(id_, nombre, deporte, puntuacion=None) -> Competicion:
    reglas = ReglasDeCompeticion(puntuacion=puntuacion) if puntuacion else ReglasDeCompeticion()
    return Competicion(
        id=id_,
        nombre=nombre,
        deporte=deporte,
        temporada="2026",
        estado=EstadoCompeticion.EN_CURSO,
        fases=(
            FaseDeGrupos(
                f"{id_}:0",
                "Fase de grupos",
                0,
                config_fixture=ConfigFixture(jornadas_forzadas=7),
            ),
            FaseEliminatoria(
                f"{id_}:1",
                "Eliminación directa",
                1,
                fixture="eliminacion_directa",
                cupos=16,
            ),
        ),
        reglas=reglas,
        calendario=Calendario(dia_de_la_semana=5, hora=dt.time(15, 0)),
    )
