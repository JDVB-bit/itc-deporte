"""Errores del dominio.

Heredan de `ValueError` para que una invariante violada se comporte como lo que
es —un argumento inválido— sin obligar a la capa exterior a conocer el dominio.
"""

from __future__ import annotations


class ErrorDeDominio(ValueError):
    """Se violó una invariante de una entidad."""


class ReglaInvalida(ErrorDeDominio):
    """La configuración de una regla es incoherente."""
