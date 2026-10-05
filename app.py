"""ITC Deportes — interfaz.

Streamlit como adaptador: monta los servicios, muestra lo que devuelven y les
pide lo que el usuario quiere hacer. No comprueba permisos, no calcula tablas y
no arma calendarios; de eso se encarga `itc_deporte.aplicacion`.

Sin las credenciales de Supabase no arranca, y dice cuál falta.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from itc_deporte.aplicacion.permisos import ANONIMO, Accion, Identidad, Rol
from itc_deporte.domain.competicion import FaseDeGrupos, FaseEliminatoria
from itc_deporte.ui import construir, tema, vistas
from itc_deporte.ui.composicion import ERRORES_DE_RED, SistemaSinPreparar

RAIZ = Path(__file__).resolve().parent

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


def _sin_conexion(error: Exception) -> None:
    """Lo dice y ofrece reintentar, en vez de dejar una traza en pantalla.

    El transporte ya reintenta los fallos de red por su cuenta, así que llegar
    aquí significa que la conexión está caída de verdad. Nada queda a medias:
    todas las escrituras del sistema son idempotentes, de modo que repetir la
    operación es inocuo aunque la anterior sí hubiera llegado.
    """
    st.error(
        "Se perdió la conexión con la base de datos.\n\n"
        f"Detalle: {error}",
        icon="🔌",
    )
    if st.button("Reintentar"):
        st.rerun()
    st.stop()


try:
    SERVICIOS = servicios(st.session_state.token)
except SistemaSinPreparar as error:
    st.error(str(error), icon="🗄️")
    st.stop()
except ERRORES_DE_RED as error:
    # `st.cache_resource` no guarda lo que lanza, así que reintentar vuelve a
    # componer de cero.
    _sin_conexion(error)


def actor() -> Identidad:
    """Quién está mirando, según el token de sesión.

    Lo que se guarda es el token, no el id de usuario: es lo único que
    `identificar` acepta. Guardar el id hacía que Supabase no reconociera a
    nadie y todo el mundo navegara como visitante.

    Se resuelve una vez por token y no en cada recarga. Streamlit reejecuta el
    guion entero ante cualquier interacción —abrir una pestaña, escribir en un
    campo—, y así cada una de ellas costaba una llamada de red a Supabase solo
    para volver a preguntar quién es el mismo de siempre.

    Recordarlo no alarga la sesión: el mismo JWT viaja al cliente de datos, y
    ahí Postgres lo valida en cada consulta. Uno caducado deja de servir para
    leer o escribir aunque esta caché siga recordando su nombre.
    """
    token = st.session_state.token
    if not token:
        return ANONIMO
    if st.session_state.get("identificado_con") != token:
        st.session_state.identidad = SERVICIOS.autenticador.identificar(token)
        st.session_state.identificado_con = token
    return st.session_state.identidad or ANONIMO


def _papel(yo: Identidad) -> str:
    """Cómo se le llama a quien entró.

    `roles_de` sin competición no ve las concesiones de registrador —son por
    competición—, así que el `else` de antes llamaba «Registrador» también a
    quien no tenía ninguna concesión.
    """
    if Rol.ADMIN in SERVICIOS.politica.roles_de(yo):
        return "Administrador"
    if SERVICIOS.politica.es_registrador_en_alguna(yo):
        return "Registrador"
    return "Sin permisos asignados"


def barra_lateral(yo: Identidad):
    with st.sidebar:
        logo = RAIZ / "static" / "logo_itc-deportes.png"
        if logo.exists():
            st.image(str(logo), width="stretch")
        else:
            st.markdown("### ITC DEPORTES")
        if st.button("Cambiar tema"):
            tema.alternar()
            st.rerun()

        st.markdown('<div class="itc-side-card">', unsafe_allow_html=True)
        if yo is ANONIMO:
            st.markdown(
                '<div class="itc-side-user">'
                '<div class="itc-side-avatar">V</div>'
                '<div><div class="itc-side-name">Visitante</div></div></div>',
                unsafe_allow_html=True,
            )
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
            etiqueta_rol = _papel(yo)
            st.markdown(
                '<div class="itc-side-user">'
                f'<div class="itc-side-avatar">{(yo.email or "?")[0].upper()}</div>'
                f'<div><div class="itc-side-name">{yo.email or yo.usuario_id}</div></div></div>',
                unsafe_allow_html=True,
            )
            st.caption(etiqueta_rol)
            if st.button("Cerrar sesión"):
                st.session_state.token = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="itc-side-card">', unsafe_allow_html=True)
        tema.seccion("🏆 Competiciones")
        competiciones = SERVICIOS.competiciones.listar()
        if not competiciones:
            st.markdown('</div>', unsafe_allow_html=True)
            return None
        seleccion = st.radio(
            "Competición",
            competiciones,
            format_func=lambda c: f"{c.deporte.icono} {c.nombre}",
            label_visibility="collapsed",
        )
        st.markdown('</div>', unsafe_allow_html=True)
        return seleccion


def main() -> None:
    tema.aplicar()
    yo = actor()
    competicion = barra_lateral(yo)

    chips = tuple(
        c
        for c in (
            competicion and f"{competicion.deporte.icono} {competicion.deporte.nombre}",
            competicion and competicion.temporada and f"Temporada {competicion.temporada}",
            competicion and competicion.estado.value,
        )
        if c
    )
    tema.hero(
        "ITC DEPORTES",
        "Sistema de gestión deportiva · 2026",
        chips,
        fondos=tema.fondos(RAIZ / "static"),
    )

    if competicion is None:
        st.info("Todavía no hay ninguna competición.")
        # El formulario va aquí y no solo en la pestaña de administrar: esa
        # pestaña vive dentro de una competición, así que sobre una base vacía
        # un administrador no tenía por dónde empezar.
        vistas.nueva_competicion(SERVICIOS, yo)
        tema.pie()
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
    tema.pie()


try:
    main()
except ERRORES_DE_RED as error:
    # Las escrituras las atrapa `vistas._ejecutar`, que puede decirlo junto al
    # botón que las pidió. Esto es para las **lecturas** —listar competiciones,
    # calcular la tabla—, que no tienen dónde caerse y se llevaban la página
    # entera por delante.
    _sin_conexion(error)
