"""ITC Deportes — interfaz.

Streamlit como adaptador: monta los servicios, muestra lo que devuelven y les
pide lo que el usuario quiere hacer. No comprueba permisos, no calcula tablas y
no arma calendarios; de eso se encarga `itc_deporte.aplicacion`.

Sin las credenciales de Supabase no arranca, y dice cuál falta.
"""

from __future__ import annotations

import streamlit as st

from itc_deporte.aplicacion.permisos import ANONIMO, Accion, Identidad, Rol
from itc_deporte.domain.competicion import FaseDeGrupos, FaseEliminatoria
from itc_deporte.ui import construir, tema, vistas
from itc_deporte.ui.composicion import SistemaSinPreparar

st.set_page_config(
    page_title="ITC Deportes",
    page_icon="static/logo_itc-deportes.png",
    layout="wide",
)

for clave, valor in [("tema", "oscuro"), ("token", None)]:
    st.session_state.setdefault(clave, valor)


@st.cache_resource(max_entries=16, ttl=3600, show_spinner=False)
def servicios(token: str | None):
    """Una composición por sesión, no una por proceso.

    El token forma parte de la clave a propósito: el cliente de datos lleva
    dentro el JWT de quien mira, así que una composición compartida haría que
    dos personas escribieran con los permisos de la que llegó primero. Ver
    `composicion._sobre_supabase`.

    Si algo falla, se propaga y la página lo dice: arrancar sobre otra cosa
    cuando falta un secreto o la base no responde sería mostrar competiciones
    inventadas con aspecto de reales, que es peor que no arrancar.
    """
    try:
        secretos = st.secrets
    except Exception:
        secretos = None
    return construir(secretos, token=token)


try:
    SERVICIOS = servicios(st.session_state.token)
except SistemaSinPreparar as error:
    st.error(str(error), icon="🗄️")
    st.stop()


def actor() -> Identidad:
    """Quién está mirando, según el token de sesión.

    Lo que se guarda es el token, no el id de usuario: es lo único que
    `identificar` acepta. Guardar el id hacía que Supabase no reconociera a
    nadie y todo el mundo navegara como visitante.
    """
    if not st.session_state.token:
        return ANONIMO
    identidad = SERVICIOS.autenticador.identificar(st.session_state.token)
    return identidad or ANONIMO


def barra_lateral(yo: Identidad):
    with st.sidebar:
        st.markdown("## ITC Deportes")
        if st.button(f"{tema.actual()['ico']} {tema.actual()['lbl']}"):
            tema.alternar()
            st.rerun()
        st.markdown("---")

        # No hay pantalla de registro, y es a propósito: un visitante no
        # necesita cuenta, y las de administrar o registrar se conceden. El
        # primer admin se crea desde el panel de Supabase (`docs/FASE_7.md`).
        if yo is ANONIMO:
            st.markdown("**👤 Visitante**")
            st.caption("Puedes consultar tablas, calendarios y cuadros.")
            with st.expander("🔐 Iniciar sesión"):
                with st.form("acceso"):
                    correo = st.text_input("Correo")
                    contrasena = st.text_input("Contraseña", type="password")
                    if st.form_submit_button("Entrar") and correo:
                        sesion = SERVICIOS.autenticador.iniciar_sesion(
                            correo, contrasena
                        )
                        if sesion:
                            st.session_state.token = sesion.token
                            st.rerun()
                        else:
                            st.error("Correo o contraseña incorrectos.")
        else:
            st.markdown(f"**★ {yo.email or yo.usuario_id}**")
            roles = SERVICIOS.politica.roles_de(yo)
            st.caption("Administrador" if Rol.ADMIN in roles else "Registrador")
            if st.button("Cerrar sesión"):
                st.session_state.token = None
                st.rerun()

        st.markdown("---")
        competiciones = SERVICIOS.competiciones.listar()
        if not competiciones:
            return None
        return st.radio(
            "Competición",
            competiciones,
            format_func=lambda c: f"{c.deporte.icono} {c.nombre}",
        )


def main() -> None:
    tema.aplicar()
    yo = actor()
    competicion = barra_lateral(yo)

    tema.hero("ITC DEPORTES", "Sistema de gestión deportiva · 2026")

    if competicion is None:
        st.info("Todavía no hay ninguna competición.")
        # El formulario va aquí y no solo en la pestaña de administrar: esa
        # pestaña vive dentro de una competición, así que sobre una base vacía
        # un administrador no tenía por dónde empezar.
        vistas.nueva_competicion(SERVICIOS, yo)
        return

    st.markdown(f"## {competicion.deporte.icono} {competicion.nombre}")
    grupos = next(
        (f for f in competicion.fases_ordenadas if isinstance(f, FaseDeGrupos)), None
    )
    eliminatoria = next(
        (f for f in competicion.fases_ordenadas if isinstance(f, FaseEliminatoria)),
        None,
    )

    pestañas = ["📊 Tabla", "📅 Calendario", "🏆 Cuadro final", "👥 Equipos"]
    administra = SERVICIOS.politica.puede(yo, Accion.SORTEAR, competicion.id)
    # Crear no depende de la competición abierta, así que va en su propia
    # pestaña y no dentro de Administrar: un registrador puede crear la suya y
    # no administra ninguna, de modo que ahí dentro no lo alcanzaba nunca.
    crea = SERVICIOS.politica.puede(yo, Accion.CREAR_COMPETICION)
    if administra:
        pestañas.append("⚙️ Administrar")
    if crea:
        pestañas.append("➕ Nueva competición")
    # Por nombre y no por índice: con dos pestañas opcionales, un índice fijo
    # apunta a otra cosa según quién esté mirando.
    abiertas = dict(zip(pestañas, st.tabs(pestañas)))

    with abiertas["📊 Tabla"]:
        if grupos:
            vistas.tabla_de_posiciones(SERVICIOS, competicion, grupos)
    with abiertas["📅 Calendario"]:
        if grupos:
            vistas.calendario(SERVICIOS, competicion, grupos, yo)
    with abiertas["🏆 Cuadro final"]:
        if eliminatoria:
            vistas.cuadro_final(SERVICIOS, competicion, eliminatoria, yo)
        else:
            st.info("Esta competición no tiene fase eliminatoria.")
    with abiertas["👥 Equipos"]:
        vistas.participantes(SERVICIOS, competicion, yo)

    if administra:
        with abiertas["⚙️ Administrar"]:
            if grupos:
                vistas.sorteo(SERVICIOS, competicion, grupos, yo)
            vistas.estado_de_competicion(SERVICIOS, competicion, yo)
            vistas.panel_de_registradores(SERVICIOS, competicion, yo)
    if crea:
        with abiertas["➕ Nueva competición"]:
            vistas.nueva_competicion(SERVICIOS, yo)


main()
