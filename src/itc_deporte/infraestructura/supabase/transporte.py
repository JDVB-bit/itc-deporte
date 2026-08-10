"""El transporte HTTP con el que se habla con Supabase.

Existe por un fallo concreto: `httpx.ReadError: [WinError 10035]` en mitad de
una sesión, con la página entera caída en una traza.

La causa es una conexión reutilizada del pool que ya no servía. Streamlit corta
un rerun en cuanto empieza el siguiente —cosa que pasa constantemente cuando
alguien va registrando resultados a buen ritmo—, y si el corte ocurre a media
petición esa conexión queda inservible dentro del pool. La siguiente llamada la
saca, escribe, intenta leer y revienta.

`postgrest` trae un `send_with_retry`, pero **solo reintenta respuestas** 503 y
520 de Cloudflare, y solo en GET. Un fallo de transporte no llega a producir
respuesta, así que se escapaba entero.

Va en el transporte y no en cada repositorio a propósito: así cubre también las
llamadas de Auth, y ningún sitio nuevo puede olvidarse de reintentar.
"""

from __future__ import annotations

import time

import httpx

#: Cuántas veces se repite una petición que ni siquiera llegó a tener respuesta.
#: Dos bastan: lo que se esquiva es una conexión muerta, y la siguiente se abre
#: limpia. Si fallan tres seguidas, lo que hay es una red caída y reintentar más
#: solo alarga la espera de quien mira la pantalla.
REINTENTOS = 2

#: Cuánto puede quedarse una conexión ociosa en el pool antes de descartarla.
#: Bajo a propósito: una conexión que lleva minutos parada tiene muchas
#: papeletas de que el otro extremo ya la haya cerrado, y abrir una nueva cuesta
#: mucho menos que un error en pantalla.
SEGUNDOS_DE_REPOSO = 15.0


class TransporteQueReintenta(httpx.HTTPTransport):
    """Repite la petición cuando falla el transporte, no la respuesta.

    Repetir es seguro con lo que este sistema envía: las lecturas son GET y
    **todas** las escrituras son idempotentes —los `upsert` llevan
    `on_conflict` y los `delete` van por filtro—, así que una petición que
    quizá llegó a ejecutarse deja la base igual si se repite.
    """

    def __init__(self, *args, dormir=time.sleep, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._dormir = dormir

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        for intento in range(REINTENTOS + 1):
            try:
                return super().handle_request(request)
            except httpx.TransportError:
                if intento == REINTENTOS:
                    raise
                self._dormir(0.2 * (intento + 1))
        raise AssertionError("inalcanzable")  # pragma: no cover


def cliente_http() -> httpx.Client:
    """El cliente HTTP que se le pasa a Supabase."""
    return httpx.Client(
        transport=TransporteQueReintenta(),
        limits=httpx.Limits(keepalive_expiry=SEGUNDOS_DE_REPOSO),
        timeout=httpx.Timeout(20.0),
    )
