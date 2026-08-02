"""Las vistas. Piden, no deciden.

Cada acción es una llamada a un servicio. Los permisos no se comprueban aquí:
se comprueban en `aplicacion/`, y aquí solo se atrapa `PermisoDenegado` para
mostrarlo. Esconder un botón es cortesía con el usuario, no seguridad —el
sistema anterior confundía las dos cosas.
"""

from __future__ import annotations

import datetime as dt
import unicodedata

import streamlit as st

from ..aplicacion.errores import ErrorDeAplicacion
from ..aplicacion.permisos import Accion, Identidad
from ..domain.calendario import Calendario
from ..domain.competicion import (
    Competicion,
    Deporte,
    EstadoCompeticion,
    FaseDeGrupos,
    FaseEliminatoria,
)
from ..domain.reglas.fixture import ConfigFixture
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


def _pintar_clasificacion(filas, nombres) -> None:
    tabla = pd.DataFrame(
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
        ]
    )
    st.table(tabla.style.hide(axis="index"))


def tabla_de_posiciones(servicios, competicion, fase) -> None:
    """Una tabla por grupo cuando los hay; si no, una sola de toda la fase.

    Con grupos, una única tabla mezcla equipos que no se han enfrentado y
    ordena por puntos a quienes juegan torneos distintos. `de_grupo` existía
    para esto y no lo llamaba nadie.
    """
    nombres = {
        p.id: p.nombre
        for p in servicios.inscripciones.inscritos(competicion.id)
    }
    grupos = getattr(fase, "grupos", ())

    if grupos:
        for grupo in grupos:
            tema.seccion(grupo.nombre or grupo.id)
            filas = servicios.clasificacion.de_grupo(
                competicion.id, fase.id, grupo.id
            )
            if filas:
                _pintar_clasificacion(filas, nombres)
            else:
                st.caption("Este grupo todavía no tiene participantes.")
        return

    filas = servicios.clasificacion.de_fase(competicion.id, fase.id)
    if not filas:
        st.info("Todavía no hay participantes inscritos.")
        return
    _pintar_clasificacion(filas, nombres)


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


