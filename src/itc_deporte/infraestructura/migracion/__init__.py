"""Migración de los datos heredados al modelo nuevo.

Paquete de vida corta: existe para ejecutar la Fase 7 una vez y desaparecer
después, junto con `legado/`.
"""

from .traductor import Conflicto, Reporte, traducir

__all__ = ["Conflicto", "Reporte", "traducir"]
