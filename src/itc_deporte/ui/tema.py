"""Los dos temas de la aplicación — identidad ETITC.

Rediseño puramente visual: mismas claves del diccionario, misma firma de
funciones (`actual`, `alternar`, `aplicar`, `hero`, `seccion`) para que
`app.py` y `vistas.py` sigan llamándolas exactamente igual. Nada de lógica,
nada de rutas, nada de datos: solo CSS inyectado y el marcado de `hero()` /
`seccion()`.

Nota de implementación: `st.markdown` interpreta cualquier línea que empiece
con 4+ espacios como un bloque de código Markdown y la muestra como texto
plano en vez de dejar que el navegador la interprete como HTML/CSS. Como el
string va indentado dentro de la función, hay que quitarle esa sangría con
`textwrap.dedent()` antes de pasarlo — si no, el CSS entero aparece impreso
en la página en vez de aplicarse.
"""

from __future__ import annotations

import textwrap

import streamlit as st

# ── Paleta institucional ──────────────────────────────────────────────────
TEMAS = {
    "oscuro": dict(
        ac="#1E7A4C",
        achi="#2FA968",
        bg="#0B0F0D",
        bgc="#121815",
        bga="#0F1512",
        bgs="#0A0F0C",
        tx="#F4F6F4",
        tx2="#9AA79E",
        tx3="#4A554E",
        sbg="#080B09",
        dorado="#C9A227",
        grad="linear-gradient(135deg,#0B0F0D 0%,#0F241A 55%,#0B0F0D 100%)",
        hero_grad="linear-gradient(180deg, rgba(6,10,8,.55) 0%, rgba(6,10,8,.85) 65%, #0B0F0D 100%)",
        ico="☀️", lbl="Tema Claro",
    ),
    "verde": dict(
        ac="#1E7A4C",
        achi="#2FA968",
        bg="#F5F7F5",
        bgc="#FFFFFF",
        bga="#EEF3EF",
        bgs="#0E2A1C",
        tx="#141A17",
        tx2="#55625B",
        tx3="#C7D2CB",
        sbg="#0E2A1C",
        dorado="#B8912A",
        grad="linear-gradient(135deg,#FFFFFF 0%,#EAF3EC 100%)",
        hero_grad="linear-gradient(180deg, rgba(10,25,18,.45) 0%, rgba(10,25,18,.82) 65%, #F5F7F5 100%)",
        ico="🌙", lbl="Tema Oscuro",
    ),
}

HERO_IMG = "https://images.unsplash.com/photo-1517649763962-0c623066013b?q=80&w=1600&auto=format&fit=crop"


def actual() -> dict:
    return TEMAS[st.session_state.get("tema", "oscuro")]


def alternar() -> None:
    st.session_state.tema = "verde" if actual() is TEMAS["oscuro"] else "oscuro"


