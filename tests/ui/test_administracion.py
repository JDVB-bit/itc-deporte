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
from itc_deporte.domain.enfrentamiento import Marcador
from itc_deporte.domain.reglas.catalogo import DEPORTES
from itc_deporte.infraestructura.autenticacion import (
    AutenticadorEnMemoria,
    ConcesionesEnMemoria,
)
from itc_deporte.infraestructura.memoria import (
    CompeticionesEnMemoria,
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


def _campo(app, etiqueta, tipo="text_input"):
    """Un widget por su etiqueta.

    Por etiqueta y no por posición: el formulario de crear competición cambia de
    campos según el deporte —el voleibol tiene cinco parámetros de puntuación y
    el fútbol tres—, así que un índice fijo apunta a otra cosa en cuanto se
    cambia de deporte.
    """
    return next(c for c in getattr(app, tipo) if c.label == etiqueta)


def _elegir_deporte(app, clave: str | None):
    """Selecciona un deporte del catálogo, o «➕ Otro…» con `None`.

    Va fuera del formulario, así que cambiarlo redibuja: de ahí el `.run()`.
    """
    from itc_deporte.ui.vistas import A_MEDIDA

    selector = _campo(app, "Deporte", "selectbox")
    return selector.set_value(DEPORTES[clave] if clave else A_MEDIDA).run()


def _rellenar_y_crear(app, nombre="Intercursos Baloncesto", deporte="baloncesto"):
    app = _elegir_deporte(app, deporte)
    _campo(app, "Nombre").set_value(nombre)
    _campo(app, "Temporada").set_value("2026")
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


class TestLasReglasVienenDelDeporte:
    """El fallo que motivó el bloque: la pantalla de crear no ofrecía elegir
    reglas, así que toda competición nacía con el 3/1/0 del fútbol aunque fuera
    de voleibol, y `PorSets` estaba escrito, probado y fuera de alcance."""

    def test_el_voleibol_nace_puntuando_por_sets(self, base_vacia):
        _rellenar_y_crear(_abrir(como=ADMIN), "Intercursos Voleibol", "voleyball")
        reglas = base_vacia.listar()[0].reglas
        # 3-2 es una victoria ajustada: 2 puntos, no 3. Con el 3/1/0 daría (3, 0).
        assert reglas.puntuacion.puntos(Marcador(3, 2)) == (2, 1)

    def test_el_microfutbol_sigue_con_el_clasico(self, base_vacia):
        _rellenar_y_crear(_abrir(como=ADMIN), "Intercursos Micro", "microfutbol")
        reglas = base_vacia.listar()[0].reglas
        assert reglas.puntuacion.puntos(Marcador(2, 1)) == (3, 0)
        assert reglas.puntuacion.puntos(Marcador(1, 1)) == (1, 1)

    def test_el_baloncesto_trae_su_dos_por_victoria(self, base_vacia):
        _rellenar_y_crear(_abrir(como=ADMIN))
        reglas = base_vacia.listar()[0].reglas
        assert reglas.puntuacion.puntos(Marcador(80, 70)) == (2, 0)

    def test_cambiar_de_deporte_trae_sus_campos_sin_enviar(self, base_vacia):
        """El selector va fuera del formulario justo para esto: dentro, elegir
        voleibol no mostraba sus reglas hasta después de intentar crear."""
        app = _elegir_deporte(_abrir(como=ADMIN), "voleyball")
        etiquetas = [n.label for n in app.number_input]
        assert "Sets del perdedor para considerarlo ajustado" in etiquetas
        assert "Puntos por empate" not in etiquetas, "el voleibol no admite empate"

    def test_los_puntos_se_pueden_ajustar_antes_de_crear(self, base_vacia):
        app = _elegir_deporte(_abrir(como=ADMIN), "microfutbol")
        _campo(app, "Puntos por victoria", "number_input").set_value(5)
        _campo(app, "Nombre").set_value("Intercursos Micro")
        app = next(b for b in app.button if "Crear competici" in b.label).click().run()
        assert not app.exception
        reglas = base_vacia.listar()[0].reglas
        assert reglas.puntuacion.puntos(Marcador(2, 1)) == (5, 0)

    def test_unos_puntos_incoherentes_se_avisan_en_vez_de_reventar(self, base_vacia):
        """Ganar no puede puntuar menos que empatar. Lo dice el dominio, y la
        vista lo traduce a un aviso en lugar de a una traza."""
        app = _elegir_deporte(_abrir(como=ADMIN), "microfutbol")
        _campo(app, "Puntos por victoria", "number_input").set_value(0)
        _campo(app, "Nombre").set_value("Imposible")
        app = next(b for b in app.button if "Crear competici" in b.label).click().run()
        assert not app.exception
        assert not base_vacia.listar()
        assert any("empatar" in w.value for w in app.warning)


class TestUnDeporteQueNoEstaEnElCatalogo:
    def test_se_puede_dar_de_alta_al_primer_intento(self, base_vacia):
        """El fallo que tenía: los campos del deporte a medida vivían dentro del
        formulario, donde cambiar el selector no redibuja. Solo aparecían al
        enviar, y en ese mismo momento nacían vacíos, así que el primer intento
        siempre se saldaba con «escribe un deporte»."""
        app = _elegir_deporte(_abrir(como=ADMIN), None)
        _campo(app, "Nombre del deporte").set_value("Balonmano")
        _campo(app, "Nombre").set_value("Intercursos Balonmano")
        app = next(b for b in app.button if "Crear competici" in b.label).click().run()
        assert not app.exception
        assert base_vacia.listar(), "no se creó al primer intento"
        assert base_vacia.listar()[0].deporte.nombre == "Balonmano"

    def test_puede_elegir_como_se_puntua(self, base_vacia):
        app = _elegir_deporte(_abrir(como=ADMIN), None)
        _campo(app, "Sistema de puntuación", "selectbox").set_value("por_sets")
        app = app.run()
        _campo(app, "Nombre del deporte").set_value("Bádminton")
        _campo(app, "Nombre").set_value("Intercursos Bádminton")
        app = next(b for b in app.button if "Crear competici" in b.label).click().run()
        assert not app.exception
        reglas = base_vacia.listar()[0].reglas
        assert reglas.puntuacion.puntos(Marcador(3, 2)) == (2, 1)

    def test_sin_nombre_de_deporte_lo_dice(self, base_vacia):
        app = _elegir_deporte(_abrir(como=ADMIN), None)
        _campo(app, "Nombre").set_value("Sin deporte")
        app = next(b for b in app.button if "Crear competici" in b.label).click().run()
        assert not base_vacia.listar()
        assert any("nombre del deporte" in w.value.lower() for w in app.warning)


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
