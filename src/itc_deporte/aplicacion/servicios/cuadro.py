"""El cuadro final, dibujado como un diagrama de torneo.

El cuadro se pinta de una sola vez como HTML (nodos cuadrados, conectores de
1 px en ángulo recto, el acento solo en lo que avanza) y la carga de resultados
vive aparte, en un desplegable: los formularios de Streamlit no pueden ir
dentro de un bloque de HTML.

Las reglas no cambian. Aquí se pide y se muestra; los permisos y la propagación
siguen en `aplicacion/` y `domain/`.
"""

from __future__ import annotations

import html

import streamlit as st

from ..aplicacion.errores import ErrorDeAplicacion
from ..aplicacion.permisos import Accion, Identidad
from ..domain.competicion import FaseDeGrupos
from ..domain.enfrentamiento import Marcador
from .vistas import _ejecutar


def _siglas(nombre: str) -> str:
    letras = "".join(c for c in nombre if c.isalnum())
    return (letras[:3] or "–").upper()


def _lado(participante, nombres, ganador, valor, es_bye: bool) -> str:
    if participante is None:
        texto = "–" if es_bye else "por definir"
        return (
            '<div class="bk-eq vacio"><span class="bk-id">–</span>'
            f'<span class="bk-n">{texto}</span><span class="bk-s"></span></div>'
        )
    nombre = nombres.get(participante, participante)
    gana = ganador is not None and participante == ganador
    return (
        f'<div class="bk-eq{" gana" if gana else ""}">'
        f'<span class="bk-id">{_siglas(nombre)}</span>'
        f'<span class="bk-n">{html.escape(nombre)}</span>'
        f'<span class="bk-s">{"" if valor is None else valor}</span></div>'
    )


def _partido(casilla, nombres) -> str:
    ganador = casilla.ganador()
    marcador = casilla.marcador
    local = marcador.local if marcador else None
    visitante = marcador.visitante if marcador else None
    nota = ""
    if casilla.es_bye:
        nota = "pasa sin jugar"
    elif casilla.espera_rival:
        nota = "esperando rival"
    return (
        f'<div class="bk-m{" ganado" if ganador else ""}">'
        + _lado(casilla.local, nombres, ganador, local, casilla.es_bye)
        + _lado(casilla.visitante, nombres, ganador, visitante, casilla.es_bye)
        + (f'<div class="bk-nota">{nota}</div>' if nota else "")
        + "</div>"
    )


def _html_del_cuadro(bracket, nombres) -> str:
    """Una columna por ronda. Sin saltos de línea: Markdown cortaría el bloque."""
    ultima = bracket.total_rondas - 1
    columnas = []
    for numero, ronda in enumerate(bracket.rondas):
        etiqueta = html.escape(bracket.nombre_de(numero))
        if numero == ultima:
            cuerpo = (
                '<div class="bk-par fin"><div class="bk-slot">'
                f"{_partido(ronda[0], nombres)}</div></div>"
            )
        else:
            pares = []
            for i in range(0, len(ronda), 2):
                par = ronda[i : i + 2]
                avanza = all(c.ganador() is not None for c in par)
                slots = "".join(
                    f'<div class="bk-slot">{_partido(c, nombres)}</div>' for c in par
                )
                pares.append(f'<div class="bk-par{" avanza" if avanza else ""}">{slots}</div>')
            cuerpo = "".join(pares)
        columnas.append(
            f'<div class="bk-col"><div class="bk-tag">{etiqueta}</div>'
            f'<div class="bk-body">{cuerpo}</div></div>'
        )
    return f'<div class="bk">{"".join(columnas)}</div>'


def cuadro_final(servicios, competicion, fase, actor: Identidad) -> None:
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
        nombre = html.escape(nombres.get(campeon, campeon))
        st.markdown(
            '<div class="bk-campeon"><span class="bk-tag">Campeón</span>'
            f'<span class="bk-nombre">{nombre}</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown(_html_del_cuadro(bracket, nombres), unsafe_allow_html=True)

    if puede_registrar:
        _carga_de_resultados(servicios, competicion, fase, bracket, nombres, actor)


def _carga_de_resultados(servicios, competicion, fase, bracket, nombres, actor) -> None:
    with st.expander("Cargar o corregir resultados"):
        hay = False
        for numero, ronda in enumerate(bracket.rondas):
            for casilla in ronda:
                if not casilla.listo:
                    continue
                hay = True
                local = nombres.get(casilla.local, casilla.local)
                visitante = nombres.get(casilla.visitante, casilla.visitante)
                marcador = casilla.marcador
                columnas = st.columns([7, 3])
                columnas[0].markdown(
                    f"`{bracket.nombre_de(numero)}` · **{local}** vs **{visitante}**"
                )
                with columnas[1].popover("Marcador", width="stretch"):
                    with st.form(f"cuadro-{casilla.ronda}-{casilla.posicion}"):
                        izquierda, derecha = st.columns(2)
                        g1 = izquierda.number_input(
                            "Local",
                            min_value=0,
                            value=marcador.local if marcador else 0,
                            step=1,
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
        if not hay:
            st.caption("Todavía no hay cruces con sus dos contendientes.")