def _retirar(servicios, inscritos, actor: Identidad) -> None:
    """Dar de baja a un inscrito.

    Se pedía confirmación explícita porque `retirar` borra al participante, y
    con él su rastro en los enfrentamientos ya sorteados.
    """
    with st.expander("Retirar un participante"):
        por_nombre = {p.nombre: p for p in inscritos}
        elegido = st.selectbox("Participante", list(por_nombre), key="retirar-quien")
        st.caption(
            "Retirarlo lo borra de la competición. Si ya se sorteó, sus "
            "partidos quedan sin uno de los lados."
        )
        if st.button("Retirar", key="retirar-confirmar"):
            if _ejecutar(
                servicios.inscripciones.retirar,
                actor,
                por_nombre[elegido].id,
                exito=f"{elegido} retirado.",
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
            if puede:
                _retirar(servicios, inscritos, actor)
        else:
            st.info(
                "Todavía no hay participantes inscritos."
                + ("" if puede else " Un administrador o registrador puede añadirlos.")
            )


# ── Administración ──────────────────────────────────────────────────────────


def _identificador(nombre: str, temporada: str) -> str:
    """Un id legible a partir del nombre. No hay pantalla que lo pida.

    Pedirle un identificador a quien crea una competición es trasladarle un
    detalle de la base. Se deriva, y si choca con otro el servicio lo dirá.
    """
    crudo = f"{nombre}-{temporada}".lower()
    limpio = "".join(c if c.isalnum() else "-" for c in unicodedata.normalize("NFKD", crudo)
                     .encode("ascii", "ignore").decode())
    return "-".join(p for p in limpio.split("-") if p) or "competicion"


def nueva_competicion(servicios, actor: Identidad) -> None:
    """Crear una competición: el camino que no existía.

    `ServicioDeCompeticiones.crear` llevaba desde su commit sin que nada lo
    invocara. En la demostración no se notaba porque las competiciones venían
    sembradas, así que sobre una base vacía —producción recién montada— un
    administrador se quedaba sin salida.

    Las fases se piden aquí porque `crear` recibe la competición entera y no
    hay operación para añadirlas después.
    """
    if not servicios.politica.puede(actor, Accion.CREAR_COMPETICION):
        return

    tema.seccion("Nueva competición")
    deportes = {c.deporte.id: c.deporte for c in servicios.competiciones.listar()}
    with st.form("nueva-competicion"):
        nombre = st.text_input("Nombre", placeholder="Intercursos — Microfútbol")
        temporada = st.text_input("Temporada", value=str(dt.date.today().year))

        if deportes:
            opciones = [*deportes.values(), None]
            deporte = st.selectbox(
                "Deporte",
                opciones,
                format_func=lambda d: f"{d.icono} {d.nombre}" if d else "➕ Otro…",
            )
        else:
            deporte = None
        if deporte is None:
            columnas = st.columns([3, 1])
            deporte_nombre = columnas[0].text_input("Deporte", placeholder="Microfútbol")
            deporte_icono = columnas[1].text_input("Icono", value="🏅", max_chars=2)

        st.caption("Fases. Una competición sin fases se crea igual, pero no se puede sortear.")
        hay_grupos = st.checkbox("Fase de grupos", value=True)
        jornadas = st.number_input(
            "Jornadas (0 = todas las que salgan)", min_value=0, max_value=99, value=0
        )
        hay_eliminatoria = st.checkbox("Fase eliminatoria", value=True)
        cupos = st.number_input("Cupos al cuadro", min_value=2, max_value=64, value=8)

        columnas = st.columns(2)
        dia = columnas[0].selectbox(
            "Día de juego",
            range(7),
            index=5,
            format_func=lambda d: (
                "lunes martes miércoles jueves viernes sábado domingo".split()[d]
            ),
        )
        hora = columnas[1].time_input("Hora", value=dt.time(15, 0))

        if not st.form_submit_button("Crear competición"):
            return
        if not nombre.strip():
            st.warning("La competición necesita un nombre.")
            return
        if deporte is None:
            if not deporte_nombre.strip():
                st.warning("Elige un deporte o escribe uno nuevo.")
                return
            deporte = Deporte(
                _identificador(deporte_nombre, ""), deporte_nombre.strip(), deporte_icono
            )

        id_ = _identificador(nombre, temporada)
        fases = []
        if hay_grupos:
            fases.append(
                FaseDeGrupos(
                    f"{id_}:0",
                    "Fase de grupos",
                    0,
                    config_fixture=ConfigFixture(
                        jornadas_forzadas=int(jornadas) or None
                    ),
                )
            )
        if hay_eliminatoria:
            fases.append(
                FaseEliminatoria(
                    f"{id_}:{len(fases)}",
                    "Eliminación directa",
                    len(fases),
                    fixture="eliminacion_directa",
                    cupos=int(cupos),
                )
            )
        _ejecutar(
            servicios.competiciones.crear,
            actor,
            Competicion(
                id=id_,
                nombre=nombre.strip(),
                deporte=deporte,
                temporada=temporada.strip() or None,
                fases=tuple(fases),
                calendario=Calendario(dia_de_la_semana=int(dia), hora=hora),
            ),
            exito=f"Competición {nombre.strip()!r} creada.",
        )


def estado_de_competicion(servicios, competicion, actor: Identidad) -> None:
    """Mover la competición entre Borrador, En curso y Finalizada.

    `cambiar_estado` era el segundo servicio sin quien lo llamara: una
    competición nacía en Borrador y ahí se quedaba para siempre.
    """
    if not servicios.politica.puede(
        actor, Accion.ADMINISTRAR_COMPETICION, competicion.id
    ):
        return

    tema.seccion("Estado")
    estados = list(EstadoCompeticion)
    elegido = st.selectbox(
        "Estado de la competición",
        estados,
        index=estados.index(competicion.estado),
        format_func=lambda e: e.value,
    )
    if elegido is competicion.estado:
        return
    if st.button(f"Pasar a {elegido.value}"):
        if _ejecutar(
            servicios.competiciones.cambiar_estado,
            actor,
            competicion.id,
            elegido,
            exito=f"La competición pasó a {elegido.value}.",
        ):
            st.rerun()


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
