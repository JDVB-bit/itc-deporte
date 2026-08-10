"""Apoyo de las pruebas de interfaz.

`AppTest` ejecuta `app.py` de verdad, y `app.py` se compone contra Supabase o no
arranca. La costura es `construir`: se sustituye por un sistema en memoria, y
todo lo demás —los servicios, los permisos, las vistas— corre tal cual.

Se sustituye `construir` y no los repositorios porque es el límite exacto entre
«de dónde salen los datos» y «qué hace la aplicación con ellos». Ejercitar
`ensamblar` de verdad es lo que evita que la composición que se prueba se separe
de la que se despliega.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def sistema_limpio():
    """Cada prueba arranca con su propio sistema.

    `app.py` cachea los servicios con `@st.cache_resource`, que vive en el
    proceso y no en la sesión. Sin limpiarlo, el sistema que arma una prueba
    sobrevive a la siguiente: la que genera el cuadro dejaba el botón «Generar»
    fuera de alcance para las demás.
    """
    streamlit = pytest.importorskip("streamlit")
    streamlit.cache_resource.clear()
    yield
    streamlit.cache_resource.clear()


@pytest.fixture
def montar(monkeypatch):
    """Deja `app.py` corriendo sobre el sistema que se le pase."""

    def _montar(sistema):
        import itc_deporte.ui as ui
        import itc_deporte.ui.composicion as composicion

        def construir_falso(*_args, **_kwargs):
            return sistema.servicios

        # `app.py` hace `from itc_deporte.ui import construir`, y `AppTest`
        # reejecuta el módulo en cada `run()`, así que reevalúa ese import y
        # recoge el sustituto. Se parchea también en `composicion` para que
        # nadie lo alcance por el otro nombre.
        monkeypatch.setattr(ui, "construir", construir_falso)
        monkeypatch.setattr(composicion, "construir", construir_falso)
        return sistema

    return _montar
