"""Los dos temas de la aplicación.

Identidad visual inspirada en la ETITC: verde institucional, blanco, gris y
detalles dorados discretos. La firma pública (`aplicar`, `hero`, `seccion`,
`actual`, `alternar`) no cambia: solo cambia lo que dibujan.
"""

from __future__ import annotations

import streamlit as st

TEMAS = {
    # Modo oscuro institucional: verde-negro profundo con dorado como acento.
    "oscuro": dict(
        ac="#C9A227", achi="#E8C866", bg="#0E1712", bgc="#16211B", bga="#131C17",
        bgs="#0A100C",
        tx="#F5F7F5", tx2="#9FB3A6", tx3="#5C6E63",
        grad="linear-gradient(160deg,#0E1712 0%,#152A1D 60%,#0E1712 100%)",
        ico="☀️", lbl="Modo Claro",
    ),
    # Modo claro institucional: blanco y gris claro con verde ETITC como acento.
    "verde": dict(
        ac="#146938", achi="#1B8449", bg="#F6F8F7", bgc="#FFFFFF", bga="#F0F3F1",
        bgs="#FFFFFF",
        tx="#16211B", tx2="#4B5A52", tx3="#8B978F",
        grad="linear-gradient(160deg,#FFFFFF 0%,#EAF2ED 60%,#FFFFFF 100%)",
        ico="🌙", lbl="Modo Oscuro",
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
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700;800&family=Inter:wght@400;500;600&display=swap');

        :root {{
            --ac:{t['ac']}; --achi:{t['achi']};
            --bg:{t['bg']}; --bgc:{t['bgc']}; --bga:{t['bga']}; --bgs:{t['bgs']};
            --tx:{t['tx']}; --tx2:{t['tx2']}; --tx3:{t['tx3']};
            --grad:{t['grad']};
            --radius-lg: 20px;
            --radius-md: 14px;
            --radius-sm: 10px;
            --shadow-soft: 0 4px 20px rgba(0,0,0,.10);
            --shadow-elev: 0 12px 32px rgba(0,0,0,.16);
        }}

        html, body, [class*="css"] {{
            font-family: 'Inter', 'Poppins', sans-serif;
        }}
        h1, h2, h3, h4, .itc-titulo {{
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
        }}

        /* ── Base ────────────────────────────────────────────────────────── */
        .stApp {{
            background: var(--bg);
            color: var(--tx);
        }}
        h1, h2, h3 {{ color: var(--ac); letter-spacing: .3px; }}

        /* ── Animaciones ─────────────────────────────────────────────────── */
        @keyframes itc-fade-up {{
            from {{ opacity: 0; transform: translateY(14px); }}
            to   {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes itc-fade-in {{
            from {{ opacity: 0; }}
            to   {{ opacity: 1; }}
        }}
        .itc-hero, .itc-tarjeta, .itc-casilla, .stTabs, div[data-testid="stForm"] {{
            animation: itc-fade-up .5s ease both;
        }}

        /* ── HERO ────────────────────────────────────────────────────────── */
        .itc-hero {{
            position: relative;
            overflow: hidden;
            padding: 56px 40px;
            margin-bottom: 28px;
            border-radius: var(--radius-lg);
            background:
                linear-gradient(180deg, rgba(10,16,12,.72), rgba(10,16,12,.85)),
                url('https://images.unsplash.com/photo-1517649763962-0c623066013b?q=80&w=1600&auto=format&fit=crop')
                center/cover no-repeat;
            box-shadow: var(--shadow-elev);
            border: 1px solid rgba(201,162,39,.25);
        }}
        .itc-hero-logo {{
            width: 56px; height: 56px; border-radius: 14px;
            background: rgba(255,255,255,.08);
            border: 1px solid rgba(201,162,39,.4);
            display: flex; align-items: center; justify-content: center;
            font-size: 26px; margin-bottom: 14px;
            backdrop-filter: blur(6px);
        }}
        .itc-titulo {{
            font-size: clamp(2rem, 5vw, 3.2rem);
            color: #FFFFFF;
            letter-spacing: 5px;
            line-height: 1.1;
            text-shadow: 0 2px 18px rgba(0,0,0,.4);
        }}
        .itc-sub {{
            color: var(--achi);
            font-size: .95rem;
            font-weight: 600;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-top: 10px;
        }}

        /* ── SIDEBAR: panel institucional con glassmorphism, fijo ─────────── */
        section[data-testid="stSidebar"] {{
            background: var(--bgs);
            width: 300px !important;
            min-width: 300px !important;
            border-right: 1px solid rgba(201,162,39,.15);
            position: sticky;
            top: 0;
            height: 100vh;
            overflow-y: auto;
        }}
        section[data-testid="stSidebar"] > div {{
            background: transparent;
            padding: 18px 14px 40px;
        }}
        .itc-side-card {{
            background: linear-gradient(160deg, rgba(255,255,255,.06), rgba(255,255,255,.02));
            border: 1px solid rgba(255,255,255,.08);
            border-radius: var(--radius-md);
            padding: 14px 16px;
            margin-bottom: 14px;
            backdrop-filter: blur(10px);
            box-shadow: var(--shadow-soft);
            animation: itc-fade-in .4s ease both;
        }}
        .itc-side-user {{
            display: flex; align-items: center; gap: 10px;
        }}
        .itc-side-avatar {{
            width: 38px; height: 38px; border-radius: 50%;
            background: var(--grad);
            border: 1px solid var(--ac);
            display: flex; align-items: center; justify-content: center;
            font-size: 18px;
            flex-shrink: 0;
        }}
        .itc-side-role {{
            font-size: .72rem; color: var(--tx3);
            text-transform: uppercase; letter-spacing: 1.2px;
        }}
        .itc-side-name {{
            font-weight: 600; color: var(--tx); font-size: .92rem;
        }}
        section[data-testid="stSidebar"] hr {{
            border-color: rgba(255,255,255,.08);
            margin: 6px 0 16px;
        }}

        /* Botones y radios dentro del sidebar, estilo pill/tarjeta */
        section[data-testid="stSidebar"] .stButton > button {{
            width: 100%;
            border-radius: var(--radius-sm);
            border: 1px solid rgba(255,255,255,.10);
            background: rgba(255,255,255,.04);
            color: var(--tx);
            font-weight: 500;
            transition: all .2s ease;
        }}
        section[data-testid="stSidebar"] .stButton > button:hover {{
            border-color: var(--ac);
            background: rgba(201,162,39,.12);
            transform: translateY(-1px);
        }}
        section[data-testid="stSidebar"] [role="radiogroup"] label {{
            border-radius: var(--radius-sm);
            padding: 6px 10px;
            transition: background .2s ease;
        }}
        section[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
            background: rgba(255,255,255,.05);
        }}

        /* ── Botones generales ───────────────────────────────────────────── */
        .stButton > button, .stFormSubmitButton > button {{
            border-radius: var(--radius-sm);
            font-weight: 600;
            transition: transform .15s ease, box-shadow .15s ease;
            box-shadow: var(--shadow-soft);
        }}
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-elev);
        }}

        /* ── TABS modernas ───────────────────────────────────────────────── */
        div[data-testid="stTabs"] button[role="tab"] {{
            font-family: 'Poppins', sans-serif;
            font-weight: 600;
            font-size: .92rem;
            border-radius: var(--radius-sm) var(--radius-sm) 0 0;
            padding: 10px 18px;
            transition: all .2s ease;
            color: var(--tx2);
        }}
        div[data-testid="stTabs"] button[role="tab"]:hover {{
            color: var(--ac);
        }}
        div[data-testid="stTabs"] button[aria-selected="true"] {{
            color: var(--ac);
            border-bottom: 3px solid var(--ac);
        }}
        div[data-testid="stTabs"] > div:nth-child(2) {{
            background: var(--bgc);
            border-radius: 0 var(--radius-lg) var(--radius-lg) var(--radius-lg);
            padding: 28px 26px;
            margin-top: -1px;
            box-shadow: var(--shadow-soft);
            border: 1px solid rgba(255,255,255,.06);
            animation: itc-fade-up .35s ease both;
        }}

        /* ── Tarjetas de contenido (calendario, partidos, cuadro) ─────────── */
        .itc-seccion {{
            color: var(--ac); font-size: .78rem; letter-spacing: 2px;
            text-transform: uppercase; margin: 18px 0 10px; font-weight: 700;
        }}
        .itc-tarjeta {{
            background: var(--bgc);
            border: 1px solid rgba(255,255,255,.06);
            border-left: 4px solid var(--tx3);
            padding: 12px 16px;
            margin-bottom: 8px;
            border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
            box-shadow: var(--shadow-soft);
            transition: border-color .2s ease, transform .15s ease;
        }}
        .itc-tarjeta:hover {{ transform: translateX(2px); }}
        .itc-tarjeta.jugado {{ border-left-color: var(--ac); }}
        .itc-marcador {{
            font-family: 'Poppins', sans-serif; font-weight: 700; font-size: 1.5rem;
            color: var(--achi); letter-spacing: 2px;
        }}
        .itc-casilla {{
            background: var(--bgc); border: 1px solid rgba(255,255,255,.08);
            border-radius: var(--radius-sm);
            padding: 10px 14px; margin-bottom: 10px; font-size: .85rem;
            box-shadow: var(--shadow-soft);
            transition: border-color .2s ease, box-shadow .2s ease;
        }}
        .itc-casilla:hover {{ box-shadow: var(--shadow-elev); }}
        .itc-casilla.ganador {{
            border-color: var(--ac); color: var(--achi);
            box-shadow: 0 0 0 1px var(--ac);
        }}
        .itc-vacia {{ color: var(--tx3); font-style: italic; }}

        /* ── Tabla nativa (contenedor, dado el límite de canvas) ───────────── */
        div[data-testid="stDataFrame"] {{
            border-radius: var(--radius-md) !important;
            overflow: hidden;
            box-shadow: var(--shadow-soft);
            border: 1px solid rgba(255,255,255,.08);
        }}

        /* ── Expanders / popovers / forms ──────────────────────────────────── */
        div[data-testid="stExpander"] {{
            border-radius: var(--radius-md);
            border: 1px solid rgba(255,255,255,.08);
            overflow: hidden;
        }}
        div[data-testid="stPopover"] > div {{
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-elev);
        }}
        div[data-testid="stForm"] {{
            background: var(--bga);
            border-radius: var(--radius-md);
            padding: 16px;
            border: 1px solid rgba(255,255,255,.06);
        }}
        </style>""",
        unsafe_allow_html=True,
    )


def hero(titulo: str, subtitulo: str) -> None:
    st.markdown(
        f'<div class="itc-hero">'
        f'<div class="itc-hero-logo">🏆</div>'
        f'<div class="itc-titulo">{titulo}</div>'
        f'<div class="itc-sub">{subtitulo}</div></div>',
        unsafe_allow_html=True,
    )


def seccion(texto: str) -> None:
    st.markdown(f'<div class="itc-seccion">{texto}</div>', unsafe_allow_html=True)
