"""Editar y borrar el cuadro final desde la interfaz, y lo que el diseño promete."""

from __future__ import annotations

from pathlib import Path

import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest

import sistema as muestra

APP_PATH = str(Path(__file__).resolve().parents[2] / "app.py")


def abrir(como=None):
    app = AppTest.from_file(APP_PATH, default_timeout=60).run()
    if como is None:
        return app
    app.sidebar.text_input[0].set_value(como.email)
    app.sidebar.text_input[1].set_value("da-igual")
    return next(b for b in app.sidebar.button if "Entrar" in b.label).click().run()


def boton(app, texto):
    return next(b for b in app.button if texto in b.label)


def hay_boton(app, texto) -> bool:
    return any(texto in b.label for b in app.button)


def textos(app) -> str:
    return " ".join(e.value for e in list(app.markdown) + list(app.caption))


@pytest.fixture
def con_cuadro(montar):
    sistema = montar(muestra.con_liga_en_marcha())
    sistema.servicios.cuadro.generar(
        muestra.ADMIN, muestra.MICRO, f"{muestra.MICRO}:1", desde_fase=f"{muestra.MICRO}:0"
    )
    return sistema


def _cuadro(sistema):
    return sistema.servicios.cuadro.actual(muestra.MICRO, f"{muestra.MICRO}:1")


def _jugable(sistema):
    """Una casilla de la primera ronda con sus dos contendientes (el cuadro de 6
    tiene byes, y esos no se juegan)."""
    return next(c for c in _cuadro(sistema).rondas[0] if c.listo)


class TestSoloElAdminAdministraElCuadro:
    def test_el_admin_ve_el_panel(self, con_cuadro):
        app = abrir(como=muestra.ADMIN)
        assert any("Administrar el cuadro" in e.label for e in app.expander)

    @pytest.mark.parametrize("quien", [None, muestra.PROFE, muestra.MIRON], ids=["visitante", "registrador", "sin-permisos"])
    def test_los_demas_no(self, con_cuadro, quien):
        app = abrir(como=quien)
        assert not any("Administrar el cuadro" in e.label for e in app.expander)
        assert not hay_boton(app, "Eliminar cuadro")

    def test_el_registrador_si_carga_resultados(self, con_cuadro):
        app = abrir(como=muestra.PROFE)
        assert any("Cargar o corregir" in e.label for e in app.expander)


class TestEliminar:
    def test_no_se_puede_sin_confirmar(self, con_cuadro):
        app = abrir(como=muestra.ADMIN)
        assert boton(app, "Eliminar cuadro").disabled

    def test_confirmando_lo_borra(self, con_cuadro):
        app = abrir(como=muestra.ADMIN)
        app.checkbox(key="cuadro-seguro").check().run()
        app = boton(app, "Eliminar cuadro").click().run()
        assert not app.exception
        assert con_cuadro.enfrentamientos.de_fase(f"{muestra.MICRO}:1") == ()

    def test_y_vuelve_a_ofrecer_generarlo(self, con_cuadro):
        app = abrir(como=muestra.ADMIN)
        app.checkbox(key="cuadro-seguro").check().run()
        app = boton(app, "Eliminar cuadro").click().run()
        assert hay_boton(app, "Generar cuadro")
        assert any("no se ha generado" in i.value for i in app.info)