def aplicar() -> None:
    t = actual()
    css = f"""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Symbols+Outlined" />
    <style>
    :root {{
        --ac:{t['ac']}; --achi:{t['achi']}; --bg:{t['bg']}; --bgc:{t['bgc']};
        --bga:{t['bga']}; --bgs:{t['bgs']}; --tx:{t['tx']}; --tx2:{t['tx2']};
        --tx3:{t['tx3']}; --sbg:{t['sbg']}; --dorado:{t['dorado']};
        --radius: 18px; --radius-sm: 10px;
        --shadow: 0 8px 24px rgba(0,0,0,.18), 0 2px 6px rgba(0,0,0,.10);
        --shadow-lg: 0 20px 45px rgba(0,0,0,.28);
    }}

    html, body, [class^="css"], .stApp {{
        font-family: 'Inter', 'Poppins', sans-serif;
    }}
    h1, h2, h3, h4, .itc-titulo, .itc-seccion {{
        font-family: 'Poppins', sans-serif;
    }}

    @keyframes itcFadeUp {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes itcFadeIn {{
        from {{ opacity: 0; }}
        to   {{ opacity: 1; }}
    }}

    .stApp {{
        background: var(--bg);
        color: var(--tx);
    }}

    .main .block-container {{
        padding-top: 1rem;
        padding-bottom: 3rem;
        max-width: 1200px;
        animation: itcFadeUp .5s ease both;
    }}

    section[data-testid="stSidebar"] {{
        background: var(--sbg);
        width: 300px !important;
        min-width: 300px !important;
        max-width: 320px !important;
        border-right: 1px solid rgba(255,255,255,.06);
        box-shadow: var(--shadow-lg);
    }}
    section[data-testid="stSidebar"] > div {{
        padding: 1.1rem .9rem 2rem;
    }}
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p {{
        color: #EDEFEC;
    }}
    section[data-testid="stSidebar"] hr {{
        border-color: rgba(255,255,255,.08);
        margin: 1rem 0;
    }}

    section[data-testid="stSidebar"] .stExpander,
    section[data-testid="stSidebar"] div[data-testid="stForm"],
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: rgba(255,255,255,.05);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,.08);
        border-radius: var(--radius-sm);
    }}

    section[data-testid="stSidebar"] div[role="radiogroup"] label {{
        display: block;
        padding: .55rem .75rem;
        margin-bottom: .4rem;
        border-radius: var(--radius-sm);
        border: 1px solid rgba(255,255,255,.08);
        background: rgba(255,255,255,.03);
        transition: all .18s ease;
    }}
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
        background: rgba(30,122,76,.18);
        border-color: var(--ac);
        transform: translateX(2px);
    }}

    .stButton > button, .stFormSubmitButton > button {{
        border-radius: 999px !important;
        border: 1px solid var(--ac) !important;
        background: var(--ac) !important;
        color: #fff !important;
        font-weight: 600;
        letter-spacing: .2px;
        padding: .5rem 1.1rem;
        transition: transform .15s ease, box-shadow .15s ease, background .15s ease;
        box-shadow: 0 4px 14px rgba(30,122,76,.25);
    }}
    .stButton > button:hover, .stFormSubmitButton > button:hover {{
        background: var(--achi) !important;
        transform: translateY(-1px);
        box-shadow: 0 8px 20px rgba(30,122,76,.35);
    }}
    section[data-testid="stSidebar"] .stButton > button {{
        background: transparent !important;
        color: var(--tx) !important;
        border: 1px solid rgba(255,255,255,.15) !important;
        box-shadow: none;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        border-color: var(--ac) !important;
        background: rgba(30,122,76,.18) !important;
    }}

    .stTextInput input, .stNumberInput input, .stDateInput input,
    .stTimeInput input, .stSelectbox div[data-baseweb="select"] > div {{
        border-radius: var(--radius-sm) !important;
        border: 1px solid var(--tx3) !important;
    }}
    div[data-testid="stForm"] {{
        border: 1px solid var(--tx3);
        border-radius: var(--radius);
        padding: 1.1rem 1.2rem;
        background: var(--bgc);
        box-shadow: var(--shadow);
    }}

    div[data-testid="stTabs"] {{
        animation: itcFadeIn .4s ease both;
    }}
    div[data-testid="stTabs"] button[role="tab"] {{
        border-radius: 999px;
        padding: .5rem 1.1rem;
        margin-right: .35rem;
        font-weight: 600;
        color: var(--tx2);
        transition: all .18s ease;
    }}
    div[data-testid="stTabs"] button[role="tab"]:hover {{
        color: var(--ac);
        background: rgba(30,122,76,.08);
    }}
    div[data-testid="stTabs"] button[aria-selected="true"] {{
        background: var(--ac) !important;
        color: #fff !important;
        box-shadow: 0 4px 12px rgba(30,122,76,.3);
    }}
    div[data-testid="stTabs"] [data-baseweb="tab-highlight"],
    div[data-testid="stTabs"] [data-baseweb="tab-border"] {{
        display: none;
    }}
    div[data-baseweb="tab-panel"] {{
        background: var(--bgc);
        border: 1px solid var(--tx3);
        border-radius: var(--radius);
        padding: 1.6rem;
        margin-top: .6rem;
        box-shadow: var(--shadow);
        animation: itcFadeUp .35s ease both;
    }}

    div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {{
        border-radius: var(--radius-sm) !important;
        overflow: hidden;
        border: 1px solid var(--tx3);
        box-shadow: var(--shadow);
    }}
    div[data-testid="stDataFrame"] [role="columnheader"] {{
        background: var(--ac) !important;
        color: #fff !important;
        font-weight: 700 !important;
    }}
    div[data-testid="stDataFrame"] [role="row"]:nth-child(even) {{
        background: var(--bga) !important;
    }}
    div[data-testid="stDataFrame"] [role="row"]:hover {{
        background: rgba(30,122,76,.12) !important;
    }}

    .stExpander {{
        border: 1px solid var(--tx3) !important;
        border-radius: var(--radius-sm) !important;
        box-shadow: var(--shadow);
    }}
    div[data-baseweb="popover"] {{
        border-radius: var(--radius-sm) !important;
    }}

    .itc-hero {{
        position: relative;
        overflow: hidden;
        border-radius: var(--radius);
        padding: 4.2rem 2.4rem 2.6rem;
        margin-bottom: 1.6rem;
        min-height: 260px;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        background:
            {t['hero_grad']},
            url('{HERO_IMG}') center/cover no-repeat;
        box-shadow: var(--shadow-lg);
        animation: itcFadeIn .6s ease both;
    }}
    .itc-hero::after {{
        content: "";
        position: absolute; inset: 0;
        background: linear-gradient(120deg, rgba(30,122,76,.20), transparent 60%);
        pointer-events: none;
    }}
    .itc-hero-badge {{
        display: inline-flex; align-items: center; gap: .4rem;
        width: fit-content;
        background: rgba(255,255,255,.12);
        border: 1px solid rgba(255,255,255,.25);
        backdrop-filter: blur(6px);
        color: #fff;
        padding: .3rem .8rem;
        border-radius: 999px;
        font-size: .72rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: .9rem;
    }}
    .itc-titulo {{
        font-weight: 800;
        font-size: clamp(2rem, 4vw, 3.2rem);
        color: #fff;
        letter-spacing: 1px;
        line-height: 1.05;
        text-shadow: 0 2px 18px rgba(0,0,0,.35);
    }}
    .itc-titulo span {{ color: var(--dorado); }}
    .itc-sub {{
        color: rgba(255,255,255,.85);
        font-size: 1rem;
        margin-top: .5rem;
        font-weight: 500;
    }}

    .itc-seccion {{
        display: flex; align-items: center; gap: .4rem;
        color: var(--ac);
        font-size: .78rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin: 1.4rem 0 .8rem;
        font-weight: 700;
    }}
    .itc-seccion::before {{
        content: "";
        width: 4px; height: 14px;
        background: var(--dorado);
        border-radius: 3px;
        display: inline-block;
    }}

    .itc-tarjeta {{
        background: var(--bgc);
        border: 1px solid var(--tx3);
        border-left: 4px solid var(--tx3);
        padding: .8rem 1.1rem;
        margin-bottom: .5rem;
        border-radius: var(--radius-sm);
        transition: all .18s ease;
    }}
    .itc-tarjeta:hover {{
        box-shadow: var(--shadow);
        transform: translateY(-1px);
    }}
    .itc-tarjeta.jugado {{ border-left-color: var(--ac); }}

    .itc-marcador {{
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
        font-size: 1.4rem;
        color: var(--ac);
        letter-spacing: 1px;
    }}

    .itc-casilla {{
        background: var(--bgc);
        border: 1px solid var(--tx3);
        border-radius: var(--radius-sm);
        padding: .7rem 1rem;
        margin-bottom: .7rem;
        font-size: .88rem;
        box-shadow: var(--shadow);
        transition: all .18s ease;
    }}
    .itc-casilla:hover {{ transform: translateY(-2px); }}
    .itc-casilla.ganador {{
        border-color: var(--ac);
        background: linear-gradient(180deg, rgba(30,122,76,.10), transparent);
        color: var(--achi);
    }}
    .itc-vacia {{ color: var(--tx2); font-style: italic; }}
    </style>
    """
    st.markdown(textwrap.dedent(css), unsafe_allow_html=True)


def hero(titulo: str, subtitulo: str) -> None:
    """Banner tipo hero con imagen de fondo y overlay institucional."""
    partes = titulo.split()
    primera, resto = (partes[0], " ".join(partes[1:])) if partes else (titulo, "")
    html = f"""
    <div class="itc-hero">
        <span class="material-symbols-outlined" style="position:absolute; top:1.6rem; left:2.2rem;
              color:#fff; font-size:2.4rem; opacity:.9;">sports_soccer</span>
        <div class="itc-hero-badge">
            <span class="material-symbols-outlined" style="font-size:16px;">verified</span>
            Plataforma oficial
        </div>
        <div class="itc-titulo">{primera} <span>{resto}</span></div>
        <div class="itc-sub">{subtitulo}</div>
    </div>
    """
    st.markdown(textwrap.dedent(html), unsafe_allow_html=True)


def seccion(texto: str) -> None:
    st.markdown(f'<div class="itc-seccion">{texto}</div>', unsafe_allow_html=True)
