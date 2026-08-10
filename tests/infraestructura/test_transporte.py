"""El transporte que reintenta.

Existe por un `httpx.ReadError: [WinError 10035]` que tumbó la aplicación entera
en mitad de una sesión, registrando resultados.

La causa: una conexión reutilizada del pool que ya no servía. Streamlit corta un
rerun en cuanto empieza el siguiente, y si el corte pilla una petición a medias,
esa conexión queda inservible dentro del pool; la siguiente llamada la saca y
revienta al leer.

Lo que hacía que se viera en pantalla es que nadie reintentaba. `postgrest` trae
un `send_with_retry`, pero solo mira **respuestas** 503 y 520 de Cloudflare: un
fallo de transporte no llega a producir respuesta, así que se escapaba entero.
"""

from __future__ import annotations

import httpx
import pytest

from itc_deporte.infraestructura.supabase.transporte import (
    REINTENTOS,
    TransporteQueReintenta,
    cliente_http,
)

PETICION = httpx.Request("GET", "https://proyecto.supabase.co/rest/v1/competiciones")


class TransporteDeMentira(TransporteQueReintenta):
    """Falla las `fallos` primeras veces y luego responde."""

    def __init__(self, fallos: int, error=None) -> None:
        super().__init__(dormir=lambda _: None)
        self.fallos = fallos
        self.intentos = 0
        self._error = error or httpx.ReadError("WinError 10035")

    def handle_request(self, request):
        return super().handle_request(request)

    def _enviar(self, request):
        self.intentos += 1
        if self.intentos <= self.fallos:
            raise self._error
        return httpx.Response(200, json=[])


@pytest.fixture
def transporte(monkeypatch):
    """Sustituye el envío real, que es lo único que toca la red."""

    def crear(fallos: int, error=None):
        doble = TransporteDeMentira(fallos, error)
        monkeypatch.setattr(
            httpx.HTTPTransport, "handle_request", lambda self, req: doble._enviar(req)
        )
        return doble

    return crear


class TestReintentaLosFallosDeTransporte:
    def test_una_conexion_muerta_no_se_nota(self, transporte):
        doble = transporte(fallos=1)
        assert doble.handle_request(PETICION).status_code == 200
        assert doble.intentos == 2

    def test_dos_seguidas_tampoco(self, transporte):
        doble = transporte(fallos=2)
        assert doble.handle_request(PETICION).status_code == 200

    def test_si_la_red_esta_caida_de_verdad_se_rinde(self, transporte):
        """Reintentar sin fin dejaría a quien mira esperando para nada."""
        doble = transporte(fallos=99)
        with pytest.raises(httpx.TransportError):
            doble.handle_request(PETICION)
        assert doble.intentos == REINTENTOS + 1

    def test_lo_que_va_bien_no_se_repite(self, transporte):
        doble = transporte(fallos=0)
        doble.handle_request(PETICION)
        assert doble.intentos == 1

    def test_un_error_de_lectura_es_de_transporte(self):
        """La regresión concreta: `ReadError` hereda de `TransportError`, que
        es lo que hace que este reintento lo cubra."""
        assert isinstance(httpx.ReadError("x"), httpx.TransportError)

    def test_no_reintenta_lo_que_no_es_de_red(self, monkeypatch):
        """Un fallo de programación tiene que salir a la primera, no tres
        veces y más lento."""
        veces = []

        def explotar(self, request):
            veces.append(1)
            raise ValueError("esto no es la red")

        monkeypatch.setattr(httpx.HTTPTransport, "handle_request", explotar)
        with pytest.raises(ValueError):
            TransporteQueReintenta(dormir=lambda _: None).handle_request(PETICION)
        assert len(veces) == 1


class TestElClienteQueSeLePasaASupabase:
    def test_lleva_el_transporte_que_reintenta(self):
        assert isinstance(cliente_http()._transport, TransporteQueReintenta)

    def test_no_reutiliza_conexiones_dormidas_mucho_rato(self):
        """Una conexión parada minutos tiene muchas papeletas de estar cerrada
        del otro lado, y abrir una nueva cuesta menos que un error en pantalla."""
        from itc_deporte.infraestructura.supabase.transporte import SEGUNDOS_DE_REPOSO

        assert SEGUNDOS_DE_REPOSO <= 30

    def test_supabase_lo_acepta_y_llega_hasta_postgrest(self):
        """Que el cliente se construya no basta: hay que ver que el transporte
        llega al sitio por el que salen las consultas."""
        supabase = pytest.importorskip("supabase")

        cliente = supabase.create_client(
            "https://proyecto.supabase.co",
            "k" * 200,
            supabase.ClientOptions(httpx_client=cliente_http()),
        )
        assert isinstance(cliente.postgrest.session._transport, TransporteQueReintenta)

    def test_y_el_jwt_se_le_puede_seguir_adjuntando(self):
        """La composición hace `postgrest.auth(token)` justo después."""
        supabase = pytest.importorskip("supabase")

        cliente = supabase.create_client(
            "https://proyecto.supabase.co",
            "k" * 200,
            supabase.ClientOptions(httpx_client=cliente_http()),
        )
        cliente.postgrest.auth("jwt-de-quien-mira")
