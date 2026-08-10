"""La interfaz, ejercitada sin navegador.

`AppTest` ejecuta `app.py` de verdad —el mismo script que sirve Streamlit— y
deja inspeccionar y accionar sus elementos. El sistema sobre el que corre lo
pone la fixture `montar`, con repositorios en memoria: sin red, y sin que la
aplicación tenga que traer datos de muestra dentro.

Lo que se comprueba aquí no es el aspecto, sino que la interfaz **pida lo que
debe**: que un visitante no vea el panel de administración, que iniciar sesión
lo haga aparecer, y que las acciones lleguen a los servicios.
"""

from __future__ import annotations

import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest

import sistema as muestra


@pytest.fixture
def liga(montar):
    """Dos competiciones, una sorteada y a medio jugar."""
    return montar(muestra.con_liga_en_marcha())


def abrir(como=None):
    """Abre la aplicación; con `como`, entra con ese correo."""
    app = AppTest.from_file("app.py", default_timeout=60).run()
    if como is None:
        return app
    app.sidebar.text_input[0].set_value(como.email)
    app.sidebar.text_input[1].set_value("da-igual")
    return next(b for b in app.sidebar.button if "Entrar" in b.label).click().run()


def etiquetas(pestañas) -> list[str]:
    return [p.label for p in pestañas]


def _generar_cuadro():
    """Entra como admin, genera el cuadro y devuelve lo que quedó pintado.

    Recoge markdown y captions: las etiquetas del cuadro usan las dos.
    """
    app = abrir(como=muestra.ADMIN)
    generar = next(b for b in app.button if "Generar cuadro" in b.label)
    app = generar.click().run()
    return " ".join(
        elemento.value for elemento in list(app.markdown) + list(app.caption)
    )


class TestArranque:
    def test_la_aplicacion_no_revienta(self, liga):
        assert not abrir().exception

    def test_ofrece_las_competiciones(self, liga):
        assert len(abrir().sidebar.radio[0].options) == 2

    def test_no_avisa_de_ninguna_demostracion(self, liga):
        """Ya no la hay: los datos que se ven son los que hay en la base."""
        assert not any("demostración" in w.value for w in abrir().sidebar.warning)


class TestSinCredencialesNoArranca:
    """Antes esto caía en una demostración. Parecía amable y era lo contrario:
    un despliegue al que se le olvidara un secreto no fallaba, arrancaba con
    competiciones inventadas y un botón de administrador sin contraseña."""

    def _sin_nada(self, monkeypatch):
        for clave in ("SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_ANON_KEY"):
            monkeypatch.delenv(clave, raising=False)

    def test_falta_de_credenciales_es_un_fallo(self, monkeypatch):
        from itc_deporte.ui.composicion import FaltanCredenciales, construir

        self._sin_nada(monkeypatch)
        with pytest.raises(FaltanCredenciales):
            construir(None)

    def test_el_mensaje_dice_que_secretos_hacen_falta(self, monkeypatch):
        from itc_deporte.ui.composicion import FaltanCredenciales, construir

        self._sin_nada(monkeypatch)
        with pytest.raises(FaltanCredenciales, match="SUPABASE_ANON_KEY"):
            construir(None)

    def test_la_pagina_lo_explica_en_vez_de_reventar(self, monkeypatch):
        """`app.py` atrapa `SistemaSinPreparar` y para con un mensaje."""
        self._sin_nada(monkeypatch)
        app = AppTest.from_file("app.py", default_timeout=60).run()
        assert not app.exception
        assert any("SUPABASE" in e.value for e in app.error)

    def test_y_no_ofrece_ninguna_manera_de_entrar(self, monkeypatch):
        self._sin_nada(monkeypatch)
        app = AppTest.from_file("app.py", default_timeout=60).run()
        assert not app.button


