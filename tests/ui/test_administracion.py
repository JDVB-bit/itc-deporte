"""La administración de competiciones, sobre una base vacía.

Este archivo existe por un fallo concreto: `ServicioDeCompeticiones.crear` y
`cambiar_estado` estaban escritos, probados y sin que **nada** en la interfaz
los invocara. En producción, con la base recién montada, un administrador veía
"Todavía no hay ninguna competición" y no tenía por dónde seguir.

No lo detectó nadie porque el resto de las pruebas de interfaz corren sobre la
demostración, que siembra dos competiciones ya hechas: el camino de crear la
primera no se ejercitaba nunca. Por eso aquí se parte de una base vacía, que es
lo que de verdad se encuentra un despliegue nuevo.
"""

from __future__ import annotations

import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest

from itc_deporte.aplicacion.permisos import Concesion, Identidad, Rol
from itc_deporte.domain.competicion import EstadoCompeticion
from itc_deporte.infraestructura.autenticacion import (
    AutenticadorEnMemoria,
    ConcesionesEnMemoria,
)
from itc_deporte.infraestructura.memoria import (
    CompeticionesEnMemoria,
    DivisionesEnMemoria,
    EnfrentamientosEnMemoria,
    ParticipantesEnMemoria,
)

ADMIN = Identidad("admin-1", "admin@itc.edu.co")
MIRON = Identidad("miron-1", "miron@itc.edu.co")


@pytest.fixture
def base_vacia(monkeypatch):
    """Compone el sistema sin una sola competición, como un despliegue nuevo."""
    from itc_deporte.ui import composicion

    competiciones = CompeticionesEnMemoria()

    def _sin_datos():
        repos = (
            competiciones,
            ParticipantesEnMemoria(),
            EnfrentamientosEnMemoria(),
            ConcesionesEnMemoria([Concesion(ADMIN.usuario_id, Rol.ADMIN)]),
            DivisionesEnMemoria(),
        )
        return repos, AutenticadorEnMemoria([ADMIN, MIRON]), False

    monkeypatch.setattr(composicion, "_en_memoria", _sin_datos)
    return competiciones


def _abrir(como: Identidad | None = None):
    app = AppTest.from_file("app.py", default_timeout=60).run()
    if como is None:
        return app
    app.sidebar.text_input[0].set_value(como.email)
    app.sidebar.text_input[1].set_value("da-igual")
    return next(b for b in app.sidebar.button if "Entrar" in b.label).click().run()


def _rellenar_y_crear(app, nombre="Intercursos Baloncesto", deporte="Baloncesto"):
    app.text_input[0].set_value(nombre)
    app.text_input[1].set_value("2026")
    app.text_input[2].set_value(deporte)
    return next(b for b in app.button if "Crear competici" in b.label).click().run()


class TestCrearLaPrimeraCompeticion:
    def test_el_admin_tiene_por_donde_empezar(self, base_vacia):
        """El fallo exacto: sin esto la base vacía era un callejón sin salida."""
        app = _abrir(como=ADMIN)
        assert any("no hay ninguna competición" in i.value for i in app.info)
        assert any("Crear competici" in b.label for b in app.button)

    def test_crearla_la_deja_disponible(self, base_vacia):
        app = _rellenar_y_crear(_abrir(como=ADMIN))
        assert not app.exception
        assert base_vacia.listar(), "la competición no llegó al repositorio"
        creada = base_vacia.listar()[0]
        assert creada.nombre == "Intercursos Baloncesto"
        assert creada.deporte.nombre == "Baloncesto"

    def test_nace_en_borrador_con_sus_fases(self, base_vacia):
        _rellenar_y_crear(_abrir(como=ADMIN))
        creada = base_vacia.listar()[0]
        assert creada.estado is EstadoCompeticion.BORRADOR
        assert [f.nombre for f in creada.fases_ordenadas] == [
            "Fase de grupos",
            "Eliminación directa",
        ]

    def test_despues_de_crearla_se_puede_operar(self, base_vacia):
        app = _rellenar_y_crear(_abrir(como=ADMIN)).run()
        assert len(app.sidebar.radio[0].options) == 1
        assert "⚙️ Administrar" in [p.label for p in app.tabs]

    def test_sin_nombre_no_crea_nada(self, base_vacia):
        app = _rellenar_y_crear(_abrir(como=ADMIN), nombre="   ")
        assert not base_vacia.listar()
        assert any("necesita un nombre" in w.value for w in app.warning)

    def test_a_quien_no_es_admin_no_se_le_ofrece(self, base_vacia):
        app = _abrir(como=MIRON)
        assert not any("Crear competici" in b.label for b in app.button)

    def test_un_visitante_sin_identificar_no_rompe_la_pagina(self, base_vacia):
        """Base vacía y nadie identificado: lo que se encontró producción.

        Este camino preguntaba las concesiones de `ANONIMO`, cuyo id no es un
        UUID, y contra Supabase eso era un error de PostgREST en pantalla.
        """
        app = _abrir()
        assert not app.exception
        assert any("no hay ninguna competición" in i.value for i in app.info)
        assert not any("Crear competici" in b.label for b in app.button)


class TestEstadoDeLaCompeticion:
    def test_se_puede_ponerla_en_curso(self, base_vacia):
        app = _rellenar_y_crear(_abrir(como=ADMIN)).run()
        selector = next(
            s for s in app.selectbox if "Estado" in (s.label or "")
        )
        app = selector.set_value(EstadoCompeticion.EN_CURSO).run()
        app = next(b for b in app.button if "Pasar a" in b.label).click().run()
        assert not app.exception
        assert base_vacia.listar()[0].estado is EstadoCompeticion.EN_CURSO
