"""Aislamiento entre pruebas de interfaz.

`app.py` cachea los servicios con `@st.cache_resource`, que vive en el proceso
y no en la sesión. Sin limpiarlo, el sistema en memoria que arma una prueba
sobrevive a la siguiente: la que genera el cuadro deja el botón «Generar» fuera
de alcance para las demás.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def sistema_limpio():
    """Cada prueba arranca con su propio sistema en memoria."""
    streamlit = pytest.importorskip("streamlit")
    streamlit.cache_resource.clear()
    yield
    streamlit.cache_resource.clear()
