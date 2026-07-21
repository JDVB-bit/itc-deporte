"""Los dos temas de la aplicación.

Portado tal cual del sistema anterior: el aspecto no cambia con el refactor.
Lo que cambia es que ya no vive mezclado con la lógica.
"""

from __future__ import annotations

import streamlit as st

TEMAS = {
    "oscuro": dict(
        ac="#D4A017", achi="#FFD040", bg="#0A0A0A", bgc="#141414", bga="#101010",
        bgs="#1A1200", tx="#F5F0E8", tx2="#9A9080", tx3="#5A5550", sbg="#050505",
        grad="linear-gradient(135deg,#0A0A0A,#1A1200)", ico="🟢", lbl="Tema Verde",
    ),
    "verde": dict(
        ac="#4CAF28", achi="#7FD44A", bg="#0D1F0F", bgc="#122516", bga="#0F1E12",
        bgs="#0A1A08", tx="#E8F5E0", tx2="#8AB880", tx3="#507848", sbg="#071208",
        grad="linear-gradient(135deg,#071208,#0D2010)", ico="🌙", lbl="Tema Oscuro",
    ),
}


def actual() -> dict:
    return TEMAS[st.session_state.get("tema", "oscuro")]


def alternar() -> None:
    st.session_state.tema = "verde" if actual() is TEMAS["oscuro"] else "oscuro"


def aplicar() -> None:
    t = actual()
    st.markdown(
        f"""<style>
        @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap');
        .stApp {{ background:{t['bg']}; color:{t['tx']}; }}
        section[data-testid="stSidebar"] {{ background:{t['sbg']}; }}
        h1,h2,h3 {{ color:{t['ac']}; }}
        .itc-hero {{
            background:{t['grad']}; border-left:6px solid {t['ac']};
            padding:20px 24px; margin-bottom:18px; border-radius:0 12px 12px 0;
        }}
        .itc-titulo {{
            font-family:'Bebas Neue',Impact,sans-serif; font-size:2.6rem;
            color:{t['ac']}; letter-spacing:4px; line-height:1.1;
        }}
        .itc-sub {{ color:{t['tx2']}; font-size:0.85rem; margin-top:4px; }}
        .itc-seccion {{
            color:{t['ac']}; font-size:0.78rem; letter-spacing:2px;
            text-transform:uppercase; margin:18px 0 8px; font-weight:700;
        }}
        .itc-tarjeta {{
            background:{t['bgc']}; border-left:3px solid {t['tx3']};
            padding:10px 14px; margin-bottom:6px; border-radius:0 8px 8px 0;
        }}
        .itc-tarjeta.jugado {{ border-left-color:{t['ac']}; }}
        .itc-marcador {{
            font-family:'Bebas Neue',Impact,sans-serif; font-size:1.5rem;
            color:{t['achi']}; letter-spacing:2px;
        }}
        .itc-casilla {{
            background:{t['bgc']}; border:1px solid {t['tx3']}; border-radius:8px;
            padding:8px 12px; margin-bottom:8px; font-size:0.85rem;
        }}
        .itc-casilla.ganador {{ border-color:{t['ac']}; color:{t['achi']}; }}
        .itc-vacia {{ color:{t['tx3']}; font-style:italic; }}
        </style>""",
        unsafe_allow_html=True,
    )


def hero(titulo: str, subtitulo: str) -> None:
    st.markdown(
        f'<div class="itc-hero"><div class="itc-titulo">{titulo}</div>'
        f'<div class="itc-sub">{subtitulo}</div></div>',
        unsafe_allow_html=True,
    )


def seccion(texto: str) -> None:
    st.markdown(f'<div class="itc-seccion">{texto}</div>', unsafe_allow_html=True)
