"""Las vistas. Piden, no deciden.

Cada acción es una llamada a un servicio. Los permisos no se comprueban aquí:
se comprueban en `aplicacion/`, y aquí solo se atrapa `PermisoDenegado` para
mostrarlo. Esconder un botón es cortesía con el usuario, no seguridad —el
sistema anterior confundía las dos cosas.
"""

from __future__ import annotations

import datetime as dt

import streamlit as st

from ..aplicacion.errores import ErrorDeAplicacion
from ..aplicacion.permisos import Accion, Identidad
from ..domain.competicion import FaseDeGrupos, FaseEliminatoria
from ..domain.enfrentamiento import Marcador
from ..domain.errores import ErrorDeDominio
from ..domain.motor.bracket import nombre_de_ronda
from . import tema


def _ejecutar(accion, *args, exito: str = "Hecho.", **kwargs) -> bool:
    """Llama a un servicio y traduce sus errores a mensajes.

    Los tres tipos que puede lanzar el sistema tienen significados distintos y
    merecen mensajes distintos: sin permiso, operación improcedente, o dato
    incoherente.

    Quien llama **no debe** rehacer la página tras un acierto: Streamlit ya la
    redibuja al enviar un formulario o pulsar un botón, y un `st.rerun()`
    adicional borra este aviso en el mismo instante en que aparece, con lo que
    la acción parece no haber hecho nada.
    """
    try:
        accion(*args, **kwargs)
    except PermissionError as error:
        st.error(f"🔒 {error}")
        return False
    except ErrorDeAplicacion as error:
        st.warning(str(error))
        return False
    except ErrorDeDominio as error:
        st.warning(str(error))
        return False
    st.success(exito, icon="✅")
    return True


# ── Consulta ────────────────────────────────────────────────────────────────


def tabla_de_posiciones(servicios, competicion, fase) -> None:
    filas = servicios.clasificacion.de_fase(competicion.id, fase.id)
    if not filas:
        st.info("Todavía no hay participantes inscritos.")
        return

    nombres = {
        p.id: p.nombre
        for p in servicios.inscripciones.inscritos(competicion.id)
    }
    st.dataframe(
        [
            {
                "#": posicion,
                "Equipo": nombres.get(f.participante_id, f.participante_id),
                "PJ": f.jugados,
                "G": f.ganados,
                "E": f.empatados,
                "P": f.perdidos,
                "AF": f.a_favor,
                "EC": f.en_contra,
                "DIF": f.diferencia,
                "Pts": f.puntos,
            }
            for posicion, f in enumerate(filas, start=1)
        ],
        hide_index=True,
        width="stretch",
    )


def calendario(servicios, competicion, fase, actor: Identidad) -> None:
    partidos = servicios.resultados.de_fase(fase.id)
    if not partidos:
        st.info("Esta fase todavía no se ha sorteado.")
        return

    nombres = {
        p.id: p.nombre for p in servicios.inscripciones.inscritos(competicion.id)
    }
    puede = servicios.politica.puede(
        actor, Accion.REGISTRAR_RESULTADO, competicion.id
    )

    por_jornada: dict[int, list] = {}
    for partido in partidos:
        por_jornada.setdefault(partido.jornada or 0, []).append(partido)

    for jornada in sorted(por_jornada):
        fecha = next(
            (p.fecha for p in por_jornada[jornada] if p.fecha), None
        )
        etiqueta = f"Jornada {jornada}"
        if fecha:
            etiqueta += f" · {fecha.strftime('%d/%m/%Y %H:%M')}"
        with st.expander(etiqueta, expanded=jornada == min(por_jornada)):
            for partido in por_jornada[jornada]:
                _fila_de_partido(servicios, partido, nombres, puede, actor)


