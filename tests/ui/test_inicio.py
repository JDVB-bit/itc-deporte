"""La portada: lo primero que ve quien abre la aplicación.

No llama a ningún servicio, así que estas pruebas comprueban tres cosas: que
se dibuja sin errores, que los botones navegan y que el tema cambia.
"""

from __future__ import annotations

import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest


def _portada():
    return AppTest.from_file("app.py", default_timeout=60).run()


def _texto(app) -> str:
    return " ".join(m.value for m in app.markdown)


def _boton(botones, texto):
    return next(b for b in botones if texto in b.label)


class TestLaPortada:
    def test_es_lo_primero_que_se_ve(self):
        app = _portada()
        assert not app.exception
        assert app.session_state["vista"] == "inicio"

    def test_no_muestra_todavia_la_competicion(self):
        assert not _portada().tabs

    def test_ITC_Deportes_encabeza_la_pagina(self):
        assert "ITC Deportes" in _texto(_portada())

    @pytest.mark.parametrize(
        "deporte", ["Microfútbol", "Baloncesto", "Voleyball", "Balonmano"]
    )
    def test_lista_los_deportes_de_la_escuela(self, deporte):
        assert deporte in _texto(_portada())

    def test_la_lista_de_competiciones_no_aparece_aqui(self):
        assert not _portada().sidebar.radio


class TestNavegacion:
    def test_el_boton_lleva_a_los_intercursos(self):
        app = _boton(_portada().main.button, "Entrar a los Intercursos").click().run()
        assert not app.exception
        assert app.session_state["vista"] == "intercursos"
        assert "📊 Tabla" in [p.label for p in app.tabs]

    def test_el_logo_de_la_barra_lateral_vuelve_a_la_portada(self):
        app = _boton(_portada().main.button, "Entrar a los Intercursos").click().run()
        app = _boton(app.sidebar.button, "ITC DEPORTES").click().run()
        assert not app.exception
        assert app.session_state["vista"] == "inicio"
        assert not app.tabs

    def test_el_logo_funciona_tambien_desde_la_portada(self):
        app = _boton(_portada().sidebar.button, "ITC DEPORTES").click().run()
        assert not app.exception
        assert app.session_state["vista"] == "inicio"

    def test_la_sesion_se_conserva_al_ir_y_volver(self):
        app = _portada()
        app = _boton(app.sidebar.button, "Administrador").click().run()
        app = _boton(app.main.button, "Entrar a los Intercursos").click().run()
        assert "⚙️ Administrar" in [p.label for p in app.tabs]
        app = _boton(app.sidebar.button, "ITC DEPORTES").click().run()
        app = _boton(app.main.button, "Entrar a los Intercursos").click().run()
        assert "⚙️ Administrar" in [p.label for p in app.tabs]


class TestElTema:
    def test_se_puede_cambiar_desde_la_portada(self):
        app = _portada()
        assert app.session_state["tema"] == "oscuro"
        app = _boton(app.main.button, "Tema").click().run()
        assert not app.exception
        assert app.session_state["tema"] == "verde"

    def test_se_puede_volver_al_primero(self):
        app = _boton(_portada().main.button, "Tema").click().run()
        app = _boton(app.main.button, "Tema").click().run()
        assert app.session_state["tema"] == "oscuro"
