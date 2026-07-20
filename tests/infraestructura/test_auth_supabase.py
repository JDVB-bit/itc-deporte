"""El adaptador de Supabase Auth, contra un doble del cliente.

**Lo que estos tests verifican:** que la traducción de respuestas de Supabase a
`Identidad` es correcta, y que los casos raros —token vacío, token inválido,
usuario sin id— se resuelven como deben.

**Lo que NO verifican:** que las llamadas coincidan con la API real de
`supabase-py`. El doble responde lo que yo supuse que responde Supabase; si esa
suposición es errónea, estos tests pasan igual. Eso lo comprueba
`TestContraSupabaseReal`, al final, bajo el marcador `supabase`.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from itc_deporte.aplicacion.permisos import Identidad
from itc_deporte.aplicacion.puertos import Autenticador
from itc_deporte.infraestructura.supabase.auth import AutenticadorSupabase


@dataclass
class UsuarioFalso:
    id: str
    email: str | None = None


@dataclass
class RespuestaFalsa:
    user: UsuarioFalso | None


class AdminFalso:
    def __init__(self, usuarios, como_lista=True):
        self.usuarios = list(usuarios)
        self.como_lista = como_lista
        self.invitados: list[str] = []

    def list_users(self):
        if self.como_lista:
            return list(self.usuarios)

        class ConAtributo:
            users = self.usuarios

        return ConAtributo()

    def invite_user_by_email(self, email):
        nuevo = UsuarioFalso(id=f"uuid-{len(self.usuarios) + 1}", email=email)
        self.usuarios.append(nuevo)
        self.invitados.append(email)
        return RespuestaFalsa(user=nuevo)


class AuthFalso:
    def __init__(self, usuarios=(), como_lista=True, token_valido="jwt-bueno"):
        self.admin = AdminFalso(usuarios, como_lista)
        self._token_valido = token_valido

    def get_user(self, token):
        if token != self._token_valido:
            raise ValueError("token inválido")
        return RespuestaFalsa(user=self.admin.usuarios[0])


class ClienteFalso:
    def __init__(self, **kwargs):
        self.auth = AuthFalso(**kwargs)


ANA = UsuarioFalso(id="uuid-ana", email="ana@itc.edu.co")
LUIS = UsuarioFalso(id="uuid-luis", email="luis@itc.edu.co")


@pytest.fixture
def cliente():
    return ClienteFalso(usuarios=[ANA, LUIS])


@pytest.fixture
def autenticador(cliente):
    return AutenticadorSupabase(cliente)


def test_satisface_el_puerto(autenticador):
    assert isinstance(autenticador, Autenticador)


class TestIdentificar:
    def test_un_token_valido_da_la_identidad(self, autenticador):
        identidad = autenticador.identificar("jwt-bueno")
        assert identidad == Identidad("uuid-ana", "ana@itc.edu.co")

    def test_un_token_invalido_no_revienta(self, autenticador):
        """Un token caducado no es un error del sistema: es alguien sin identificar."""
        assert autenticador.identificar("jwt-caducado") is None

    def test_un_token_vacio_ni_siquiera_pregunta(self, autenticador):
        assert autenticador.identificar("") is None

    def test_una_respuesta_sin_usuario_da_none(self):
        class SinUsuario:
            auth = type("A", (), {"get_user": staticmethod(lambda t: RespuestaFalsa(None))})()

        assert AutenticadorSupabase(SinUsuario()).identificar("x") is None

    def test_un_usuario_sin_id_da_none(self):
        class SinId:
            auth = type(
                "A",
                (),
                {"get_user": staticmethod(lambda t: RespuestaFalsa(UsuarioFalso("")))},
            )()

        assert AutenticadorSupabase(SinId()).identificar("x") is None


class TestBuscarPorCorreo:
    def test_encuentra(self, autenticador):
        assert autenticador.por_email("luis@itc.edu.co") == Identidad(
            "uuid-luis", "luis@itc.edu.co"
        )

    def test_no_encuentra(self, autenticador):
        assert autenticador.por_email("nadie@itc.edu.co") is None

    def test_admite_que_list_users_devuelva_un_objeto_con_users(self):
        """La biblioteca ha devuelto ambas formas según la versión."""
        cliente = ClienteFalso(usuarios=[ANA], como_lista=False)
        assert AutenticadorSupabase(cliente).por_email("ana@itc.edu.co") is not None


class TestInvitar:
    def test_da_de_alta_a_quien_no_existe(self, autenticador, cliente):
        identidad = autenticador.invitar("nuevo@itc.edu.co")
        assert identidad.email == "nuevo@itc.edu.co"
        assert cliente.auth.admin.invitados == ["nuevo@itc.edu.co"]

    def test_a_quien_ya_existe_no_lo_invita_otra_vez(self, autenticador, cliente):
        identidad = autenticador.invitar("ana@itc.edu.co")
        assert identidad.usuario_id == "uuid-ana"
        assert cliente.auth.admin.invitados == []

    def test_si_supabase_no_devuelve_usuario_falla_claro(self):
        class AdminMudo:
            def list_users(self):
                return []

            def invite_user_by_email(self, email):
                return RespuestaFalsa(user=None)

        class Cliente:
            auth = type("A", (), {"admin": AdminMudo()})()

        with pytest.raises(RuntimeError, match="no devolvió un usuario"):
            AutenticadorSupabase(Cliente()).invitar("x@itc.edu.co")


@pytest.mark.supabase
class TestContraSupabaseReal:
    """El adaptador contra una instancia de verdad.

    Dos cosas aprendidas al correrlo la primera vez, ambas del proveedor y no
    del adaptador:

    - Supabase **rechaza los dominios inventados** como `.test`. Hay que usar
      uno con TLD real.
    - `invite_user_by_email` envía un correo y está limitado a unos cuatro por
      hora. Por eso aquí se invita **una sola vez** y el resto de casos se
      montan con `create_user`, que no manda nada.
    """

    CORREO = "adaptador-itc@example.com"

    @pytest.fixture
    def cliente(self):
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).parent.parent / "contratos"))
        from conftest import cliente_supabase

        return cliente_supabase("SUPABASE_KEY")

    @pytest.fixture
    def autenticador(self, cliente):
        return AutenticadorSupabase(cliente)

    @pytest.fixture
    def ya_registrado(self, cliente, autenticador):
        """Da de alta sin enviar correo, para no gastar la cuota de invitaciones."""
        existente = autenticador.por_email(self.CORREO)
        if existente is not None:
            return existente
        creado = cliente.auth.admin.create_user(
            {"email": self.CORREO, "password": "contrato-1234", "email_confirm": True}
        )
        return Identidad(str(creado.user.id), self.CORREO)

    def test_por_email_encuentra_a_quien_existe(self, autenticador, ya_registrado):
        encontrado = autenticador.por_email(self.CORREO)
        assert encontrado is not None
        assert encontrado.usuario_id == ya_registrado.usuario_id

    def test_por_email_no_inventa_a_quien_no_existe(self, autenticador):
        assert autenticador.por_email("nadie-de-nadie@example.com") is None

    def test_invitar_a_quien_ya_existe_no_envia_correo(
        self, autenticador, ya_registrado
    ):
        """El atajo que evita gastar la cuota: si ya está, se devuelve tal cual."""
        assert autenticador.invitar(self.CORREO).usuario_id == ya_registrado.usuario_id

    def test_un_token_invalido_no_identifica(self, autenticador):
        """Un JWT falsificado es alguien sin identificar, no un error."""
        assert autenticador.identificar("jwt.falsificado.xxx") is None

    def test_un_token_vacio_tampoco(self, autenticador):
        assert autenticador.identificar("") is None
