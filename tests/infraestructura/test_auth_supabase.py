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


@dataclass
class SesionFalsa:
    access_token: str


@dataclass
class RespuestaDeAcceso:
    user: UsuarioFalso | None
    session: SesionFalsa | None


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
    """Imita a Supabase en lo que importa: `get_user` **solo** acepta el JWT.

    Que rechace cualquier otra cosa —un UUID, por ejemplo— no es un capricho
    del doble: es lo que hace el proveedor, y era justo lo que este doble no
    reproducía cuando el fallo del token pasó a producción.
    """

    def __init__(self, usuarios=(), como_lista=True, token_valido="jwt-bueno"):
        self.admin = AdminFalso(usuarios, como_lista)
        self._token_valido = token_valido

    def get_user(self, token):
        if token != self._token_valido:
            raise ValueError("token inválido")
        return RespuestaFalsa(user=self.admin.usuarios[0])

    def sign_in_with_password(self, credenciales):
        usuario = next(
            (u for u in self.admin.usuarios if u.email == credenciales["email"]), None
        )
        if usuario is None or credenciales["password"] != "correcta":
            raise ValueError("credenciales inválidas")
        return RespuestaDeAcceso(user=usuario, session=SesionFalsa(self._token_valido))


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


class TestIniciarSesion:
    def test_devuelve_identidad_y_token(self, autenticador):
        sesion = autenticador.iniciar_sesion("ana@itc.edu.co", "correcta")
        assert sesion.identidad == Identidad("uuid-ana", "ana@itc.edu.co")
        assert sesion.token == "jwt-bueno"

    def test_el_token_sirve_para_identificar(self, autenticador):
        """La ida y vuelta: es lo que la interfaz hace en cada recarga.

        Sin esta comprobación el adaptador podía devolver un token que
        `identificar` no aceptaba, que es exactamente lo que pasó: la interfaz
        guardaba el UUID, `get_user` lo rechazaba y el usuario quedaba anónimo.
        """
        sesion = autenticador.iniciar_sesion("ana@itc.edu.co", "correcta")
        assert autenticador.identificar(sesion.token) == sesion.identidad

    def test_el_id_de_usuario_no_vale_como_token(self, autenticador):
        """Lo que se guardaba antes, y por qué nadie llegaba a administrador."""
        sesion = autenticador.iniciar_sesion("ana@itc.edu.co", "correcta")
        assert autenticador.identificar(sesion.identidad.usuario_id) is None

    def test_credenciales_erroneas_no_revientan(self, autenticador):
        assert autenticador.iniciar_sesion("ana@itc.edu.co", "mala") is None

    def test_sin_sesion_en_la_respuesta_no_hay_acceso(self):
        """Un acceso sin token no es un acceso: no habría con qué volver."""

        class SinSesion:
            auth = type(
                "A",
                (),
                {
                    "sign_in_with_password": staticmethod(
                        lambda c: RespuestaDeAcceso(user=ANA, session=None)
                    )
                },
            )()

        assert AutenticadorSupabase(SinSesion()).iniciar_sesion("a@b.co", "x") is None


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
    def cliente(self, crear_cliente_supabase):
        return crear_cliente_supabase("SUPABASE_KEY")

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

    def test_la_ida_y_vuelta_completa(self, autenticador, ya_registrado):
        """Entrar y seguir siendo quien entró, contra Supabase de verdad.

        Este es el test que faltaba. Todo lo demás de este archivo corre contra
        un doble que yo escribí, así que solo comprueba lo que supuse. Esto
        comprueba lo que Supabase hace.
        """
        sesion = autenticador.iniciar_sesion(self.CORREO, "contrato-1234")
        assert sesion is not None
        assert sesion.identidad.usuario_id == ya_registrado.usuario_id
        assert autenticador.identificar(sesion.token) == sesion.identidad

    def test_el_uuid_no_sirve_como_token_contra_supabase(
        self, autenticador, ya_registrado
    ):
        """La forma exacta del fallo que tumbó el panel de administrador."""
        assert autenticador.identificar(ya_registrado.usuario_id) is None
