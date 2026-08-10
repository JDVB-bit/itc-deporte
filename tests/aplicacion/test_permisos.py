"""Roles, concesiones y permisos.

El entregable de la fase es `TestElPermisoNoEsCosmetico`: los casos de uso se
invocan aquí directamente, sin pasar por ninguna interfaz, y aun así fallan
cuando el actor no tiene permiso. En el sistema anterior el rol solo escondía
botones, así que este mismo código habría funcionado sin obstáculo.
"""

from __future__ import annotations

import pytest

from itc_deporte.aplicacion.errores import ErrorDeAplicacion
from itc_deporte.aplicacion.permisos import (
    ANONIMO,
    Accion,
    Concesion,
    Identidad,
    PermisoDenegado,
    Politica,
    Rol,
)
from itc_deporte.infraestructura.autenticacion import (
    AutenticadorEnMemoria,
    ConcesionesEnMemoria,
)

ADMIN = Identidad("admin", "admin@itc.edu.co")
PROFE = Identidad("profe", "profe@itc.edu.co")
OTRO = Identidad("otro", "otro@itc.edu.co")


@pytest.fixture
def politica():
    return Politica(
        ConcesionesEnMemoria(
            [
                Concesion("admin", Rol.ADMIN),
                Concesion("profe", Rol.REGISTRADOR, "c1"),
            ]
        )
    )


class TestConcesion:
    def test_un_registrador_necesita_competicion(self):
        """La decisión del plan, impuesta por el tipo: no es un rol global."""
        with pytest.raises(ErrorDeAplicacion, match="por competición"):
            Concesion("profe", Rol.REGISTRADOR)

    def test_un_admin_no_se_otorga_por_competicion(self):
        with pytest.raises(ErrorDeAplicacion, match="global"):
            Concesion("admin", Rol.ADMIN, "c1")

    def test_visitante_no_se_otorga(self):
        """Es lo que se es sin concesión alguna."""
        with pytest.raises(ErrorDeAplicacion, match="sin concesión"):
            Concesion("alguien", Rol.VISITANTE, "c1")

    def test_el_admin_es_global(self):
        assert Concesion("admin", Rol.ADMIN).es_global

    def test_el_registrador_no_lo_es(self):
        assert not Concesion("profe", Rol.REGISTRADOR, "c1").es_global

    def test_rechaza_usuario_vacio(self):
        with pytest.raises(ErrorDeAplicacion):
            Concesion("", Rol.ADMIN)


class TestIdentidad:
    def test_rechaza_usuario_vacio(self):
        with pytest.raises(ErrorDeAplicacion):
            Identidad("")

    def test_el_correo_es_opcional(self):
        assert Identidad("u1").email is None


class TestRolesEfectivos:
    def test_cualquiera_es_visitante(self, politica):
        assert politica.roles_de(ANONIMO) == frozenset({Rol.VISITANTE})

    def test_el_admin_lo_es_en_todas_partes(self, politica):
        assert Rol.ADMIN in politica.roles_de(ADMIN, "cualquiera")

    def test_el_registrador_lo_es_en_la_suya(self, politica):
        assert Rol.REGISTRADOR in politica.roles_de(PROFE, "c1")

    def test_fuera_de_la_suya_es_un_visitante_mas(self, politica):
        """El punto entero de que la concesión tenga alcance."""
        assert politica.roles_de(PROFE, "c2") == frozenset({Rol.VISITANTE})

    def test_sin_ambito_el_registrador_no_cuenta(self, politica):
        assert politica.roles_de(PROFE) == frozenset({Rol.VISITANTE})

    def test_al_anonimo_no_se_le_consulta_el_repositorio(self):
        """La regresión del fallo que tumbó producción.

        `ANONIMO` no lleva un id de usuario de verdad. Preguntar por él a la
        base reventaba: `concesiones.usuario_id` es `uuid` y Postgres rechaza
        `'anonimo'`. Solo se llegaba a este camino con la base vacía, que es
        justo el estado de un despliegue recién montado.
        """

        class RepositorioQueProtesta:
            def de_usuario(self, usuario_id):
                raise AssertionError(
                    f"no se debe preguntar por {usuario_id!r}: no es un usuario"
                )

        assert Politica(RepositorioQueProtesta()).roles_de(ANONIMO) == frozenset(
            {Rol.VISITANTE}
        )


class TestQuienPuedeQue:
    @pytest.mark.parametrize("accion", list(Accion))
    def test_el_admin_puede_todo(self, politica, accion):
        assert politica.puede(ADMIN, accion, "c1")

    @pytest.mark.parametrize(
        "accion",
        [Accion.LEER, Accion.INSCRIBIR_PARTICIPANTE, Accion.REGISTRAR_RESULTADO],
    )
    def test_el_registrador_puede_lo_suyo_en_su_competicion(self, politica, accion):
        assert politica.puede(PROFE, accion, "c1")

    @pytest.mark.parametrize(
        "accion",
        [
            Accion.SORTEAR,
            Accion.ADMINISTRAR_COMPETICION,
            Accion.GESTIONAR_REGISTRADORES,
        ],
    )
    def test_el_registrador_no_administra(self, politica, accion):
        assert not politica.puede(PROFE, accion, "c1")

    def test_el_registrador_no_puede_en_otra_competicion(self, politica):
        assert not politica.puede(PROFE, Accion.REGISTRAR_RESULTADO, "c2")

    def test_cualquiera_puede_leer(self, politica):
        assert politica.puede(ANONIMO, Accion.LEER, "c1")
        assert politica.puede(OTRO, Accion.LEER)

    def test_un_desconocido_no_puede_escribir(self, politica):
        assert not politica.puede(OTRO, Accion.REGISTRAR_RESULTADO, "c1")

    def test_exigir_deja_pasar_a_quien_puede(self, politica):
        politica.exigir(ADMIN, Accion.SORTEAR, "c1")

    def test_exigir_corta_a_quien_no(self, politica):
        with pytest.raises(PermisoDenegado, match="sortear"):
            politica.exigir(PROFE, Accion.SORTEAR, "c1")

    def test_el_mensaje_nombra_la_competicion(self, politica):
        with pytest.raises(PermisoDenegado, match="c2"):
            politica.exigir(PROFE, Accion.REGISTRAR_RESULTADO, "c2")


