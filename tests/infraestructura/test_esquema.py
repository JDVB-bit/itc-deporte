"""El DDL no se puede probar sin una base, pero sí se puede comprobar que sigue
siendo SQL válido y que cubre lo que el dominio necesita persistir."""

from __future__ import annotations

import pytest

from itc_deporte.infraestructura.supabase import ESQUEMA

sqlglot = pytest.importorskip("sqlglot")


@pytest.fixture(scope="module")
def sentencias():
    return sqlglot.parse(ESQUEMA.read_text(encoding="utf-8"), dialect="postgres")


@pytest.fixture(scope="module")
def tablas(sentencias):
    return {
        s.this.this.name
        for s in sentencias
        if s.key == "create" and s.kind == "TABLE"
    }


def test_el_esquema_existe():
    assert ESQUEMA.is_file()


def test_es_sql_valido_de_postgres(sentencias):
    assert len(sentencias) > 0


def test_cubre_los_agregados_del_dominio(tablas):
    """Cada entidad que el dominio persiste tiene dónde caerse muerta."""
    assert {
        "competiciones",
        "divisiones",
        "participantes",
        "miembros",
        "fases",
        "grupos",
        "enfrentamientos",
        "marcadores",
    } <= tablas


def test_el_enfrentamiento_referencia_participantes_por_id(sentencias):
    """El cambio de fondo: el partido deja de ser texto."""
    enfrentamientos = next(
        s for s in sentencias
        if s.key == "create" and s.kind == "TABLE" and s.this.this.name == "enfrentamientos"
    )
    columnas = {c.name for c in enfrentamientos.this.expressions if hasattr(c, "name")}
    assert {"local_id", "visitante_id"} <= columnas
    assert "enf" not in columnas
