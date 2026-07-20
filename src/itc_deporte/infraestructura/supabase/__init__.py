"""Adaptadores de Supabase.

Por ahora solo el DDL del esquema objetivo. Los repositorios llegan con la
Fase 7, cuando el esquema se aplique: escribirlos antes sería comprometer
código que no puede ejecutarse contra ninguna tabla real, que es justamente el
antipatrón que dejó muerto el bracket anterior.

Cuando existan, heredarán los tests de `tests/contratos/` y correrán las mismas
pruebas que los repositorios en memoria.
"""

from pathlib import Path

#: DDL del esquema objetivo. No se aplica todavía: ver Fase 7 del plan.
ESQUEMA = Path(__file__).parent / "esquema.sql"

__all__ = ["ESQUEMA"]