def _fila_de_partido(servicios, partido, nombres, puede_registrar, actor) -> None:
    local = nombres.get(partido.local, partido.local)
    visitante = nombres.get(partido.visitante, partido.visitante)
    marcador = partido.marcador

    columnas = st.columns([5, 2, 5, 3] if puede_registrar else [5, 2, 5])
    columnas[0].markdown(f"**{local}**")
    columnas[1].markdown(
        f'<div class="itc-marcador">{marcador.local} - {marcador.visitante}</div>'
        if marcador
        else '<div class="itc-vacia">vs</div>',
        unsafe_allow_html=True,
    )
    columnas[2].markdown(f"**{visitante}**")

    if not puede_registrar:
        return

    with columnas[3].popover("Marcador", width="stretch"):
        with st.form(f"res-{partido.id}"):
            izquierda, derecha = st.columns(2)
            g1 = izquierda.number_input(
                local, min_value=0, value=marcador.local if marcador else 0, step=1
            )
            g2 = derecha.number_input(
                visitante,
                min_value=0,
                value=marcador.visitante if marcador else 0,
                step=1,
            )
            if st.form_submit_button("Guardar", width="stretch"):
                if _ejecutar(
                    servicios.resultados.registrar,
                    actor,
                    partido.id,
                    Marcador(int(g1), int(g2)),
                    exito="Resultado registrado.",
                ):
                    st.rerun()


def cuadro_final(servicios, competicion, fase, actor: Identidad) -> None:
    """El cuadro que el sistema anterior nunca llegó a mostrar."""
    nombres = {
        p.id: p.nombre for p in servicios.inscripciones.inscritos(competicion.id)
    }
    puede_generar = servicios.politica.puede(actor, Accion.SORTEAR, competicion.id)
    puede_registrar = servicios.politica.puede(
        actor, Accion.REGISTRAR_RESULTADO, competicion.id
    )

    try:
        bracket = servicios.cuadro.actual(competicion.id, fase.id)
    except ErrorDeAplicacion:
        st.info("El cuadro final todavía no se ha generado.")
        if puede_generar:
            grupos = next(
                (f for f in competicion.fases_ordenadas if isinstance(f, FaseDeGrupos)),
                None,
            )
            if grupos and st.button("Generar cuadro con los clasificados"):
                if _ejecutar(
                    servicios.cuadro.generar,
                    actor,
                    competicion.id,
                    fase.id,
                    desde_fase=grupos.id,
                    exito="Cuadro generado.",
                ):
                    st.rerun()
        return

    campeon = bracket.campeon()
    if campeon:
        st.success(f"🏆 Campeón: **{nombres.get(campeon, campeon)}**")

    columnas = st.columns(bracket.total_rondas)
    for numero, ronda in enumerate(bracket.rondas):
        with columnas[numero]:
            tema.seccion(nombre_de_ronda(len(ronda)))
            for casilla in ronda:
                _casilla_del_cuadro(
                    servicios,
                    competicion,
                    fase,
                    casilla,
                    nombres,
                    puede_registrar,
                    actor,
                )


def _casilla_del_cuadro(
    servicios, competicion, fase, casilla, nombres, puede_registrar, actor
) -> None:
    ganador = casilla.ganador()

    def etiqueta(participante):
        if participante is None:
            return '<span class="itc-vacia">por definir</span>'
        nombre = nombres.get(participante, participante)
        return f"<b>{nombre}</b>" if participante == ganador else nombre

    marcador = casilla.marcador
    resultado = f"{marcador.local}–{marcador.visitante}" if marcador else ""
    clase = "itc-casilla ganador" if ganador else "itc-casilla"
    st.markdown(
        f'<div class="{clase}">{etiqueta(casilla.local)}<br>'
        f'{etiqueta(casilla.visitante)}'
        f'{f"<br><small>{resultado}</small>" if resultado else ""}</div>',
        unsafe_allow_html=True,
    )

    if casilla.es_bye:
        st.caption("pasa sin jugar")
        return
    if casilla.espera_rival:
        st.caption("esperando rival")
        return
    if not puede_registrar or not casilla.listo:
        return

    with st.popover("Marcador", width="stretch"):
        with st.form(f"cuadro-{casilla.ronda}-{casilla.posicion}"):
            izquierda, derecha = st.columns(2)
            g1 = izquierda.number_input(
                "Local", min_value=0, value=marcador.local if marcador else 0, step=1
            )
            g2 = derecha.number_input(
                "Visitante",
                min_value=0,
                value=marcador.visitante if marcador else 0,
                step=1,
            )
            if st.form_submit_button("Guardar", width="stretch"):
                if _ejecutar(
                    servicios.cuadro.registrar,
                    actor,
                    competicion.id,
                    fase.id,
                    casilla.ronda,
                    casilla.posicion,
                    Marcador(int(g1), int(g2)),
                    exito="Resultado registrado, cuadro propagado.",
                ):
                    st.rerun()


