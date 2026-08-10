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


class SistemaSinPreparar(RuntimeError):
    """No se puede arrancar contra Supabase con lo que hay configurado."""


class BaseSinPreparar(SistemaSinPreparar):
    """Hay credenciales pero la base no tiene el esquema del sistema nuevo."""


class ClavesIncompletas(SistemaSinPreparar):
    """Falta una de las dos claves. Ver `_sobre_supabase` para por qué son dos."""


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


#: Quién existe en la demostración, para poder probar el sistema desde cada
#: papel sin dar de alta a nadie. En producción no hay atajo: el primer
#: administrador se crea desde el panel de Supabase (ver `docs/FASE_7.md`).
#: Cada papel se identifica por su **correo**, no por su id, para que probarlo
#: pase por `iniciar_sesion` igual que en producción. Guardar el id a mano era
#: un atajo que solo funcionaba con el doble en memoria, y así fue como el
#: fallo del token llegó a producción sin que nadie lo viera.
PAPELES_DE_DEMOSTRACION = (
    (
        "demo-admin",
        "admin@itc.edu.co",
        "🛠️ Administrador",
        "Crea competiciones, sortea y reparte permisos.",
    ),
    (
        "demo-registrador",
        "profe@itc.edu.co",
        "✍️ Registrador",
        "Inscribe y carga resultados, solo en Microfútbol.",
    ),
    (None, None, "👤 Visitante", "Consulta tablas, calendarios y cuadros."),
)


def construir(secretos: Any = None, token: str | None = None) -> Servicios:
    """Arma los servicios.

    Sin credenciales usa memoria y datos de muestra. **Con** credenciales usa
    Supabase o falla: caer a la demostración cuando la base no responde sería
    mostrar competiciones inventadas como si fueran reales, que es peor que no
    arrancar.

    `token` es el JWT de quien está mirando. Viaja hasta el cliente de datos
    para que `auth.uid()` exista dentro de Postgres; sin él las políticas de
    `permisos.sql` no pueden decidir nada. Ver `_sobre_supabase`.
    """
    url = _leer(secretos, "SUPABASE_URL")
    servicio = _leer(secretos, "SUPABASE_KEY")
    publica = _leer(secretos, "SUPABASE_ANON_KEY")

    if url and (servicio or publica):
        _exigir_las_dos_claves(servicio, publica)
        repositorios, autenticador, demostracion = _sobre_supabase(
            url, servicio, publica, token
        )
        _exigir_esquema(repositorios[0])
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
        resultados=ServicioDeResultados(enfrentamientos, competiciones, politica),
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


def _exigir_esquema(competiciones) -> None:
    """Comprueba que la base tenga el esquema nuevo, y lo dice si no.

    Sin esto, el fallo aparecería más tarde y en forma de error de red, sin
    pista de que lo que falta es aplicar `esquema.sql`.
    """
    try:
        competiciones.listar()
    except Exception as error:
        raise BaseSinPreparar(
            "Hay credenciales de Supabase, pero la base no responde a las "
            "tablas del sistema nuevo.\n\n"
            "Si es la primera vez, falta aplicar `docs/PASO_2.sql` en el editor "
            "SQL de Supabase (ver `docs/FASE_7.md`).\n\n"
            f"Detalle: {error}"
        ) from error


def _leer(secretos: Any, clave: str) -> str | None:
    import os

    if secretos is not None:
        try:
            if clave in secretos:
                return secretos[clave]
        except Exception:
            pass
    return os.getenv(clave)


def _exigir_las_dos_claves(servicio: str | None, publica: str | None) -> None:
    """El sistema necesita las dos, y por motivos distintos. Ver `_sobre_supabase`."""
    if servicio and publica:
        return
    falta, para_que = (
        ("SUPABASE_ANON_KEY", "leer y escribir datos con los permisos de quien mira")
        if publica is None
        else ("SUPABASE_KEY", "invitar registradores por correo")
    )
    raise ClavesIncompletas(
        f"Falta el secreto `{falta}`, que hace falta para {para_que}.\n\n"
        "El sistema usa dos claves de Supabase a propósito: la `anon` para los "
        "datos, de modo que las políticas RLS decidan, y la `service_role` solo "
        "para la API de administración de Auth.\n\n"
        "Las dos están en Project Settings → API. Ver `docs/FASE_7.md`."
    )


def _sobre_supabase(
    url: str, clave_servicio: str, clave_publica: str, token: str | None
):
    """Dos clientes, y la separación importa.

    Antes había uno solo y nunca llevaba la sesión de nadie, así que dentro de
    Postgres `auth.uid()` era NULL: `es_admin()` y `puede_registrar()` daban
    false siempre y **ninguna** política de `permisos.sql` podía autorizar una
    escritura. Solo funcionaba con la clave `service_role`, que salta RLS por
    completo —y entonces la «segunda línea de defensa» que ese archivo
    documenta no existía.

    - **Datos**: clave `anon` más el JWT de quien mira. Es lo que hace que RLS
      decida de verdad, con los permisos de esa persona y no con los de nadie.
    - **Administración**: `service_role`, y solo para Auth. `invitar` y
      `por_email` usan la API de administración, que la exige. No toca datos,
      así que no puede saltarse RLS por descuido.
    """
    import supabase

    from ..infraestructura.supabase.auth import AutenticadorSupabase
    from ..infraestructura.supabase.repositorios import (
        CompeticionesSupabase,
        ConcesionesSupabase,
        EnfrentamientosSupabase,
        ParticipantesSupabase,
    )

    datos = supabase.create_client(url, clave_publica)
    if token:
        datos.postgrest.auth(token)
    administracion = supabase.create_client(url, clave_servicio)

    repositorios = (
        CompeticionesSupabase(datos),
        ParticipantesSupabase(datos),
        EnfrentamientosSupabase(datos),
        ConcesionesSupabase(datos),
    )
    return repositorios, AutenticadorSupabase(administracion), False


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

    admin = Identidad("demo-admin", "admin@itc.edu.co")
    registrador = Identidad("demo-registrador", "profe@itc.edu.co")
    repositorios = (
        CompeticionesEnMemoria(),
        ParticipantesEnMemoria(),
        EnfrentamientosEnMemoria(),
        ConcesionesEnMemoria(
            [
                Concesion("demo-admin", Rol.ADMIN),
                # Solo sobre una de las dos competiciones, para que se note que
                # la concesión tiene alcance.
                Concesion("demo-registrador", Rol.REGISTRADOR, "demo-micro"),
            ]
        ),
    )
    autenticador = AutenticadorEnMemoria([admin, registrador])
    _sembrar(repositorios, admin)
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
    resultados = ServicioDeResultados(enfrentamientos, competiciones, politica)

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
