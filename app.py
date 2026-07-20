"""ITC Deportes — interfaz.

Streamlit como adaptador: monta los servicios, muestra lo que devuelven y les
pide lo que el usuario quiere hacer. No comprueba permisos, no calcula tablas y
no arma calendarios; de eso se encarga `itc_deporte.aplicacion`.

Sin credenciales de Supabase arranca sobre repositorios en memoria con datos de
muestra, lo que permite ver la aplicación funcionando sin tocar la red.
"""

from __future__ import annotations

import streamlit as st

from itc_deporte.aplicacion.permisos import ANONIMO, Accion, Identidad, Rol
from itc_deporte.domain.competicion import FaseDeGrupos, FaseEliminatoria
from itc_deporte.ui import construir, tema, vistas
from itc_deporte.ui.composicion import BaseSinPreparar

st.set_page_config(
    page_title="ITC Deportes",
    page_icon="static/logo_itc-deportes.png",
    layout="wide",
)

for clave, valor in [("tema", "oscuro"), ("usuario_id", None)]:
    st.session_state.setdefault(clave, valor)


@st.cache_resource
def servicios():
    """Una sola composición por proceso.

    Solo se cae a la demostración cuando de verdad no hay credenciales. Si las
    hay y algo falla, se propaga: mostrar datos de muestra con aspecto de reales
    sería peor que no arrancar.
    """
    try:
        secretos = st.secrets
    except Exception:
        secretos = None
    return construir(secretos)


try:
    SERVICIOS = servicios()
except BaseSinPreparar as error:
    st.error(str(error), icon="🗄️")
    st.stop()


def actor() -> Identidad:
    if not st.session_state.usuario_id:
        return ANONIMO
    identidad = SERVICIOS.autenticador.identificar(st.session_state.usuario_id)
    return identidad or ANONIMO


def barra_lateral(yo: Identidad):
    with st.sidebar:
        st.markdown("## ITC Deportes")
        if st.button(f"{tema.actual()['ico']} {tema.actual()['lbl']}"):
            tema.alternar()
            st.rerun()
        st.markdown("---")

        if SERVICIOS.es_demostracion:
            st.warning(
                "**Modo demostración.** Sin conexión a Supabase: los datos son "
                "de muestra y nada de lo que hagas se guarda.",
                icon="⚠️",
            )
            if yo is ANONIMO and st.button("Entrar como administrador"):
                st.session_state.usuario_id = "demo-admin"
                st.rerun()
            st.markdown("---")

        if yo is ANONIMO:
            st.markdown("**👤 Visitante**")
            st.caption("Puedes consultar tablas, calendarios y cuadros.")
            with st.expander("🔐 Iniciar sesión"):
                token = st.text_input("Token de sesión", type="password")
                if st.button("Entrar") and token:
                    if SERVICIOS.autenticador.identificar(token):
                        st.session_state.usuario_id = token
                        st.rerun()
                    else:
                        st.error("No se pudo identificar.")
        else:
            st.markdown(f"**★ {yo.email or yo.usuario_id}**")
            roles = SERVICIOS.politica.roles_de(yo)
            st.caption("Administrador" if Rol.ADMIN in roles else "Registrador")
            if st.button("Cerrar sesión"):
                st.session_state.usuario_id = None
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
    if administra:
        pestañas.append("⚙️ Administrar")
    abiertas = st.tabs(pestañas)

    with abiertas[0]:
        if grupos:
            vistas.tabla_de_posiciones(SERVICIOS, competicion, grupos)
    with abiertas[1]:
        if grupos:
            vistas.calendario(SERVICIOS, competicion, grupos, yo)
    with abiertas[2]:
        if eliminatoria:
            vistas.cuadro_final(SERVICIOS, competicion, eliminatoria, yo)
        else:
            st.info("Esta competición no tiene fase eliminatoria.")
    with abiertas[3]:
        vistas.participantes(SERVICIOS, competicion, yo)

    if administra:
        with abiertas[4]:
            if grupos:
                vistas.sorteo(SERVICIOS, competicion, grupos, yo)
            vistas.panel_de_registradores(SERVICIOS, competicion, yo)


main()