class TestCrearCompeticionNoNecesitaAmbito:
    """Crear no ocurre *dentro* de ninguna competición, y ahí estaba el nudo.

    La concesión de un registrador siempre lleva competición, así que preguntar
    por sus roles sin ámbito no encontraba ninguna: la acción quedaba fuera de
    su alcance por construcción, no por decisión.
    """

    def test_el_registrador_puede_crear_la_suya(self, politica):
        assert politica.puede(PROFE, Accion.CREAR_COMPETICION)

    def test_aunque_su_concesion_sea_de_otra_competicion(self, politica):
        """Su única concesión es sobre `c1` y aun así puede crear una nueva."""
        assert politica.puede(PROFE, Accion.CREAR_COMPETICION, "c2")

    def test_el_admin_tambien(self, politica):
        assert politica.puede(ADMIN, Accion.CREAR_COMPETICION)

    def test_quien_no_tiene_ninguna_concesion_no(self, politica):
        """Estar identificado no basta: hay que ser registrador de algo."""
        assert not politica.puede(OTRO, Accion.CREAR_COMPETICION)

    def test_un_visitante_sin_identificar_tampoco(self, politica):
        assert not politica.puede(ANONIMO, Accion.CREAR_COMPETICION)

    def test_y_no_le_abre_ninguna_otra_puerta(self, politica):
        """Crear no arrastra administrar: sortear sigue siendo del admin."""
        assert not politica.puede(PROFE, Accion.SORTEAR, "c1")
        assert not politica.puede(PROFE, Accion.ADMINISTRAR_COMPETICION, "c1")

    def test_a_anonimo_no_se_le_preguntan_las_concesiones(self):
        """Su id no es un UUID: preguntarlo tumbó producción una vez.

        `es_registrador_en_alguna` es un camino nuevo hacia el repositorio, así
        que repite la guarda en lugar de confiar en que nadie llegue.
        """

        class Explosivo:
            def de_usuario(self, usuario_id):
                raise AssertionError(f"no debió preguntarse por {usuario_id!r}")

        assert not Politica(Explosivo()).es_registrador_en_alguna(ANONIMO)


class TestConcesionesEnMemoria:
    def test_otorgar_y_consultar(self):
        repo = ConcesionesEnMemoria()
        repo.otorgar(Concesion("profe", Rol.REGISTRADOR, "c1"))
        assert len(repo.de_usuario("profe")) == 1
        assert len(repo.de_competicion("c1")) == 1

    def test_otorgar_dos_veces_no_duplica(self):
        repo = ConcesionesEnMemoria()
        for _ in range(2):
            repo.otorgar(Concesion("profe", Rol.REGISTRADOR, "c1"))
        assert len(repo.de_usuario("profe")) == 1

    def test_revocar(self):
        repo = ConcesionesEnMemoria([Concesion("profe", Rol.REGISTRADOR, "c1")])
        repo.revocar("profe", "c1")
        assert repo.de_usuario("profe") == ()

    def test_revocar_una_competicion_no_toca_las_demas(self):
        repo = ConcesionesEnMemoria(
            [
                Concesion("profe", Rol.REGISTRADOR, "c1"),
                Concesion("profe", Rol.REGISTRADOR, "c2"),
            ]
        )
        repo.revocar("profe", "c1")
        assert [c.competicion_id for c in repo.de_usuario("profe")] == ["c2"]

    def test_revocar_lo_que_no_existe_no_revienta(self):
        ConcesionesEnMemoria().revocar("nadie", "c1")


class TestAutenticadorEnMemoria:
    def test_identificar(self):
        auth = AutenticadorEnMemoria([ADMIN])
        sesion = auth.iniciar_sesion(ADMIN.email, "")
        assert auth.identificar(sesion.token) == ADMIN

    def test_un_token_desconocido_no_identifica(self):
        assert AutenticadorEnMemoria().identificar("fantasma") is None

    def test_el_id_de_usuario_no_sirve_como_token(self):
        """La regresión del fallo que llegó a producción.

        Este doble aceptaba el UUID como token; el adaptador de Supabase no.
        Mientras el doble fue más permisivo, la interfaz guardaba el id, todos
        los tests pasaban y en producción nadie llegaba a ser administrador.
        """
        auth = AutenticadorEnMemoria([ADMIN])
        assert auth.identificar(ADMIN.usuario_id) is None

    def test_sin_credenciales_no_hay_sesion(self):
        assert AutenticadorEnMemoria().iniciar_sesion("nadie@itc.edu.co", "") is None

    def test_buscar_por_correo(self):
        auth = AutenticadorEnMemoria([PROFE])
        assert auth.por_email("profe@itc.edu.co") == PROFE

    def test_invitar_da_de_alta(self):
        auth = AutenticadorEnMemoria()
        invitado = auth.invitar("nuevo@itc.edu.co")
        assert auth.por_email("nuevo@itc.edu.co") == invitado

    def test_invitar_a_quien_ya_esta_lo_devuelve(self):
        auth = AutenticadorEnMemoria([PROFE])
        assert auth.invitar("profe@itc.edu.co") == PROFE
