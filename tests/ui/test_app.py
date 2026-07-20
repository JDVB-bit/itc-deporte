"""La interfaz, ejercitada sin navegador.

`AppTest` ejecuta `app.py` de verdad —el mismo script que sirve Streamlit— y
deja inspeccionar y accionar sus elementos. Como la composición cae en
repositorios de memoria cuando no hay credenciales, esto corre sin red.

Lo que se comprueba aquí no es el aspecto, sino que la interfaz **pida lo que
debe**: que un visitante no vea el panel de administración, que iniciar sesión
lo haga aparecer, y que las acciones lleguen a los servicios.
"""

from __future__ import annotations

import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest


def abrir(*, como_admin: bool = False):
    app = AppTest.from_file("app.py", default_timeout=60).run()
    if como_admin:
        _entrar(app)
    return app


def _entrar(app):
    boton = next(b for b in app.sidebar.button if "administrador" in b.label)
    return boton.click().run()


def etiquetas(pestañas) -> list[str]:
    return [p.label for p in pestañas]


def _generar_cuadro() -> str:
    """Entra como admin, genera el cuadro y devuelve lo que quedó pintado.

    Recoge markdown y captions: las etiquetas del cuadro usan las dos.
    """
    app = abrir(como_admin=True)
    generar = next(b for b in app.button if "Generar cuadro" in b.label)
    app = generar.click().run()
    return " ".join(
        elemento.value for elemento in list(app.markdown) + list(app.caption)
    )


class TestArranque:
    def test_la_aplicacion_no_revienta(self):
        assert not abrir().exception

    def test_sin_credenciales_avisa_de_que_es_una_demostracion(self):
        app = abrir()
        assert any("demostración" in w.value for w in app.sidebar.warning)

    def test_ofrece_las_competiciones_de_muestra(self):
        app = abrir()
        opciones = app.sidebar.radio[0].options
        assert len(opciones) == 2


class TestLoQueVeUnVisitante:
    def test_puede_consultar_sin_identificarse(self):
        app = abrir()
        assert "📊 Tabla" in etiquetas(app.tabs)
        assert "🏆 Cuadro final" in etiquetas(app.tabs)

    def test_no_ve_el_panel_de_administracion(self):
        """La pestaña no está porque no puede administrar, no al revés."""
        assert "⚙️ Administrar" not in etiquetas(abrir().tabs)

    def test_la_tabla_de_posiciones_se_muestra(self):
        app = abrir()
        assert app.dataframe, "no se pintó ninguna tabla"

    def test_el_cuadro_sin_generar_lo_dice(self):
        app = abrir()
        assert any("no se ha generado" in i.value for i in app.info)


class TestAcceso:
    def test_entrar_identifica_al_administrador(self):
        app = abrir(como_admin=True)
        assert any("demo@itc.edu.co" in m.value for m in app.sidebar.markdown)

    def test_y_entonces_aparece_la_administracion(self):
        assert "⚙️ Administrar" in etiquetas(abrir(como_admin=True).tabs)

    def test_salir_devuelve_al_modo_visitante(self):
        app = abrir(como_admin=True)
        salir = next(b for b in app.sidebar.button if "Cerrar" in b.label)
        app = salir.click().run()
        assert "⚙️ Administrar" not in etiquetas(app.tabs)


class TestElCuadroFinalEstaConectado:
    """Lo que el sistema anterior nunca llegó a mostrar."""

    def test_el_administrador_puede_generarlo(self):
        app = abrir(como_admin=True)
        generar = next(
            (b for b in app.button if "Generar cuadro" in b.label), None
        )
        assert generar is not None, "no se ofrece generar el cuadro"
        app = generar.click().run()
        assert not app.exception

    def test_una_vez_generado_se_muestra(self):
        """Las rondas se rotulan en minúsculas; el CSS las pone en mayúsculas."""
        pintado = _generar_cuadro().lower()
        assert "cuartos de final" in pintado
        assert "semifinal" in pintado
        assert "final" in pintado

    def test_nadie_aparece_en_la_final_sin_jugar(self):
        """El fallo que se encontró al conectar el cuadro a la interfaz: los
        mejores sembrados llegaban a la final sin disputar su cuartos."""
        pintado = _generar_cuadro().lower()
        desde_la_final = pintado[pintado.rindex(">final<") :]
        assert "por definir" in desde_la_final

    def test_los_byes_de_la_primera_ronda_se_distinguen_de_la_espera(self):
        pintado = _generar_cuadro()
        assert "pasa sin jugar" in pintado
        assert "esperando rival" in pintado


class TestLosPermisosGobiernanLaInterfaz:
    def test_un_visitante_no_puede_generar_el_cuadro(self):
        app = abrir()
        assert not any("Generar cuadro" in b.label for b in app.button)

    def test_un_visitante_no_ve_el_formulario_de_inscripcion(self):
        """Inscribir exige permiso; sin él ni siquiera se ofrece."""
        app = abrir()
        assert not any("Inscribir" in b.label for b in app.button)


class TestNoSeDisfrazaDeProduccion:
    """Un fallo visible es mejor que datos inventados con aspecto de reales."""

    def test_sin_credenciales_arranca_en_demostracion(self, monkeypatch):
        from itc_deporte.ui.composicion import construir

        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)
        assert construir(None).es_demostracion

    def test_con_credenciales_que_no_sirven_falla_en_vez_de_fingir(self, monkeypatch):
        """El defecto que tenía: un `except Exception` alrededor de la
        composición hacía que un Supabase caído se presentara como una
        demostración, y el usuario veía competiciones inventadas."""
        from itc_deporte.ui.composicion import BaseSinPreparar, construir

        monkeypatch.setenv("SUPABASE_URL", "https://no-existe.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "x" * 200)
        with pytest.raises(BaseSinPreparar):
            construir(None)

    def test_el_mensaje_dice_que_falta_aplicar_el_esquema(self, monkeypatch):
        from itc_deporte.ui.composicion import BaseSinPreparar, construir

        monkeypatch.setenv("SUPABASE_URL", "https://no-existe.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "x" * 200)
        with pytest.raises(BaseSinPreparar, match="PASO_2.sql"):
            construir(None)