class TestIntercambiar:
    def test_cambia_a_los_dos_equipos_de_sitio(self, con_cuadro):
        def lugares():
            return [p for c in _cuadro(con_cuadro).rondas[0] for p in (c.local, c.visitante)]

        antes = lugares()
        uno, otro = [p for p in antes if p][:2]
        app = abrir(como=muestra.ADMIN)
        app.selectbox(key="cuadro-uno").set_value(uno).run()
        app.selectbox(key="cuadro-otro").set_value(otro).run()
        app = boton(app, "Intercambiar").click().run()
        assert not app.exception
        despues = lugares()
        assert despues.index(uno) == antes.index(otro)
        assert despues.index(otro) == antes.index(uno)
        assert sorted(p for p in despues if p) == sorted(p for p in antes if p)

    def test_con_resultados_lo_explica_en_vez_de_ofrecerlo(self, con_cuadro):
        from itc_deporte.domain.enfrentamiento import Marcador

        casilla = _jugable(con_cuadro)
        con_cuadro.servicios.cuadro.registrar(
            muestra.ADMIN, muestra.MICRO, f"{muestra.MICRO}:1",
            casilla.ronda, casilla.posicion, Marcador(2, 1),
        )
        app = abrir(como=muestra.ADMIN)
        assert not hay_boton(app, "Intercambiar")
        assert "Borra primero los resultados" in textos(app)


class TestBorrarResultado:
    def test_quita_el_resultado_y_lo_que_dependia(self, con_cuadro):
        from itc_deporte.domain.enfrentamiento import Marcador

        servicios = con_cuadro.servicios
        fase = f"{muestra.MICRO}:1"
        casilla = _jugable(con_cuadro)
        ganador = casilla.local
        servicios.cuadro.registrar(
            muestra.ADMIN, muestra.MICRO, fase, casilla.ronda, casilla.posicion, Marcador(2, 1)
        )
        assert any(ganador in (c.local, c.visitante) for c in _cuadro(con_cuadro).rondas[1])
        app = abrir(como=muestra.ADMIN)
        app = boton(app, "Borrar resultado").click().run()
        assert not app.exception
        despues = _cuadro(con_cuadro)
        assert despues.slot(casilla.ronda, casilla.posicion).marcador is None
        assert not any(ganador in (c.local, c.visitante) for c in despues.rondas[1])

    def test_sin_resultados_no_ofrece_borrar(self, con_cuadro):
        app = abrir(como=muestra.ADMIN)
        assert not hay_boton(app, "Borrar resultado")
        assert "Todavía no hay resultados" in textos(app)


class TestElDiseno:
    def test_la_tabla_muestra_el_curso_bajo_cada_equipo(self, montar):
        montar(muestra.con_liga_en_marcha())
        pintado = textos(abrir())
        assert "Curso 601" in pintado and "Los Tigres" in pintado

    def test_los_que_clasifican_se_marcan(self, montar):
        montar(muestra.con_liga_en_marcha())
        assert "Clasifican al cuadro final" in textos(abrir())

    def test_el_encabezado_lleva_la_rueda_de_imagenes(self, montar):
        montar(muestra.con_liga_en_marcha())
        pintado = textos(abrir())
        assert "itc-fondo" in pintado and "itc-rueda" in pintado

    def test_el_cuadro_dibujado_es_simetrico_con_la_final_al_centro(self, con_cuadro):
        pintado = textos(abrir())
        assert pintado.count('class="col iz"') == pintado.count('class="col de"') >= 1
        assert pintado.count('class="col cen"') == 1

    def test_la_final_lleva_el_vs(self, con_cuadro):
        assert '<div class="vs">VS</div>' in textos(abrir())

    def test_el_curso_tambien_sale_en_el_cuadro(self, con_cuadro):
        assert "<small>Curso" in textos(abrir())

    def test_el_nombre_de_un_equipo_no_inyecta_html(self, montar):
        sistema = montar(muestra.con_liga_en_marcha())
        sistema.servicios.inscripciones.inscribir(
            muestra.ADMIN, muestra.MICRO, "x", "<script>alert(1)</script>", "999"
        )
        assert "<script>" not in textos(abrir())

    def test_sin_imagenes_el_encabezado_sigue_en_pie(self, montar, monkeypatch):
        from itc_deporte.ui import tema

        montar(muestra.con_liga_en_marcha())
        monkeypatch.setattr(tema, "fondos", lambda *_a, **_k: ())
        app = abrir()
        assert not app.exception
        assert "itc-rueda" not in textos(app)

    def test_cambiar_tema_alterna_y_no_revienta(self, montar):
        montar(muestra.con_liga_en_marcha())
        app = abrir()
        antes = app.session_state.tema
        app = next(b for b in app.sidebar.button if b.label == "Cambiar tema").click().run()
        assert not app.exception
        assert app.session_state.tema != antes


