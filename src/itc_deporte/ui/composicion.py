"""Dónde se enchufan las piezas.

Es el único sitio del sistema que conoce a la vez los servicios y las
implementaciones concretas. Todo lo demás habla con protocolos, y por eso
`ensamblar` puede devolver los mismos servicios apoyados en Supabase o en
memoria sin que nada más se entere.

Las dos mitades van separadas a propósito. `ensamblar` monta los servicios
sobre los repositorios que se le den; `construir` decide cuáles son. La suite de
interfaz sustituye la segunda y ejercita la primera tal cual, que es lo que
permite probar la aplicación entera sin red.

**No hay modo demostración.** Lo hubo: sin credenciales la aplicación levantaba
sobre memoria con dos competiciones sembradas y un selector para mirarla desde
cada papel. Servía para enseñarla, pero convertía una variable de entorno
ausente en un botón de administrador sin contraseña, y hacía que la suite de
interfaz corriera sobre datos que nadie había creado por los caminos de la
aplicación —así fue como «crear la primera competición» pudo estar roto sin que
nadie lo viera. Los datos de muestra viven ahora en `tests/ui/sistema.py`, que
es su sitio.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from ..aplicacion.permisos import Politica
from ..aplicacion.servicios import (
    ServicioDeClasificacion,
    ServicioDeCompeticiones,
    ServicioDeCuadroFinal,
    ServicioDeInscripciones,
    ServicioDeRegistradores,
    ServicioDeResultados,
    ServicioDeSorteo,
)


class SistemaSinPreparar(RuntimeError):
    """No se puede arrancar contra Supabase con lo que hay configurado."""


class BaseSinPreparar(SistemaSinPreparar):
    """Hay credenciales pero la base no tiene el esquema del sistema nuevo."""


class ClavesIncompletas(SistemaSinPreparar):
    """Falta una de las dos claves. Ver `_sobre_supabase` para por qué son dos."""


class FaltanCredenciales(SistemaSinPreparar):
    """No hay a qué conectarse.

    Antes esto caía en la demostración. Parecía amable y era lo contrario: un
    despliegue al que se le olvidara un secreto no fallaba, arrancaba con
    competiciones inventadas y un botón para entrar como administrador sin
    contraseña.
    """


#: Lo que puede fallar por red y no por culpa de nadie.
#:
#: La interfaz lo atrapa para decir «se cayó la conexión» en vez de mostrar una
#: traza de httpx. El transporte ya reintenta (ver `supabase/transporte.py`), así
#: que llegar hasta aquí significa que la red está de verdad caída.
ERRORES_DE_RED = (httpx.TransportError,)


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


def construir(secretos: Any = None, token: str | None = None) -> Servicios:
    """Decide sobre qué van montados los servicios, y los monta.

    Contra Supabase o no arranca. Caer a otra cosa cuando falta un secreto o la
    base no responde sería mostrar competiciones inventadas como si fueran
    reales, que es peor que no arrancar.

    `token` es el JWT de quien está mirando. Viaja hasta el cliente de datos
    para que `auth.uid()` exista dentro de Postgres; sin él las políticas de
    `permisos.sql` no pueden decidir nada. Ver `_sobre_supabase`.
    """
    url = _leer(secretos, "SUPABASE_URL")
    servicio = _leer(secretos, "SUPABASE_KEY")
    publica = _leer(secretos, "SUPABASE_ANON_KEY")

    if not url:
        raise FaltanCredenciales(
            "Falta el secreto `SUPABASE_URL`, así que no hay a qué conectarse.\n\n"
            "La aplicación necesita `SUPABASE_URL`, `SUPABASE_ANON_KEY` y "
            "`SUPABASE_KEY`. Las tres están en Project Settings → API del "
            "proyecto de Supabase. Ver `docs/FASE_7.md`."
        )
    _exigir_las_dos_claves(servicio, publica)
    repositorios, autenticador = _sobre_supabase(url, servicio, publica, token)
    _exigir_esquema(repositorios[0])
    return ensamblar(repositorios, autenticador)


def ensamblar(repositorios, autenticador) -> Servicios:
    """Monta los servicios sobre los repositorios que se le den.

    Va aparte de `construir` porque montar los servicios y decidir sobre qué
    van montados son dos cosas distintas. La suite de interfaz sustituye la
    segunda y ejercita esta tal cual, así que lo que prueba es la composición
    de verdad y no una copia suya que puede quedarse atrás.
    """
    competiciones, participantes, enfrentamientos, concesiones = repositorios
    politica = Politica(concesiones)
    clasificacion = ServicioDeClasificacion(
        competiciones, participantes, enfrentamientos
    )
    return Servicios(
        competiciones=ServicioDeCompeticiones(competiciones, concesiones, politica),
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
    )


def _exigir_esquema(competiciones) -> None:
    """Comprueba que la base tenga el esquema nuevo, y lo dice si no.

    Sin esto, el fallo aparecería más tarde y en forma de error de red, sin
    pista de que lo que falta es aplicar `esquema.sql`.
    """
    try:
        competiciones.listar()
    except ERRORES_DE_RED:
        # Una red caída no es una base sin preparar. Mandar a aplicar el
        # esquema a quien solo se quedó sin conexión es peor que no decir nada.
        raise
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
        DivisionesSupabase,
        EnfrentamientosSupabase,
        ParticipantesSupabase,
    )
    from ..infraestructura.supabase.transporte import cliente_http

    def crear(clave: str):
        # El transporte reintenta los fallos de red. Sin él, una conexión
        # muerta del pool tumbaba la página entera con una traza de httpx.
        return supabase.create_client(
            url, clave, supabase.ClientOptions(httpx_client=cliente_http())
        )

    datos = crear(clave_publica)
    if token:
        datos.postgrest.auth(token)
    administracion = crear(clave_servicio)

    repositorios = (
        CompeticionesSupabase(datos),
        ParticipantesSupabase(datos),
        EnfrentamientosSupabase(datos),
        ConcesionesSupabase(datos),
    )
    return repositorios, AutenticadorSupabase(administracion)
