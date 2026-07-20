"""Adaptadores de Supabase.

El DDL del esquema objetivo y el proveedor de identidad. Los **repositorios**
llegan con la Fase 7, cuando el esquema se aplique: escribirlos antes sería
comprometer código que no puede ejecutarse contra ninguna tabla real, que es el
antipatrón que dejó muerto el bracket anterior. Cuando existan, heredarán los
tests de `tests/contratos/`.

`AutenticadorSupabase` sí está aquí porque Supabase Auth existe ya y no depende
del esquema nuevo. Su lógica de traducción está probada; la forma de la API de
`supabase-py` no, y eso exige una instancia real (`pytest -m supabase`).
"""

from pathlib import Path

_AQUI = Path(__file__).parent

#: DDL del esquema objetivo. No se aplica todavía: ver Fase 7 del plan.
ESQUEMA = _AQUI / "esquema.sql"

#: Concesiones y políticas RLS. Se aplica después de `esquema.sql`.
PERMISOS = _AQUI / "permisos.sql"

__all__ = ["ESQUEMA", "PERMISOS"]