class TestRediseñoDeLaInterfaz:
    """Lo que se pidió quitar, fijar y mejorar en el menú, los cuadros y el movimiento."""

    def _hero(self, app) -> str:
        return next(m.value for m in app.markdown if m.value.startswith('<div class="itc-hero">'))

    def test_el_encabezado_no_muestra_el_estado_de_la_competicion(self, montar):
        montar(muestra.con_liga_en_marcha())
        hero = self._hero(abrir())
        assert "itc-chip" in hero  # deporte y temporada siguen
        assert "Borrador" not in hero

    def test_ya_no_hay_pie(self, montar):
        montar(muestra.con_liga_en_marcha())
        pintado = textos(abrir())
        assert "itc-pie" not in pintado and "Establecimiento Público" not in pintado

    def test_la_rueda_sigue_y_ahora_marca_su_progreso(self, montar):
        montar(muestra.con_liga_en_marcha())
        hero = self._hero(abrir())
        assert "itc-rueda" in hero and "itc-prog" in hero and "itc-llena" in hero

    def test_una_barra_de_progreso_por_imagen(self, montar):
        from itc_deporte.ui import tema

        uris = ("data:image/jpeg;base64,AA", "data:image/jpeg;base64,BB", "data:image/jpeg;base64,CC")
        html = tema._rueda(uris)
        assert html.count("<i></i>") == 3 and html.count("<b></b>") == 3

    def test_la_barra_lateral_no_deja_cajas_huerfanas(self, montar):
        """Abrir un `<div>` en un markdown y cerrarlo en otro no envuelve nada:
        dejaba cuadros vacíos en el menú."""
        montar(muestra.con_liga_en_marcha())
        sueltos = [m.value.strip() for m in abrir().sidebar.markdown]
        assert '<div class="itc-side-card">' not in sueltos and "</div>" not in sueltos

    def test_el_menu_rotula_las_competiciones_sin_adornos(self, montar):
        montar(muestra.con_liga_en_marcha())
        assert "Competiciones" in " ".join(m.value for m in abrir().sidebar.markdown)

    def test_el_menu_sigue_listando_las_competiciones(self, montar):
        montar(muestra.con_liga_en_marcha())
        assert len(abrir().sidebar.radio[0].options) >= 1


class TestElCssDelRediseño:
    @pytest.fixture
    def css(self):
        from itc_deporte.ui import tema

        return tema._ESTILO + tema._ESCALONADO

    def test_la_barra_lateral_no_se_puede_redimensionar(self, css):
        assert 'stSidebarResizeHandle"]{display:none' in css

    def test_las_cajas_van_redondeadas(self, css):
        assert "--r:10px" in css and "--rg:16px" in css
        # Solo quedan rectas las pestañas, que son un subrayado y no una caja.
        rectos = [t for t in css.split("}") if "border-radius:0" in t]
        assert len(rectos) == 1 and 'data-baseweb="tab"' in rectos[0]

    def test_los_botones_responden_al_pulsarse(self, css):
        assert ":active" in css and "scale(.96)" in css

    def test_la_pestaña_activa_se_subraya_con_movimiento(self, css):
        assert "scaleX(1)" in css and "transform-origin:left" in css

    def test_los_avisos_entran_con_movimiento(self, css):
        assert "itc-aviso" in css

    def test_las_filas_y_las_rondas_entran_escalonadas(self, css):
        assert "tr:nth-child(5)" in css and ".col:nth-child(3)" in css

    def test_se_respeta_reducir_movimiento(self, css):
        assert "prefers-reduced-motion:reduce" in css and "animation:none!important" in css

    def test_no_queda_el_estilo_del_pie(self, css):
        assert "itc-pie" not in css
