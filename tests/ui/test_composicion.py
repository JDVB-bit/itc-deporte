"""Cómo se arman los clientes de Supabase.

Este archivo existe por un fallo que no se veía desde ninguna otra prueba: había
**un solo** cliente, creado una vez por proceso, y nunca llevaba la sesión de
nadie. Dentro de Postgres `auth.uid()` era NULL, así que `es_admin()` y
`puede_registrar()` devolvían false siempre y ninguna política de `permisos.sql`
podía autorizar una escritura.

La aplicación parecía funcionar porque se desplegaba con la clave `service_role`,
que salta RLS por completo. Es decir: la «segunda línea de defensa» que
`permisos.sql` documenta no estaba activa, y nada lo decía.

La suite de contrato tampoco podía verlo: corre a propósito con `service_role`.
"""

from __future__ import annotations

import pytest

from itc_deporte.ui.composicion import (
    BaseSinPreparar,
    ClavesIncompletas,
    FaltanCredenciales,
    construir,
)

URL = "https://proyecto.supabase.co"
ANON = "anon-" + "x" * 200
SERVICIO = "service-" + "x" * 200


class _Respuesta:
    data: list = []


class _Consulta:
    """Lo justo para que `listar()` responda «no hay nada»."""

    def select(self, *_args, **_kwargs):
        return self

    def execute(self):
        return _Respuesta()


class _Postgrest:
    def __init__(self) -> None:
        self.jwt = None

    def auth(self, token):
        self.jwt = token


class ClienteFalso:
    """Un doble que solo recuerda con qué se le construyó."""

    def __init__(self, url, clave) -> None:
        self.url = url
        self.clave = clave
        self.postgrest = _Postgrest()
        self.auth = object()  # lo que consume `AutenticadorSupabase`

    def table(self, _nombre):
        return _Consulta()


@pytest.fixture
def clientes(monkeypatch):
    """Intercepta `create_client` y devuelve los que se hayan creado, en orden."""
    import supabase

    creados: list[ClienteFalso] = []

    def crear(url, clave, *_args, **_kwargs):
        cliente = ClienteFalso(url, clave)
        creados.append(cliente)
        return cliente

    monkeypatch.setattr(supabase, "create_client", crear)
    return creados


@pytest.fixture
def con_credenciales(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", URL)
    monkeypatch.setenv("SUPABASE_ANON_KEY", ANON)
    monkeypatch.setenv("SUPABASE_KEY", SERVICIO)


class TestLasDosClavesSonObligatorias:
    """Silenciar la que falte sería volver al fallo: con solo `service_role` la
    aplicación escribe, pero saltándose RLS y sin que nadie se entere."""

    def test_sin_la_publica_lo_dice_y_la_nombra(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", URL)
        monkeypatch.setenv("SUPABASE_KEY", SERVICIO)
        monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
        with pytest.raises(ClavesIncompletas, match="SUPABASE_ANON_KEY"):
            construir(None)

    def test_sin_la_de_servicio_tambien(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", URL)
        monkeypatch.setenv("SUPABASE_ANON_KEY", ANON)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)
        with pytest.raises(ClavesIncompletas, match="SUPABASE_KEY"):
            construir(None)

    def test_el_mensaje_explica_para_que_es_cada_una(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", URL)
        monkeypatch.setenv("SUPABASE_KEY", SERVICIO)
        monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
        with pytest.raises(ClavesIncompletas, match="RLS"):
            construir(None)

    def test_sigue_siendo_un_fallo_de_arranque(self, monkeypatch):
        """`app.py` atrapa `SistemaSinPreparar`; que herede importa."""
        from itc_deporte.ui.composicion import SistemaSinPreparar

        monkeypatch.setenv("SUPABASE_URL", URL)
        monkeypatch.setenv("SUPABASE_KEY", SERVICIO)
        monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
        with pytest.raises(SistemaSinPreparar):
            construir(None)
        assert issubclass(BaseSinPreparar, SistemaSinPreparar)


class TestCadaClienteConSuClave:
    def test_los_datos_van_con_la_clave_publica(self, clientes, con_credenciales):
        construir(None)
        assert clientes[0].clave == ANON

    def test_la_administracion_va_con_la_de_servicio(self, clientes, con_credenciales):
        """`invitar` y `por_email` usan la API de administración, que la exige."""
        construir(None)
        assert clientes[1].clave == SERVICIO

    def test_se_crean_exactamente_dos(self, clientes, con_credenciales):
        construir(None)
        assert len(clientes) == 2


class TestLaSesionViajaHastaPostgres:
    """Lo que faltaba: sin el JWT en el cliente de datos, `auth.uid()` es NULL
    y RLS no puede autorizar nada."""

    def test_el_token_se_adjunta_al_cliente_de_datos(self, clientes, con_credenciales):
        construir(None, token="jwt-de-quien-mira")
        assert clientes[0].postgrest.jwt == "jwt-de-quien-mira"

    def test_un_visitante_no_adjunta_ninguno(self, clientes, con_credenciales):
        """Sin identificarse se lee con la clave pública y nada más."""
        construir(None)
        assert clientes[0].postgrest.jwt is None

    def test_la_administracion_nunca_lo_lleva(self, clientes, con_credenciales):
        """No toca datos, así que no puede saltarse RLS por descuido."""
        construir(None, token="jwt-de-quien-mira")
        assert clientes[1].postgrest.jwt is None


class TestSinCredenciales:
    """Ya no hay a dónde caer: antes esto arrancaba una demostración."""

    def _sin_nada(self, monkeypatch):
        for clave in ("SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_ANON_KEY"):
            monkeypatch.delenv(clave, raising=False)

    def test_falla_en_vez_de_arrancar(self, monkeypatch):
        self._sin_nada(monkeypatch)
        with pytest.raises(FaltanCredenciales):
            construir(None)

    def test_y_no_llega_a_tocar_supabase(self, clientes, monkeypatch):
        self._sin_nada(monkeypatch)
        with pytest.raises(FaltanCredenciales):
            construir(None)
        assert clientes == []
