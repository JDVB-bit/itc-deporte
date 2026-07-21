"""Adaptadores de Supabase.

El DDL del esquema objetivo, los repositorios y el proveedor de identidad. Los
repositorios heredan los tests de contrato de los de memoria, así que ninguna de
las dos implementaciones puede desviarse de la otra en silencio.

`AutenticadorSupabase` está aquí porque Supabase Auth no depende del esquema
nuevo. Todo lo de este paquete se comprueba con `pytest -m supabase` contra una
instancia real.
"""

from pathlib import Path

_AQUI = Path(__file__).parent

#: DDL del esquema objetivo. No se aplica todavía: ver Fase 7 del plan.
ESQUEMA = _AQUI / "esquema.sql"

#: Concesiones y políticas RLS. Se aplica después de `esquema.sql`.
PERMISOS = _AQUI / "permisos.sql"

#: El corte: retira las tablas viejas. Rompe la aplicación anterior.
CORTE = _AQUI / "corte.sql"

__all__ = ["CORTE", "ESQUEMA", "PERMISOS"]