class TestNoSeDisfrazaDeProduccion:
    """Un fallo visible es mejor que datos inventados con aspecto de reales."""

    def _credenciales_que_no_sirven(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", "https://no-existe.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "x" * 200)
        monkeypatch.setenv("SUPABASE_ANON_KEY", "y" * 200)

    def test_con_credenciales_que_no_sirven_falla_en_vez_de_fingir(self, monkeypatch):
        """El defecto que tenía: un `except Exception` alrededor de la
        composición hacía que un Supabase caído se presentara como una
        demostración, y el usuario veía competiciones inventadas."""
        from itc_deporte.ui.composicion import BaseSinPreparar, construir

        self._credenciales_que_no_sirven(monkeypatch)
        with pytest.raises(BaseSinPreparar):
            construir(None)

    def test_el_mensaje_dice_que_falta_aplicar_el_esquema(self, monkeypatch):
        from itc_deporte.ui.composicion import BaseSinPreparar, construir

        self._credenciales_que_no_sirven(monkeypatch)
        with pytest.raises(BaseSinPreparar, match="PASO_2.sql"):
            construir(None)


class TestLoQueVeUnVisitante:
    def test_puede_consultar_sin_identificarse(self, liga):
        app = abrir()
        assert "📊 Tabla" in etiquetas(app.tabs)
        assert "🏆 Cuadro final" in etiquetas(app.tabs)

    def test_no_ve_el_panel_de_administracion(self, liga):
        """La pestaña no está porque no puede administrar, no al revés."""
        assert "⚙️ Administrar" not in etiquetas(abrir().tabs)

    def test_ni_la_de_crear_competiciones(self, liga):
        assert "➕ Nueva competición" not in etiquetas(abrir().tabs)

    def test_la_tabla_de_posiciones_se_muestra(self, liga):
        assert abrir().dataframe, "no se pintó ninguna tabla"

    def test_el_cuadro_sin_generar_lo_dice(self, liga):
        assert any("no se ha generado" in i.value for i in abrir().info)


class TestAcceso:
    def test_entrar_identifica_al_administrador(self, liga):
        app = abrir(como=muestra.ADMIN)
        assert any("admin@itc.edu.co" in m.value for m in app.sidebar.markdown)

    def test_y_entonces_aparece_la_administracion(self, liga):
        assert "⚙️ Administrar" in etiquetas(abrir(como=muestra.ADMIN).tabs)

    def test_salir_devuelve_al_modo_visitante(self, liga):
        app = abrir(como=muestra.ADMIN)
        salir = next(b for b in app.sidebar.button if "Cerrar" in b.label)
        app = salir.click().run()
        assert "⚙️ Administrar" not in etiquetas(app.tabs)

    def test_un_correo_desconocido_lo_dice(self, liga):
        app = abrir()
        app.sidebar.text_input[0].set_value("nadie@itc.edu.co")
        app = next(b for b in app.sidebar.button if "Entrar" in b.label).click().run()
        assert any("incorrect" in e.value.lower() for e in app.error)

    def test_el_formulario_pide_correo_y_contrasena(self, liga):
        """Un profesor entra con su correo, no con un identificador interno."""
        campos = [c.label for c in abrir().sidebar.text_input]
        assert "Correo" in campos
        assert "Contraseña" in campos


class TestNoHayRegistro:
    """El sistema no tiene alta propia a propósito: un visitante no necesita
    cuenta, y las de administrar o registrar se conceden. El primer admin se
    crea desde el panel de Supabase."""

    def test_no_se_ofrece_crear_una_cuenta(self, liga):
        etiquetas_botones = " ".join(b.label.lower() for b in abrir().button)
        for palabra in ("registrarse", "crear cuenta", "registro", "sign up"):
            assert palabra not in etiquetas_botones

    def test_ni_un_selector_para_elegir_papel(self, liga):
        """Lo había en la demostración: cualquiera pulsaba «Administrador»."""
        etiquetas_botones = [b.label for b in abrir().sidebar.button]
        assert not any("Administrador" in e for e in etiquetas_botones)


class TestElCuadroFinalEstaConectado:
    """Lo que el sistema anterior nunca llegó a mostrar."""

    def test_el_administrador_puede_generarlo(self, liga):
        app = abrir(como=muestra.ADMIN)
        generar = next((b for b in app.button if "Generar cuadro" in b.label), None)
        assert generar is not None, "no se ofrece generar el cuadro"
        assert not generar.click().run().exception

    def test_una_vez_generado_se_muestra(self, liga):
        """Las rondas se rotulan en minúsculas; el CSS las pone en mayúsculas."""
        pintado = _generar_cuadro().lower()
        assert "cuartos de final" in pintado
        assert "semifinal" in pintado
        assert "final" in pintado

    def test_nadie_aparece_en_la_final_sin_jugar(self, liga):
        """El fallo que se encontró al conectar el cuadro a la interfaz: los
        mejores sembrados llegaban a la final sin disputar su cuartos."""
        pintado = _generar_cuadro().lower()
        desde_la_final = pintado[pintado.rindex(">final<") :]
        assert "por definir" in desde_la_final

    def test_los_byes_de_la_primera_ronda_se_distinguen_de_la_espera(self, liga):
        pintado = _generar_cuadro()
        assert "pasa sin jugar" in pintado
        assert "esperando rival" in pintado


class TestLosPermisosGobiernanLaInterfaz:
    def test_un_visitante_no_puede_generar_el_cuadro(self, liga):
        assert not any("Generar cuadro" in b.label for b in abrir().button)

    def test_un_visitante_no_ve_el_formulario_de_inscripcion(self, liga):
        """Inscribir exige permiso; sin él ni siquiera se ofrece."""
        assert not any("Inscribir" in b.label for b in abrir().button)

    def test_el_registrador_carga_resultados_pero_no_administra(self, liga):
        app = abrir(como=muestra.PROFE)
        assert "⚙️ Administrar" not in etiquetas(app.tabs)
        assert any("Inscribir" in b.label for b in app.button)

    def test_el_registrador_no_puede_en_la_competicion_ajena(self, liga):
        """Su concesión alcanza a Microfútbol, no a Voleibol."""
        app = abrir(como=muestra.PROFE)
        app.sidebar.radio[0].set_value(app.sidebar.radio[0].options[1]).run()
        assert not any("Inscribir" in b.label for b in app.button)

    def test_quien_no_tiene_concesiones_solo_consulta(self, liga):
        app = abrir(como=muestra.MIRON)
        assert etiquetas(app.tabs) == [
            "📊 Tabla",
            "📅 Calendario",
            "🏆 Cuadro final",
            "👥 Equipos",
        ]


class TestInscribir:
    """Lo que el usuario reportó como «no deja inscribir nada»."""

    def _inscribir(self, app, nombre, division="999"):
        app.text_input[0].set_value(nombre)
        app.text_input[1].set_value(division)
        return next(b for b in app.button if b.label == "Inscribir").click().run()

    def test_el_equipo_queda_inscrito(self, liga):
        app = self._inscribir(abrir(como=muestra.ADMIN), "Equipo Nuevo")
        assert any("inscrito" in s.value for s in app.success)

    def test_y_aparece_en_la_lista_sin_tener_que_hacer_nada_mas(self, liga):
        """La tabla se dibuja antes que el formulario, así que sin reservarle
        el hueco mostraría la lista de antes de inscribir y parecería que la
        acción no hizo nada."""
        app = abrir(como=muestra.ADMIN)
        antes = len(app.dataframe[1].value)
        app = self._inscribir(app, "Equipo Nuevo")
        assert len(app.dataframe[1].value) == antes + 1

    def test_un_nombre_repetido_se_rechaza_con_su_motivo(self, liga):
        app = self._inscribir(abrir(como=muestra.ADMIN), "Los Tigres")
        assert any("Ya hay un participante" in w.value for w in app.warning)

    def test_sin_nombre_lo_dice_en_vez_de_callarse(self, liga):
        app = abrir(como=muestra.ADMIN)
        app = next(b for b in app.button if b.label == "Inscribir").click().run()
        assert any("Escribe el nombre" in w.value for w in app.warning)

    def test_el_registrador_tambien_puede_en_la_suya(self, liga):
        app = self._inscribir(abrir(como=muestra.PROFE), "De la Profe")
        assert any("inscrito" in s.value for s in app.success)
