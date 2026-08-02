"""Los dos temas de la aplicación.

Identidad visual institucional: verde-dorado, tipografía Poppins/Inter, hero
con carrusel de fondos y logo propio, sidebar en tarjetas reales (vía
st.container(key=...), no divs huérfanos entre llamadas de markdown).
"""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

TEMAS = {
    "oscuro": dict(
        ac="#C9A227", achi="#E8C866", bg="#0E1712", bgc="#16211B", bga="#131C17",
        bgs="#0A100C",
        tx="#F5F7F5", tx2="#9FB3A6", tx3="#7C9186",
        grad="linear-gradient(160deg,#0E1712 0%,#152A1D 60%,#0E1712 100%)",
        ico="☀️", lbl="Modo Claro",
    ),
    "verde": dict(
        ac="#146938", achi="#1B8449", bg="#F6F8F7", bgc="#FFFFFF", bga="#F0F3F1",
        bgs="#FFFFFF",
        tx="#16211B", tx2="#3F4C45", tx3="#6B7A72",
        grad="linear-gradient(160deg,#FFFFFF 0%,#EAF2ED 60%,#FFFFFF 100%)",
        ico="🌙", lbl="Modo Oscuro",
    ),
}

_CARPETA_ESTATICA = Path("static")
_EXTENSIONES = (".jpg", ".jpeg", ".png", ".webp")


def actual() -> dict:
    return TEMAS[st.session_state.get("tema", "oscuro")]


def alternar() -> None:
    st.session_state.tema = "verde" if actual() is TEMAS["oscuro"] else "oscuro"


# ── Recursos: logo y fondos del carrusel, como data-URI cacheado ────────────


def _buscar(nombre_base: str) -> Path | None:
    for ext in _EXTENSIONES:
        candidato = _CARPETA_ESTATICA / f"{nombre_base}{ext}"
        if candidato.is_file():
            return candidato
    return None


@st.cache_data(show_spinner=False)
def _a_base64(ruta_str: str, mtime: float) -> str:
    ruta = Path(ruta_str)
    mime = {
        ".png": "image/png", ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg", ".webp": "image/webp",
    }.get(ruta.suffix.lower(), "image/png")
    datos = ruta.read_bytes()
    return f"data:{mime};base64,{base64.b64encode(datos).decode()}"


def _uri_de(nombre_base: str) -> str | None:
    archivo = _buscar(nombre_base)
    if archivo is None:
        return None
    return _a_base64(str(archivo), archivo.stat().st_mtime)


def _fondos_carrusel() -> list[str]:
    fondos = [_uri_de(f"fondo_{i}") for i in range(1, 6)]
    return [f for f in fondos if f is not None]


def logo_uri() -> str | None:
    """El logo institucional, listo para incrustar en un <img src="...">."""
    return _uri_de("logo_itc-deportes") or _uri_de("logo")


