"""El sistema en memoria con el que corre la suite de interfaz.

Esto vivía dentro de la aplicación, como «modo demostración»: sin credenciales
`app.py` levantaba sobre memoria, sembraba dos competiciones y ofrecía un
selector para mirarlo desde cada papel. Se retiró por dos motivos.

El primero es que convertía un secreto olvidado en un botón de administrador sin
contraseña: un despliegue mal configurado no fallaba, arrancaba fingiendo.

El segundo es este archivo. Con los datos sembrados por la aplicación, la suite
de interfaz nunca recorría el camino de crearlos —y así fue como «crear la
primera competición» llegó a producción rota sin que nadie lo viera. Los datos
de muestra son cosa de las pruebas, y aquí se ven como lo que son.

`ensamblar` es la composición de verdad, la misma que usa `construir`: lo que se
sustituye es de dónde salen los repositorios, no cómo se montan los servicios.
"""

from __future__ import annotations

import datetime as dt
import random
from dataclasses import dataclass
from typing import Iterable

from itc_deporte.aplicacion.permisos import Concesion, Identidad, Rol
from itc_deporte.aplicacion.servicios import (
    ServicioDeCompeticiones,
    ServicioDeInscripciones,
    ServicioDeResultados,
    ServicioDeSorteo,
)
from itc_deporte.domain.calendario import Calendario
from itc_deporte.domain.competicion import (
    Competicion,
    Deporte,
    EstadoCompeticion,
    FaseDeGrupos,
    FaseEliminatoria,
)
from itc_deporte.domain.enfrentamiento import Marcador
from itc_deporte.domain.reglas.catalogo import DEPORTES
from itc_deporte.domain.reglas.fixture import ConfigFixture
from itc_deporte.infraestructura.autenticacion import (
    AutenticadorEnMemoria,
    ConcesionesEnMemoria,
)
from itc_deporte.infraestructura.memoria import (
    CompeticionesEnMemoria,
    EnfrentamientosEnMemoria,
    ParticipantesEnMemoria,
)
from itc_deporte.ui.composicion import ensamblar

ADMIN = Identidad("admin-1", "admin@itc.edu.co")
PROFE = Identidad("profe-1", "profe@itc.edu.co")
MIRON = Identidad("miron-1", "miron@itc.edu.co")

MICRO = "micro"
VOLEY = "voley"


@dataclass
class Sistema:
    """Los servicios y los repositorios sobre los que van montados.

    Los repositorios se exponen para que una prueba pueda comprobar qué quedó
    guardado sin volver a preguntárselo a la interfaz.
    """

    servicios: object
    competiciones: CompeticionesEnMemoria
    participantes: ParticipantesEnMemoria
    enfrentamientos: EnfrentamientosEnMemoria
    concesiones: ConcesionesEnMemoria


#: Quién es quién por defecto. El profe es registrador **solo** de Microfútbol,
#: para que se note que la concesión tiene alcance.
def concesiones_por_defecto() -> ConcesionesEnMemoria:
    return ConcesionesEnMemoria(
        [
            Concesion(ADMIN.usuario_id, Rol.ADMIN),
            Concesion(PROFE.usuario_id, Rol.REGISTRADOR, MICRO),
        ]
    )


def vacio(
    concesiones: ConcesionesEnMemoria | None = None,
    identidades: Iterable[Identidad] = (ADMIN, PROFE, MIRON),
) -> Sistema:
    """Un sistema sin una sola competición, como un despliegue recién montado."""
    competiciones = CompeticionesEnMemoria()
    participantes = ParticipantesEnMemoria()
    enfrentamientos = EnfrentamientosEnMemoria()
    otorgadas = concesiones if concesiones is not None else concesiones_por_defecto()
    servicios = ensamblar(
        (competiciones, participantes, enfrentamientos, otorgadas),
        AutenticadorEnMemoria(identidades),
    )
    return Sistema(servicios, competiciones, participantes, enfrentamientos, otorgadas)


def con_liga_en_marcha() -> Sistema:
    """Dos competiciones, uná ya sorteada y a medio jugar.

    Se siembra **por los servicios**, no escribiendo en los repositorios: si
    crear, inscribir, sortear o registrar se rompieran, esto dejaría de montarse
    y la suite lo diría antes de llegar a ninguna aserción.
    """
    sistema = vacio()
    servicios = sistema.servicios

    for competicion in (_microfutbol(), _voleibol()):
        servicios.competiciones.crear(ADMIN, competicion)

    equipos = [
        ("601", "Los Tigres"), ("602", "Las Panteras"), ("603", "Halcones"),
        ("701", "Titanes"), ("702", "Cóndores"), ("801", "Leones"),
    ]
    for indice, (curso, nombre) in enumerate(equipos, start=1):
        servicios.inscripciones.inscribir(
            ADMIN, MICRO, f"{MICRO}-e{indice}", nombre, curso
        )

    # El azar se inyecta, así que la muestra es la misma en cada ejecución.
    sorteo = ServicioDeSorteo(
        sistema.competiciones,
        sistema.participantes,
        sistema.enfrentamientos,
        servicios.politica,
        azar=random.Random(7),
    )
    partidos = sorteo.sortear(ADMIN, MICRO, f"{MICRO}:0", desde=dt.date(2026, 3, 2))

    azar = random.Random(11)
    for partido in partidos[: len(partidos) // 2]:
        servicios.resultados.registrar(
            ADMIN, partido.id, Marcador(azar.randint(0, 5), azar.randint(0, 5))
        )
    return sistema


def _microfutbol() -> Competicion:
    return _competicion(MICRO, "Intercursos — Microfútbol", "microfutbol")


def _voleibol() -> Competicion:
    return _competicion(VOLEY, "Intercursos — Voleibol", "voleyball")


def _competicion(id_: str, nombre: str, deporte: str) -> Competicion:
    """Las reglas salen del catálogo, igual que al crearla desde la pantalla."""
    catalogo = DEPORTES[deporte]
    return Competicion(
        id=id_,
        nombre=nombre,
        deporte=catalogo.deporte(),
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
        reglas=catalogo.reglas(),
        calendario=Calendario(dia_de_la_semana=5, hora=dt.time(15, 0)),
    )
