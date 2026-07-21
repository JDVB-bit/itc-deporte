"""Casos de uso.

Aquí se decide. La interfaz pasa a pedir cosas —"sortea esta fase", "registra
este resultado"— en lugar de orquestar consultas, comprobar condiciones y armar
escrituras por su cuenta, que es lo que hacía `app.py`.

Cada servicio recibe sus repositorios por constructor y los conoce solo a través
de los protocolos de `puertos.py`. Ninguno importa Supabase.
"""

from .clasificacion import ServicioDeClasificacion
from .competiciones import ServicioDeCompeticiones
from .cuadro import ServicioDeCuadroFinal
from .inscripciones import ServicioDeInscripciones
from .registradores import ServicioDeRegistradores
from .resultados import ServicioDeResultados
from .sorteo import ServicioDeSorteo

__all__ = [
    "ServicioDeClasificacion",
    "ServicioDeCompeticiones",
    "ServicioDeCuadroFinal",
    "ServicioDeInscripciones",
    "ServicioDeRegistradores",
    "ServicioDeResultados",
    "ServicioDeSorteo",
]
