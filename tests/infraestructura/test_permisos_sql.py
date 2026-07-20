"""El DDL de permisos.

**Límite de estos tests.** `sqlglot` no entiende `CREATE POLICY` ni
`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`: los reconoce como comandos opacos y
no comprueba su sintaxis. Así que de este fichero solo queda verificada la tabla
`concesiones`, sus índices y las dos funciones. **Las políticas RLS no las valida
nada de este repositorio**; la única forma de comprobarlas es aplicarlas contra
Postgres, y eso ocurre en la Fase 7.

Lo que sí se comprueba aquí es de otro tipo y sí tiene valor: que cada tabla del
esquema tenga RLS activado y al menos una política, para que ninguna quede
expuesta por olvido al añadirla.
"""

from __future__ import annotations

import re

import pytest

from itc_deporte.infraestructura.supabase import ESQUEMA, PERMISOS

sqlglot = pytest.importorskip("sqlglot")


@pytest.fixture(scope="module")
def sql():
    return PERMISOS.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def tablas_del_esquema():
    sentencias = sqlglot.parse(ESQUEMA.read_text(encoding="utf-8"), dialect="postgres")
    return {
        s.this.this.name
        for s in sentencias
        if s.key == "create" and s.kind == "TABLE"
    }


def test_el_fichero_existe():
    assert PERMISOS.is_file()


class TestLoQueSqlglotSiValida:
    def test_declara_la_tabla_de_concesiones(self, sql):
        tablas = {
            s.this.this.name
            for s in sqlglot.parse(sql, dialect="postgres")
            if s is not None and s.key == "create" and s.kind == "TABLE"
        }
        assert tablas == {"concesiones"}

    def test_declara_las_dos_funciones_de_apoyo(self, sql):
        funciones = [
            s
            for s in sqlglot.parse(sql, dialect="postgres")
            if s is not None and s.key == "create" and s.kind == "FUNCTION"
        ]
        assert len(funciones) == 2


class TestInvariantesDeLaConcesion:
    """Las mismas que impone `Concesion` en memoria, ahora también en la base."""

    def test_un_registrador_necesita_competicion(self, sql):
        assert "rol <> 'registrador' or competicion_id is not null" in sql

    def test_un_admin_no_la_lleva(self, sql):
        assert "rol <> 'admin' or competicion_id is null" in sql

    def test_dos_concesiones_globales_del_mismo_usuario_colisionan(self, sql):
        """Sin `nulls not distinct`, NULL != NULL las dejaría duplicarse."""
        assert "unique nulls not distinct (usuario_id, competicion_id)" in sql

    def test_las_concesiones_cuelgan_de_supabase_auth(self, sql):
        """Es lo que sustituye a la tabla `usuarios` con bcrypt propio."""
        assert "references auth.users (id) on delete cascade" in sql


class TestNingunaTablaQuedaExpuesta:
    """Comprobación textual, no sintáctica: que no se olvide ninguna."""

    def _tablas_con(self, sql, patron):
        return set(re.findall(patron, sql))

    def test_todas_las_tablas_tienen_rls_activado(self, sql, tablas_del_esquema):
        activadas = self._tablas_con(
            sql, r"alter table (\w+)\s+enable row level security"
        )
        assert tablas_del_esquema <= activadas

    def test_la_propia_tabla_de_concesiones_tambien(self, sql):
        assert "alter table concesiones    enable row level security" in sql

    def test_todas_permiten_lectura_publica(self, sql, tablas_del_esquema):
        """El visitante consulta tablas y resultados sin identificarse."""
        con_lectura = self._tablas_con(
            sql, r'create policy "lectura publica" on (\w+)'
        )
        assert tablas_del_esquema <= con_lectura

    def test_toda_tabla_con_rls_tiene_alguna_politica(self, sql):
        """RLS activado y sin políticas deja la tabla inaccesible."""
        activadas = self._tablas_con(
            sql, r"alter table (\w+)\s+enable row level security"
        )
        con_politica = self._tablas_con(sql, r'create policy "[^"]+" on (\w+)')
        assert activadas - con_politica == set()

    def test_las_funciones_fijan_su_search_path(self, sql):
        """`security definer` sin `search_path` fijo se puede redirigir a un
        esquema plantado por otro.

        Se cuentan solo las declaraciones, no las menciones en comentarios.
        """
        declaraciones = re.findall(r"^\s+language sql .*$", sql, re.MULTILINE)
        assert len(declaraciones) == 2
        assert all(
            "security definer set search_path = public" in linea
            for linea in declaraciones
        )


@pytest.mark.supabase
class TestContraPostgresReal:
    def test_pendiente_de_aplicarse(self):
        pytest.skip(
            "Las políticas RLS solo se validan aplicándolas contra Postgres. "
            "Ocurre en la Fase 7, con la migración."
        )
