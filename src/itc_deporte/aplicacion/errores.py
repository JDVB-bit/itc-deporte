"""Errores de la capa de aplicación.

Se distinguen del `ErrorDeDominio` a propósito: aquel dice que una entidad sería
incoherente, este que la operación pedida no procede con el estado actual del
sistema.
"""

from __future__ import annotations


class ErrorDeAplicacion(Exception):
    """Base de los errores de caso de uso."""


class NoEncontrado(ErrorDeAplicacion, LookupError):
    """Se pidió algo que el repositorio no tiene."""


class OperacionInvalida(ErrorDeAplicacion, ValueError):
    """La operación no procede con el estado actual."""
    
class ErrorDeInfraestructura(ErrorDeAplicacion, RuntimeError):
    """Un adaptador externo (red, base de datos, proveedor de identidad) falló."""
