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


def abrir(*, papel: str | None = None):
    """Abre la app; con `papel` entra desde el selector de la demostración."""
    app = AppTest.from_file("app.py", default_timeout=60).run()
    if papel:
        app = _entrar(app, papel)
    return app


def _entrar(app, papel: str = "Administrador"):
    boton = next(b for b in app.sidebar.button if papel in b.label)
    return boton.click().run()


def etiquetas(pestañas) -> list[str]:
    return [p.label for p in pestañas]


def _generar_cuadro() -> str:
    """Entra como admin, genera el cuadro y devuelve lo que quedó pintado.

    Recoge markdown y captions: las etiquetas del cuadro usan las dos.
    """
    app = abrir(papel="Administrador")
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
        assert any("itc-tabla" in m.value for m in app.markdown), (
            "no se pintó ninguna tabla"
        )

    def test_el_cuadro_sin_generar_lo_dice(self):
        app = abrir()
        assert any("no se ha generado" in i.value for i in app.info)


class TestAcceso:
    def test_entrar_identifica_al_administrador(self):
        app = abrir(papel="Administrador")
        assert any("admin@itc.edu.co" in m.value for m in app.sidebar.markdown)

    def test_y_entonces_aparece_la_administracion(self):
        assert "⚙️ Administrar" in etiquetas(abrir(papel="Administrador").tabs)

    def test_salir_devuelve_al_modo_visitante(self):
        app = abrir(papel="Administrador")
        salir = next(b for b in app.sidebar.button if "Cerrar" in b.label)
        app = salir.click().run()
        assert "⚙️ Administrar" not in etiquetas(app.tabs)


class TestElCuadroFinalEstaConectado:
    """Lo que el sistema anterior nunca llegó a mostrar."""

    def test_el_administrador_puede_generarlo(self):
        app = abrir(papel="Administrador")
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


class TestAccesoConCorreo:
    """Un profesor entra con su correo, no con un identificador interno."""

    def test_el_formulario_pide_correo_y_contrasena(self):
        app = abrir()
        etiquetas_campos = [c.label for c in app.text_input]
        assert "Correo" in etiquetas_campos
        assert "Contraseña" in etiquetas_campos

    def test_un_correo_conocido_identifica(self):
        app = abrir()
        app.text_input[0].set_value("admin@itc.edu.co")
        app = next(b for b in app.button if b.label == "Entrar").click().run()
        assert any("admin@itc.edu.co" in m.value for m in app.sidebar.markdown)

    def test_un_correo_desconocido_lo_dice(self):
        app = abrir()
        app.text_input[0].set_value("nadie@itc.edu.co")
        app = next(b for b in app.button if b.label == "Entrar").click().run()
        assert any("incorrect" in e.value.lower() for e in app.error)


class TestSePuedeProbarCadaPapel:
    """El sistema no tiene registro a propósito —un visitante no necesita
    cuenta y las de administrar o registrar se conceden—, así que la
    demostración ofrece los tres papeles para poder probarlo."""

    def test_ofrece_los_tres(self):
        etiquetas_botones = [b.label for b in abrir().sidebar.button]
        for papel in ("Administrador", "Registrador", "Visitante"):
            assert any(papel in e for e in etiquetas_botones), papel

    def test_el_administrador_lo_puede_todo(self):
        app = abrir(papel="Administrador")
        assert "⚙️ Administrar" in etiquetas(app.tabs)

    def test_el_registrador_carga_resultados_pero_no_administra(self):
        app = abrir(papel="Registrador")
        assert "⚙️ Administrar" not in etiquetas(app.tabs)
        assert any("Inscribir" in b.label for b in app.button)

    def test_el_registrador_no_puede_en_la_competicion_ajena(self):
        """Su concesión alcanza a Microfútbol, no a Voleyball."""
        app = abrir(papel="Registrador")
        app.sidebar.radio[0].set_value(app.sidebar.radio[0].options[1]).run()
        assert not any("Inscribir" in b.label for b in app.button)


class TestInscribir:
    """Lo que el usuario reportó como «no deja inscribir nada»."""

    def _inscribir(self, app, nombre, division="999"):
        app.text_input[0].set_value(nombre)
        app.text_input[1].set_value(division)
        return next(b for b in app.button if b.label == "Inscribir").click().run()

    def test_el_equipo_queda_inscrito(self):
        app = self._inscribir(abrir(papel="Administrador"), "Equipo Nuevo")
        assert any("inscrito" in s.value for s in app.success)

    def test_y_aparece_en_la_lista_sin_tener_que_hacer_nada_mas(self):
        """La tabla se dibuja antes que el formulario, así que sin reservarle
        el hueco mostraría la lista de antes de inscribir y parecería que la
        acción no hizo nada."""
        app = abrir(papel="Administrador")
        antes = len(app.dataframe[1].value)
        app = self._inscribir(app, "Equipo Nuevo")
        assert len(app.dataframe[1].value) == antes + 1

    def test_un_nombre_repetido_se_rechaza_con_su_motivo(self):
        app = self._inscribir(abrir(papel="Administrador"), "Los Tigres")
        assert any("Ya hay un participante" in w.value for w in app.warning)

    def test_sin_nombre_lo_dice_en_vez_de_callarse(self):
        app = abrir(papel="Administrador")
        app = next(b for b in app.button if b.label == "Inscribir").click().run()
        assert any("Escribe el nombre" in w.value for w in app.warning)

    def test_el_registrador_tambien_puede_en_la_suya(self):
        app = self._inscribir(abrir(papel="Registrador"), "De la Profe")
        assert any("inscrito" in s.value for s in app.success)