def participantes(servicios, competicion, actor: Identidad) -> None:
    """Lista e inscripción.

    La tabla se reserva con un hueco y se rellena **después** del formulario.
    Streamlit ejecuta el guion de arriba abajo: si se dibujara antes, mostraría
    la lista de antes de inscribir, y quien acabara de añadir un equipo no lo
    vería hasta la siguiente interacción.
    """
    puede = servicios.politica.puede(
        actor, Accion.INSCRIBIR_PARTICIPANTE, competicion.id
    )
    hueco_de_la_tabla = st.empty()

    if puede:
        with st.form("inscribir", clear_on_submit=True):
            tema.seccion("Inscribir participante")
            nombre = st.text_input("Nombre del equipo")
            division = st.text_input("División o curso", placeholder="601")
            enviado = st.form_submit_button("Inscribir")
        if enviado and nombre.strip():
            _ejecutar(
                servicios.inscripciones.inscribir,
                actor,
                competicion.id,
                f"{competicion.id}:{nombre.strip().lower().replace(' ', '-')}",
                nombre,
                division.strip() or None,
                exito=f"{nombre} inscrito.",
            )
        elif enviado:
            st.warning("Escribe el nombre del equipo.")

    inscritos = servicios.inscripciones.inscritos(competicion.id)
    with hueco_de_la_tabla.container():
        if inscritos:
            st.dataframe(
                [
                    {
                        "Equipo": p.nombre,
                        "División": p.division_id or "—",
                        "Integrantes": len(p.miembros),
                    }
                    for p in inscritos
                ],
                hide_index=True,
                width="stretch",
            )
        else:
            st.info(
                "Todavía no hay participantes inscritos."
                + ("" if puede else " Un administrador o registrador puede añadirlos.")
            )


# ── Administración ──────────────────────────────────────────────────────────


def sorteo(servicios, competicion, fase, actor: Identidad) -> None:
    if not servicios.politica.puede(actor, Accion.SORTEAR, competicion.id):
        return
    tema.seccion("Sorteo")
    ya_hay = bool(servicios.resultados.de_fase(fase.id))
    if ya_hay:
        st.caption("Volver a sortear descarta el calendario actual por completo.")
    desde = st.date_input("Primera jornada a partir de", value=dt.date.today())
    if st.button("Sortear" if not ya_hay else "Rehacer el sorteo"):
        if _ejecutar(
            servicios.sorteo.sortear,
            actor,
            competicion.id,
            fase.id,
            desde=desde,
            exito="Calendario generado.",
        ):
            st.rerun()


def panel_de_registradores(servicios, competicion, actor: Identidad) -> None:
    if not servicios.politica.puede(
        actor, Accion.GESTIONAR_REGISTRADORES, competicion.id
    ):
        return

    tema.seccion("Registradores")
    st.caption(
        "Un registrador puede inscribir participantes y cargar resultados en "
        "esta competición, y solo en esta."
    )
    concesiones = servicios.registradores.de_competicion(competicion.id)
    for concesion in concesiones:
        columnas = st.columns([6, 2])
        columnas[0].markdown(f"`{concesion.usuario_id}`")
        if columnas[1].button("Revocar", key=f"rev-{concesion.usuario_id}"):
            if _ejecutar(
                servicios.registradores.revocar,
                actor,
                competicion.id,
                concesion.usuario_id,
                exito="Permiso revocado.",
            ):
                st.rerun()
    if not concesiones:
        st.caption("Nadie más tiene permiso todavía.")

    with st.form("otorgar", clear_on_submit=True):
        correo = st.text_input("Correo de la persona")
        st.caption(
            "Si no tiene cuenta se le enviará una invitación. El proveedor "
            "limita cuántos correos se mandan por hora."
        )
        if st.form_submit_button("Conceder") and correo.strip():
            if _ejecutar(
                servicios.registradores.otorgar_por_email,
                actor,
                competicion.id,
                correo,
                exito=f"Permiso concedido a {correo}.",
            ):
                st.rerun()
