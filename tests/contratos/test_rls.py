"""El comportamiento de las políticas RLS.

El resto de la suite de Supabase corre con `service_role`, que **salta RLS por
completo**. Que esos 42 tests pasen no dice absolutamente nada sobre si las
políticas permiten o niegan lo que deben: solo que el adaptador habla bien con
PostgREST.

Esto es lo único que comprueba la segunda línea de defensa, y por eso necesita
una credencial más: la clave `anon`, que es la que llevaría un navegador.

    SUPABASE_URL=... SUPABASE_KEY=<service_role> SUPABASE_ANON_KEY=<anon> \\
        pytest -m supabase

Sin `SUPABASE_ANON_KEY` se salta, y entonces las políticas quedan sin verificar
—que es exactamente lo que había antes de este fichero.
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.supabase


@pytest.fixture(scope="module")
def admin(crear_cliente_supabase):
    """Cliente con `service_role`: escribe saltándose RLS. Prepara el terreno."""
    return crear_cliente_supabase("SUPABASE_KEY")


@pytest.fixture(scope="module")
def anonimo(crear_cliente_supabase):
    """Cliente con la clave `anon`: sujeto a RLS, como un visitante.

    Sin `SUPABASE_ANON_KEY` esto se salta, y entonces las políticas quedan sin
    comprobar: `service_role` las ignora.
    """
    if not os.getenv("SUPABASE_ANON_KEY"):
        pytest.skip(
            "Falta SUPABASE_ANON_KEY. Sin ella no se puede comprobar RLS: "
            "la clave service_role salta las políticas."
        )
    return crear_cliente_supabase("SUPABASE_ANON_KEY")


@pytest.fixture
def competicion_de_prueba(admin):
    """Una competición creada con service_role, para que el anónimo la lea."""
    from itc_deporte.domain.competicion import Competicion, Deporte
    from itc_deporte.infraestructura.supabase.repositorios import (
        CompeticionesSupabase,
    )

    repo = CompeticionesSupabase(admin)
    repo.guardar(
        Competicion(
            id="rls-prueba",
            nombre="Prueba de RLS",
            deporte=Deporte("microfutbol", "Microfútbol", "⚽"),
        )
    )
    yield "rls-prueba"
    admin.table("competiciones").delete().eq("id", "rls-prueba").execute()


def escribir(cliente, tabla, fila):
    """Intenta insertar y dice si RLS lo dejó pasar."""
    from postgrest.exceptions import APIError

    try:
        cliente.table(tabla).insert(fila).execute()
        return True
    except APIError:
        return False


class TestLeerEsPublico:
    """Un visitante consulta tablas, resultados y cuadros sin identificarse."""

    def test_el_anonimo_lee_competiciones(self, anonimo, competicion_de_prueba):
        respuesta = (
            anonimo.table("competiciones")
            .select("*")
            .eq("id", competicion_de_prueba)
            .execute()
        )
        assert len(respuesta.data) == 1

    @pytest.mark.parametrize(
        "tabla",
        ["deportes", "competiciones", "participantes", "enfrentamientos", "marcadores"],
    )
    def test_el_anonimo_lee_todas_las_tablas_publicas(self, anonimo, tabla):
        anonimo.table(tabla).select("*").limit(1).execute()


class TestEscribirExigeConcesion:
    """La segunda línea: si alguien alcanzara la API saltándose la aplicación."""

    def test_el_anonimo_no_crea_competiciones(self, anonimo):
        assert not escribir(
            anonimo,
            "competiciones",
            {"id": "colada", "nombre": "Colada", "deporte_id": "microfutbol"},
        )

    def test_el_anonimo_no_crea_deportes(self, anonimo):
        assert not escribir(anonimo, "deportes", {"id": "colado", "nombre": "Colado"})

    def test_el_anonimo_no_inscribe_participantes(self, anonimo, competicion_de_prueba):
        assert not escribir(
            anonimo,
            "participantes",
            {
                "id": "colado",
                "competicion_id": competicion_de_prueba,
                "nombre": "Colado",
            },
        )

    def test_el_anonimo_no_registra_resultados(self, anonimo):
        assert not escribir(
            anonimo,
            "marcadores",
            {
                "enfrentamiento_id": "cualquiera",
                "total_local": 9,
                "total_visitante": 0,
            },
        )

    def test_el_anonimo_no_se_hace_administrador(self, anonimo):
        """El ataque que más importa cortar."""
        assert not escribir(
            anonimo,
            "concesiones",
            {
                "usuario_id": "00000000-0000-0000-0000-000000000000",
                "rol": "admin",
                "competicion_id": None,
            },
        )

    def test_el_anonimo_no_ve_las_concesiones_de_otros(self, anonimo):
        """La política solo deja ver las propias, y un anónimo no tiene."""
        respuesta = anonimo.table("concesiones").select("*").execute()
        assert respuesta.data == []


class TestCrearCompeticionSigueExigiendoConcesion:
    """`competiciones` y `fases` admiten ahora un `insert` de quien sea
    registrador de algo. La parte que hay que comprobar es la otra: que sin
    concesión alguna sigue cerrado."""

    def test_el_anonimo_no_crea_fases(self, anonimo, competicion_de_prueba):
        assert not escribir(
            anonimo,
            "fases",
            {
                "id": "colada",
                "competicion_id": competicion_de_prueba,
                "tipo": "grupos",
                "nombre": "Colada",
                "orden": 0,
            },
        )

    def test_el_anonimo_no_se_hace_registrador(self, anonimo, competicion_de_prueba):
        """La política de «quedarse con la que uno crea» exige `es_registrador()`,
        justo para que nadie se otorgue la primera concesión a sí mismo."""
        assert not escribir(
            anonimo,
            "concesiones",
            {
                "usuario_id": "00000000-0000-0000-0000-000000000000",
                "rol": "registrador",
                "competicion_id": competicion_de_prueba,
            },
        )

    def test_el_anonimo_no_crea_divisiones(self, anonimo, competicion_de_prueba):
        """Dejaron de ser «solo admin» para que un registrador pueda inscribir
        con el curso; sin concesión siguen cerradas."""
        assert not escribir(
            anonimo,
            "divisiones",
            {"id": "601", "competicion_id": competicion_de_prueba, "nombre": "601"},
        )


class TestLasFuncionesDeApoyo:
    def test_es_admin_dice_que_no_para_un_anonimo(self, anonimo):
        assert anonimo.rpc("es_admin", {}).execute().data is False

    def test_puede_registrar_dice_que_no_para_un_anonimo(self, anonimo):
        respuesta = anonimo.rpc("puede_registrar", {"comp": "rls-prueba"}).execute()
        assert respuesta.data is False

    def test_es_registrador_dice_que_no_para_un_anonimo(self, anonimo):
        assert anonimo.rpc("es_registrador", {}).execute().data is False
