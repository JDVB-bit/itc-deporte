"""El mismo contrato, contra Supabase real.

Hereda exactamente las clases que corren contra los repositorios en memoria, así
que si el adaptador de Supabase se desvía del comportamiento esperado, estos
tests lo dicen. **Todavía no se han ejecutado nunca.**

Para correrlos hace falta un proyecto de Supabase con el esquema aplicado
(`esquema.sql` y `permisos.sql`) y sus credenciales en el entorno:

    SUPABASE_URL=... SUPABASE_KEY=... pytest -m supabase

Se saltan solos si no están, para que la suite normal no dependa de la red.
"""

from __future__ import annotations

import os

import pytest

from test_repositorios import (
    ContratoDeCompeticiones,
    ContratoDeConcesiones,
    ContratoDeEnfrentamientos,
    ContratoDeParticipantes,
)

pytestmark = pytest.mark.supabase


@pytest.fixture(scope="module")
def cliente():
    url, clave = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
    if not url or not clave:
        pytest.skip("Faltan SUPABASE_URL y SUPABASE_KEY.")
    supabase = pytest.importorskip("supabase")
    return supabase.create_client(url, clave)


@pytest.fixture
def limpiar(cliente):
    """Deja la instancia como estaba. Se ejecuta antes y después."""
    def borrar():
        for tabla in (
            "marcadores", "enfrentamientos", "inscripciones_en_grupo", "grupos",
            "miembros", "participantes", "fases", "concesiones", "competiciones",
            "divisiones", "deportes",
        ):
            cliente.table(tabla).delete().neq("id", "__imposible__").execute()

    borrar()
    yield
    borrar()


class TestCompeticionesSupabase(ContratoDeCompeticiones):
    @pytest.fixture
    def repositorio(self, cliente, limpiar):
        from itc_deporte.infraestructura.supabase.repositorios import (
            CompeticionesSupabase,
        )

        return CompeticionesSupabase(cliente)


class TestParticipantesSupabase(ContratoDeParticipantes):
    @pytest.fixture
    def repositorio(self, cliente, limpiar):
        from itc_deporte.infraestructura.supabase.repositorios import (
            ParticipantesSupabase,
        )

        return ParticipantesSupabase(cliente)


class TestEnfrentamientosSupabase(ContratoDeEnfrentamientos):
    @pytest.fixture
    def repositorio(self, cliente, limpiar):
        from itc_deporte.infraestructura.supabase.repositorios import (
            EnfrentamientosSupabase,
        )

        return EnfrentamientosSupabase(cliente)


class TestConcesionesSupabase(ContratoDeConcesiones):
    @pytest.fixture
    def repositorio(self, cliente, limpiar):
        from itc_deporte.infraestructura.supabase.repositorios import (
            ConcesionesSupabase,
        )

        return ConcesionesSupabase(cliente)