# ── Estilos ──────────────────────────────────────────────────────────────


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
            --radius-lg: 20px; --radius-md: 14px; --radius-sm: 10px;
            --shadow-soft: 0 4px 20px rgba(0,0,0,.10);
            --shadow-elev: 0 12px 32px rgba(0,0,0,.16);
        }}

        html, body, [class*="css"] {{ font-family: 'Inter', 'Poppins', sans-serif; }}
        h1, h2, h3, h4, .itc-titulo {{ font-family: 'Poppins', sans-serif; font-weight: 700; }}

        .stApp {{ background: var(--bg); color: var(--tx); }}
        h1, h2, h3 {{ color: var(--ac); letter-spacing: .3px; }}
        p, span, label, div {{ color: var(--tx); }}

        div[data-testid="stDecoration"] {{ height: 2px !important; }}

        /* Oculta cualquier resto del toolbar nativo de st.dataframe, por si
           se usa en algún otro lugar del proyecto a futuro. */
        div[data-testid="stElementToolbar"] {{ display: none !important; }}

        hr {{
            border: none !important;
            border-top: 1px solid rgba(120,140,130,.18) !important;
            margin: 10px 0 !important;
        }}

        @keyframes itc-fade-up {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to   {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes itc-fade-in {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        .itc-hero, .itc-tarjeta, .itc-casilla, .stTabs, div[data-testid="stForm"] {{
            animation: itc-fade-up .45s ease both;
        }}

        /* ── HERO con carrusel de fondos ───────────────────────────────────── */
        .itc-hero {{
            position: relative; overflow: hidden; min-height: 260px;
            display: flex; align-items: flex-end;
            padding: 48px 40px; margin-bottom: 28px;
            border-radius: var(--radius-lg);
            background: var(--grad);
            box-shadow: var(--shadow-elev);
            border: 1px solid rgba(201,162,39,.25);
        }}
        .itc-hero-capas {{ position: absolute; inset: 0; z-index: 0; }}
        .itc-hero-bg {{
            position: absolute; inset: 0; background-size: cover; background-position: center;
            opacity: 0; animation: itc-carrusel 30s ease-in-out infinite;
        }}
        @keyframes itc-carrusel {{
            0% {{ opacity: 0; }} 4% {{ opacity: 1; }} 18% {{ opacity: 1; }}
            23% {{ opacity: 0; }} 100% {{ opacity: 0; }}
        }}
        .itc-hero-overlay {{
            position: absolute; inset: 0; z-index: 1;
            background: linear-gradient(180deg, rgba(10,16,12,.50), rgba(10,16,12,.88));
        }}
        .itc-hero-contenido {{ position: relative; z-index: 2; width: 100%; }}
        .itc-hero-logo {{
            width: 56px; height: 56px; border-radius: 14px;
            background: rgba(255,255,255,.08); border: 1px solid rgba(201,162,39,.4);
            display: flex; align-items: center; justify-content: center;
            margin-bottom: 14px; backdrop-filter: blur(6px); overflow: hidden;
        }}
        .itc-hero-logo img {{ width: 36px; height: 36px; object-fit: contain; }}
        .itc-titulo {{
            font-size: clamp(2rem, 5vw, 3.2rem); color: #FFFFFF;
            letter-spacing: 5px; line-height: 1.1; text-shadow: 0 2px 18px rgba(0,0,0,.4);
        }}
        .itc-sub {{
            color: var(--achi); font-size: .95rem; font-weight: 600;
            letter-spacing: 2px; text-transform: uppercase; margin-top: 10px;
        }}

        /* ── SIDEBAR ─────────────────────────────────────────────────────── */
        section[data-testid="stSidebar"] {{
            background: var(--bgs); width: 300px !important; min-width: 300px !important;
            border-right: 1px solid rgba(201,162,39,.15);
            position: sticky; top: 0; height: 100vh; overflow-y: auto;
        }}
        section[data-testid="stSidebar"] > div {{ background: transparent; padding: 18px 14px 40px; }}

        /* Fuerza legibilidad del texto del sidebar en AMBOS temas, sin
           importar qué color interno traiga Streamlit por su config.toml. */
        section[data-testid="stSidebar"] * {{ color: var(--tx) !important; }}
        section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] * {{
            color: var(--tx2) !important;
        }}

        /* Tarjetas reales (st.container(key=...)) */
        .st-key-itc-brand, .st-key-itc-demo, .st-key-itc-user, .st-key-itc-comp {{
            background: linear-gradient(160deg, rgba(120,140,130,.10), rgba(120,140,130,.02));
            border: 1px solid rgba(120,140,130,.18);
            border-radius: var(--radius-md);
            padding: 16px;
            margin-bottom: 14px;
            backdrop-filter: blur(10px);
            box-shadow: var(--shadow-soft);
            transition: border-color .2s ease, box-shadow .2s ease, transform .2s ease;
        }}
        .st-key-itc-brand:hover, .st-key-itc-demo:hover,
        .st-key-itc-user:hover, .st-key-itc-comp:hover {{
            border-color: rgba(201,162,39,.35);
            box-shadow: var(--shadow-elev);
        }}

        .itc-brand {{ display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center; }}
        .itc-brand-logo-img {{ width: 52px; height: 52px; object-fit: contain; border-radius: 12px; }}
        .itc-brand-logo-fallback {{ font-size: 30px; }}
        .itc-brand-title {{
            font-family: 'Poppins', sans-serif; font-weight: 800;
            font-size: 1.05rem; letter-spacing: 2px !important; color: var(--tx) !important;
        }}

        .itc-side-user {{ display: flex; align-items: center; gap: 10px; }}
        .itc-side-avatar {{
            width: 38px; height: 38px; border-radius: 50%;
            background: var(--grad); border: 1px solid var(--ac);
            display: flex; align-items: center; justify-content: center;
            font-size: 18px; flex-shrink: 0;
        }}
        .itc-side-role {{
            font-size: .72rem; color: var(--tx3) !important;
            text-transform: uppercase; letter-spacing: 1.2px;
        }}
        .itc-side-name {{ font-weight: 600; color: var(--tx) !important; font-size: .92rem; }}

        section[data-testid="stSidebar"] .stButton > button {{
            width: 100%; border-radius: var(--radius-sm);
            border: 1px solid rgba(120,140,130,.22);
            background: rgba(120,140,130,.06);
            font-weight: 500; transition: all .18s ease;
        }}
        section[data-testid="stSidebar"] .stButton > button:hover {{
            border-color: var(--ac); background: rgba(201,162,39,.14);
            transform: translateY(-1px);
        }}
        section[data-testid="stSidebar"] [role="radiogroup"] label {{
            border-radius: var(--radius-sm); padding: 6px 10px; transition: background .18s ease;
        }}
        section[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
            background: rgba(120,140,130,.08);
        }}

        /* ── Botones generales ────────────────────────────────────────────── */
        .stButton > button, .stFormSubmitButton > button {{
            border-radius: var(--radius-sm); font-weight: 600;
            transition: transform .15s ease, box-shadow .15s ease;
            box-shadow: var(--shadow-soft);
        }}
        .stButton > button:hover {{ transform: translateY(-2px); box-shadow: var(--shadow-elev); }}

        /* ── TABS ─────────────────────────────────────────────────────────── */
        div[data-testid="stTabs"] button[role="tab"] {{
            font-family: 'Poppins', sans-serif; font-weight: 600; font-size: .92rem;
            border-radius: var(--radius-sm) var(--radius-sm) 0 0;
            padding: 10px 18px; transition: color .2s ease; color: var(--tx2) !important;
        }}
        div[data-testid="stTabs"] button[role="tab"]:hover {{ color: var(--ac) !important; }}
        div[data-testid="stTabs"] button[aria-selected="true"] {{
            color: var(--ac) !important; border-bottom: 3px solid var(--ac);
        }}
        div[data-testid="stTabs"] > div:nth-child(2) {{
            background: var(--bgc);
            border-radius: 0 var(--radius-lg) var(--radius-lg) var(--radius-lg);
            padding: 28px 26px; margin-top: -1px;
            box-shadow: var(--shadow-soft);
            border: 1px solid rgba(120,140,130,.14);
            animation: itc-fade-up .3s ease both;
        }}

        /* ── Tarjetas de contenido ────────────────────────────────────────── */
        .itc-seccion {{
            color: var(--ac) !important; font-size: .78rem; letter-spacing: 2px;
            text-transform: uppercase; margin: 18px 0 10px; font-weight: 700;
        }}
        .itc-tarjeta {{
            background: var(--bgc); border: 1px solid rgba(120,140,130,.14);
            border-left: 3px solid var(--tx3);
            padding: 12px 16px; margin-bottom: 8px;
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
            background: var(--bgc); border: 1px solid rgba(120,140,130,.16);
            border-radius: var(--radius-sm);
            padding: 10px 14px; margin-bottom: 10px; font-size: .85rem;
            box-shadow: var(--shadow-soft);
            transition: border-color .2s ease, box-shadow .2s ease;
        }}
        .itc-casilla:hover {{ box-shadow: var(--shadow-elev); }}
        .itc-casilla.ganador {{ border-color: var(--ac); color: var(--achi); box-shadow: 0 0 0 1px var(--ac); }}
        .itc-vacia {{ color: var(--tx3); font-style: italic; }}

        /* ── Tabla (st.table: HTML plano, sin toolbar ni buscador) ─────────── */
        div[data-testid="stTable"] {{
            border-radius: var(--radius-md);
            overflow: hidden;
            box-shadow: var(--shadow-soft);
            border: 1px solid rgba(120,140,130,.16);
        }}
        div[data-testid="stTable"] table {{
            width: 100%; border-collapse: collapse; font-size: .9rem;
        }}
        div[data-testid="stTable"] thead th {{
            background: var(--ac); color: #FFFFFF !important;
            font-family: 'Poppins', sans-serif; font-weight: 600;
            text-transform: uppercase; letter-spacing: .5px;
            padding: 12px 14px; text-align: left; border: none;
        }}
        div[data-testid="stTable"] tbody td {{
            padding: 10px 14px; color: var(--tx);
            border-bottom: 1px solid rgba(120,140,130,.12);
        }}
        div[data-testid="stTable"] tbody tr:nth-child(even) {{
            background: rgba(120,140,130,.05);
        }}
        div[data-testid="stTable"] tbody tr:hover {{
            background: rgba(201,162,39,.10);
        }}
        div[data-testid="stTable"] td:not(:nth-child(1)):not(:nth-child(2)),
        div[data-testid="stTable"] th:not(:nth-child(1)):not(:nth-child(2)) {{
            text-align: right;
        }}

        div[data-testid="stExpander"] {{ border-radius: var(--radius-md); border: 1px solid rgba(120,140,130,.16); overflow: hidden; }}
        div[data-testid="stPopover"] > div {{ border-radius: var(--radius-md); box-shadow: var(--shadow-elev); }}
        div[data-testid="stForm"] {{
            background: var(--bga); border-radius: var(--radius-md);
            padding: 16px; border: 1px solid rgba(120,140,130,.14);
        }}
        </style>""",
        unsafe_allow_html=True,
    )


def hero(titulo: str, subtitulo: str) -> None:
    fondos = _fondos_carrusel()
    logo = logo_uri()

    capas = "".join(
        f'<div class="itc-hero-bg" style="background-image:url(\'{src}\');'
        f'animation-delay:{i * 6}s;"></div>'
        for i, src in enumerate(fondos)
    )
    logo_html = f'<img src="{logo}" alt="ITC Deportes">' if logo else "🏆"

    st.markdown(
        f'<div class="itc-hero">'
        f'<div class="itc-hero-capas">{capas}</div>'
        f'<div class="itc-hero-overlay"></div>'
        f'<div class="itc-hero-contenido">'
        f'<div class="itc-hero-logo">{logo_html}</div>'
        f'<div class="itc-titulo">{titulo}</div>'
        f'<div class="itc-sub">{subtitulo}</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def seccion(texto: str) -> None:
    st.markdown(f'<div class="itc-seccion">{texto}</div>', unsafe_allow_html=True)
