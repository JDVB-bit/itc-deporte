"""El mismo contrato, contra Supabase real.

Hereda exactamente las clases que corren contra los repositorios en memoria, así
que si el adaptador de Supabase se desvía del comportamiento esperado, estos
tests lo dicen.

Corren con la clave `service_role`, que salta RLS. Eso es deliberado —aquí se
prueba el adaptador, no los permisos— pero implica que **nada de lo que pasa aquí
dice nada sobre si las políticas RLS funcionan**. Eso es `test_rls.py`.

Para correrlos hace falta un proyecto de Supabase con el esquema aplicado
(`esquema.sql` y `permisos.sql`) y sus credenciales en el entorno:

    SUPABASE_URL=... SUPABASE_KEY=... pytest -m supabase

Se saltan solos si no están, para que la suite normal no dependa de la red.
"""

from __future__ import annotations

import pytest

from conftest import cliente_supabase
from test_repositorios import (
    ContratoDeCompeticiones,
    ContratoDeConcesiones,
    ContratoDeEnfrentamientos,
    ContratoDeParticipantes,
)

pytestmark = pytest.mark.supabase


@pytest.fixture(scope="module")
def cliente():
    return cliente_supabase("SUPABASE_KEY")


#: Tablas a vaciar, de hija a padre para no chocar con las claves ajenas, y la
#: columna por la que filtrar el borrado. No todas tienen `id`: las de relación
#: se identifican por su clave compuesta.
A_VACIAR = (
    ("marcadores", "enfrentamiento_id"),
    ("enfrentamientos", "id"),
    ("inscripciones_en_grupo", "participante_id"),
    ("grupos", "id"),
    ("miembros", "id"),
    ("participantes", "id"),
    ("fases", "id"),
    ("concesiones", "usuario_id"),
    ("competiciones", "id"),
    ("divisiones", "id"),
    ("deportes", "id"),
)


@pytest.fixture
def limpiar(cliente):
    """Deja la instancia como estaba. Se ejecuta antes y después.

    PostgREST exige un filtro en cada `delete` para que un descuido no vacíe una
    tabla entera. Se usa `not.is.null` sobre una columna de la clave primaria:
    no excluye ninguna fila y, a diferencia de comparar con un valor centinela,
    no depende del tipo de la columna —`concesiones.usuario_id` es `uuid` y no
    admite texto arbitrario.
    """
    def borrar():
        for tabla, columna in A_VACIAR:
            cliente.table(tabla).delete().not_.is_(columna, "null").execute()

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


@pytest.fixture
def mundo(cliente, limpiar):
    """Las competiciones y fases de las que cuelga todo lo demás.

    El repositorio en memoria no tiene integridad referencial y toleraba
    participantes de competiciones inexistentes. Postgres no: hay que crear los
    padres. Es el contrato real, y por eso la fixture vive aquí y no en memoria.
    """
    from itc_deporte.domain.competicion import (
        Competicion,
        Deporte,
        FaseDeGrupos,
        FaseEliminatoria,
    )
    from itc_deporte.infraestructura.supabase.repositorios import (
        CompeticionesSupabase,
    )

    deporte = Deporte("microfutbol", "Microfútbol", "⚽")
    repo = CompeticionesSupabase(cliente)
    for competicion_id in ("c1", "c2"):
        repo.guardar(
            Competicion(
                id=competicion_id,
                nombre=f"Competición {competicion_id}",
                deporte=deporte,
                fases=(
                    FaseDeGrupos("f1", "Grupos", 0),
                    FaseEliminatoria("f2", "Eliminatoria", 1),
                ),
            )
        )
    return repo


@pytest.fixture
def participantes_creados(cliente, mundo):
    """Los enfrentamientos referencian participantes: tienen que existir."""
    from itc_deporte.domain.participante import Participante
    from itc_deporte.infraestructura.supabase.repositorios import (
        ParticipantesSupabase,
    )

    repo = ParticipantesSupabase(cliente)
    for i in range(1, 8):
        repo.guardar(Participante(f"p{i}", f"Equipo {i}", "c1"))
    return repo


class TestParticipantesSupabase(ContratoDeParticipantes):
    @pytest.fixture
    def repositorio(self, cliente, mundo):
        from itc_deporte.infraestructura.supabase.repositorios import (
            ParticipantesSupabase,
        )

        return ParticipantesSupabase(cliente)


class TestEnfrentamientosSupabase(ContratoDeEnfrentamientos):
    @pytest.fixture
    def repositorio(self, cliente, participantes_creados):
        from itc_deporte.infraestructura.supabase.repositorios import (
            EnfrentamientosSupabase,
        )

        return EnfrentamientosSupabase(cliente)


class TestConcesionesSupabase(ContratoDeConcesiones):
    @pytest.fixture
    def usuario(self, cliente, mundo):
        """`concesiones.usuario_id` referencia `auth.users`, así que un id
        inventado no vale: hay que dar de alta a alguien de verdad."""
        correo = "contrato@itc.test"
        existentes = cliente.auth.admin.list_users()
        usuarios = existentes if isinstance(existentes, list) else existentes.users
        for u in usuarios:
            if getattr(u, "email", None) == correo:
                return str(u.id)
        creado = cliente.auth.admin.create_user(
            {"email": correo, "password": "contrato-1234", "email_confirm": True}
        )
        return str(creado.user.id)

    @pytest.fixture
    def repositorio(self, cliente, mundo):
        from itc_deporte.infraestructura.supabase.repositorios import (
            ConcesionesSupabase,
        )

        return ConcesionesSupabase(cliente)
