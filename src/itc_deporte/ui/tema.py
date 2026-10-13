"""Los dos temas de la aplicación.

Rediseño: composición de galería deportiva (franja negra superior, hero a tres
paneles, títulos condensados, botones cuadrados con sombra desplazada, pestañas
como navegación) y cuadro final de diagrama (monoespaciada, esquinas rectas,
líneas de 1 px). Las paletas siguen siendo las de siempre: dorado y verde.

Lo que cambia es solo el aspecto. Ninguna función cambia de firma.
"""

from __future__ import annotations

from string import Template

import streamlit as st

# `wire` es el color de las líneas finas y `on` el del texto sobre el acento.
TEMAS = {
    "oscuro": dict(
        ac="#D4A017", achi="#FFD040", bg="#0A0A0A", bgc="#141414", bga="#101010",
        bgs="#1A1200", tx="#F5F0E8", tx2="#9A9080", tx3="#5A5550", sbg="#050505",
        wire="#2B2A26", on="#0A0A0A",
        grad="linear-gradient(135deg,#0A0A0A,#1A1200)", ico="🟢", lbl="Tema Verde",
    ),
    "verde": dict(
        ac="#4CAF28", achi="#7FD44A", bg="#0D1F0F", bgc="#122516", bga="#0F1E12",
        bgs="#0A1A08", tx="#E8F5E0", tx2="#8AB880", tx3="#507848", sbg="#071208",
        wire="#21402A", on="#071208",
        grad="linear-gradient(135deg,#071208,#0D2010)", ico="🌙", lbl="Tema Oscuro",
    ),
}


def actual() -> dict:
    return TEMAS[st.session_state.get("tema", "oscuro")]


def alternar() -> None:
    st.session_state.tema = "verde" if actual() is TEMAS["oscuro"] else "oscuro"


# Plantilla con `$nombre` y no f-string: el CSS está lleno de llaves.
_CSS = Template(
    """<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=JetBrains+Mono:wght@500;700&display=swap');

/* ── Base ───────────────────────────────────────────────────────────── */
.stApp { background:$bg; color:$tx; }
.block-container { max-width:1440px; padding:4.5rem 2rem 3rem; }
h1,h2,h3 { color:$tx; font-weight:500; }
h2 {
    font-family:'Bebas Neue',Impact,sans-serif; font-weight:400;
    font-size:2.4rem; letter-spacing:2px; text-transform:uppercase;
    border-bottom:1px solid $wire; padding-bottom:8px;
}
section[data-testid="stSidebar"] { background:$sbg; border-right:1px solid $wire; }
section[data-testid="stSidebar"] h2 { font-size:1.8rem; border-bottom:0; }

/* Franja superior: el aviso de la tienda, aquí sobre la cabecera de Streamlit. */
[data-testid="stHeader"] { background:$sbg; height:2.75rem; border-bottom:1px solid $wire; }
[data-testid="stHeader"]::after {
    content:"Competición escolar · Intercursos 2026 · Resultados al instante";
    position:absolute; left:50%; top:50%; transform:translate(-50%,-50%);
    font-size:.68rem; font-weight:700; letter-spacing:2px; text-transform:uppercase;
    color:$tx; pointer-events:none; white-space:nowrap;
}

/* ── Hero a tres paneles ────────────────────────────────────────────── */
.itc-hero {
    display:grid; grid-template-columns:1.1fr 1.6fr; min-height:250px;
    background:$bga; border-bottom:3px solid $ac; margin-bottom:28px; overflow:hidden;
}
.itc-hero-txt { padding:32px; align-self:end; }
.itc-titulo {
    font-family:'Bebas Neue',Impact,sans-serif; font-size:clamp(3rem,7vw,5.5rem);
    line-height:.95; color:$tx; letter-spacing:2px;
}
.itc-sub {
    display:inline-block; margin-top:14px; background:$tx; color:$bg;
    padding:4px 10px; font-size:.8rem; font-weight:700;
}
.itc-hero-paneles { display:grid; grid-template-columns:repeat(3,1fr); }
.itc-hero-paneles i { display:block; background:linear-gradient(160deg,$bgs,$bgc); }
.itc-hero-paneles i:nth-child(2) { background:linear-gradient(160deg,$bgc,$bga); border-left:1px solid $wire; }
.itc-hero-paneles i:nth-child(3) { background:linear-gradient(160deg,$ac,$bgs); }
@media (max-width:800px) {
    .itc-hero { grid-template-columns:1fr; }
    .itc-hero-paneles { display:none; }
}

/* ── Títulos de sección y tarjetas ──────────────────────────────────── */
.itc-seccion {
    font-family:'Bebas Neue',Impact,sans-serif; font-size:1.5rem; letter-spacing:2px;
    color:$tx; margin:22px 0 10px; border-bottom:1px solid $wire; padding-bottom:6px;
}
.itc-tarjeta {
    background:$bgc; border:1px solid $wire; border-left:3px solid $tx3;
    padding:10px 14px; margin-bottom:6px;
}
.itc-tarjeta.jugado { border-left-color:$ac; }
.itc-marcador {
    font-family:'JetBrains Mono',ui-monospace,Menlo,monospace; font-weight:700;
    font-size:1.4rem; color:$achi; letter-spacing:-0.02em; text-align:center;
}
.itc-vacia { color:$tx3; font-style:italic; text-align:center; }

/* ── Botones: cuadrados, con sombra desplazada ──────────────────────── */
.stButton button, .stFormSubmitButton button, [data-testid="stPopover"] button {
    border-radius:0; background:$tx; color:$bg; border:1px solid $tx;
    font-weight:700; font-size:.74rem; letter-spacing:1.5px; text-transform:uppercase;
    box-shadow:3px 3px 0 $ac; transition:transform .08s, box-shadow .08s;
}
.stButton button p, .stFormSubmitButton button p, [data-testid="stPopover"] button p { color:inherit; }
.stButton button:hover, .stFormSubmitButton button:hover, [data-testid="stPopover"] button:hover {
    background:$tx; color:$bg; border-color:$tx; transform:translate(2px,2px); box-shadow:1px 1px 0 $ac;
}
.stButton button:disabled { opacity:.55; box-shadow:none; }
.stButton button:focus-visible, .stFormSubmitButton button:focus-visible { outline:2px solid $ac; outline-offset:2px; }

/* ── Pestañas como navegación ───────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] { gap:28px; border-bottom:1px solid $wire; }
.stTabs button[data-baseweb="tab"] {
    padding:0 0 12px; font-weight:700; font-size:.82rem; letter-spacing:1.5px;
    text-transform:uppercase; color:$tx2;
}
.stTabs button[data-baseweb="tab"][aria-selected="true"] { color:$tx; }
.stTabs [data-baseweb="tab-highlight"] { background:$ac; height:3px; }
.stTabs [data-baseweb="tab-border"] { display:none; }

/* ── Formularios, tablas, avisos: esquinas rectas ───────────────────── */
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="select"] > div,
[data-baseweb="textarea"], .stNumberInput input { border-radius:0 !important; }
[data-testid="stExpander"] { border:1px solid $wire; border-radius:0; background:transparent; }
[data-testid="stAlert"] { border-radius:0; }
[data-testid="stDataFrame"] { border:1px solid $wire; border-radius:0; }

/* ── Cuadro final: diagrama ─────────────────────────────────────────── */
.bk {
    display:flex; align-items:stretch; overflow-x:auto; padding:4px 40px 12px 0;
    font-family:'JetBrains Mono',ui-monospace,Menlo,monospace;
}
.bk-col { flex:0 0 220px; display:flex; flex-direction:column; margin-right:36px; }
.bk-col:last-child { margin-right:0; }
.bk-tag {
    align-self:flex-start; background:$ac; color:$on; font-size:.7rem; font-weight:700;
    letter-spacing:1px; text-transform:uppercase; padding:4px 8px; margin-bottom:10px;
}
.bk-body { flex:1; display:flex; flex-direction:column; }
.bk-par { flex:1; position:relative; display:flex; flex-direction:column; }
/* Conector en ángulo recto: un corchete entre los dos cruces y un tramo al siguiente. */
.bk-par::after {
    content:""; position:absolute; right:-18px; top:25%; bottom:25%; width:18px;
    border:1px solid $wire; border-left:0; pointer-events:none;
}
.bk-par::before {
    content:""; position:absolute; right:-36px; top:50%; width:18px;
    border-top:1px solid $wire; pointer-events:none;
}
.bk-par.avanza::after, .bk-par.avanza::before { border-color:$ac; }
.bk-par.fin::after, .bk-par.fin::before { display:none; }
.bk-slot { flex:1; display:flex; align-items:center; padding:6px 0; min-height:96px; }
.bk-m { width:100%; border:1px solid $wire; background:$bgc; }
.bk-m.ganado { border-color:$tx3; }
.bk-eq { display:flex; align-items:stretch; min-height:30px; font-size:.78rem; }
.bk-eq + .bk-eq { border-top:1px solid $wire; }
.bk-id {
    flex:0 0 36px; display:flex; align-items:center; justify-content:center;
    background:$sbg; color:$tx; font-size:.65rem; font-weight:700;
}
.bk-n {
    flex:1; display:flex; align-items:center; padding:0 8px; color:$tx; font-weight:500;
    font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis; min-width:0;
}
.bk-s {
    flex:0 0 32px; display:flex; align-items:center; justify-content:center;
    border-left:1px solid $wire; color:$tx; font-weight:700;
}
.bk-eq.gana .bk-n { font-weight:700; }
.bk-eq.gana .bk-id, .bk-eq.gana .bk-s { background:$ac; color:$on; }
.bk-eq.vacio .bk-n { color:$tx3; font-style:italic; font-weight:400; }
.bk-nota {
    padding:3px 8px; font-size:.62rem; letter-spacing:1px; text-transform:uppercase;
    color:$tx2; border-top:1px solid $wire;
}
.bk-campeon { display:inline-flex; align-items:stretch; margin:0 0 18px; border:1px solid $ac; }
.bk-campeon .bk-tag { margin:0; align-self:stretch; display:flex; align-items:center; }
.bk-campeon .bk-nombre {
    padding:2px 14px; font-family:'Bebas Neue',Impact,sans-serif; font-size:1.6rem;
    letter-spacing:2px; color:$achi;
}

/* ── Pie ────────────────────────────────────────────────────────────── */
.itc-pie {
    margin-top:48px; background:$sbg; border-top:3px solid $ac; padding:28px 32px;
    display:flex; justify-content:space-between; flex-wrap:wrap; gap:16px;
    color:$tx2; font-size:.78rem;
}
.itc-pie b {
    font-family:'Bebas Neue',Impact,sans-serif; font-weight:400; font-size:1.5rem;
    letter-spacing:3px; color:$tx;
}
</style>"""
)


def aplicar() -> None:
    st.markdown(_CSS.safe_substitute(actual()), unsafe_allow_html=True)


def hero(titulo: str, subtitulo: str) -> None:
    st.markdown(
        '<div class="itc-hero"><div class="itc-hero-txt">'
        f'<div class="itc-titulo">{titulo}</div>'
        f'<div class="itc-sub">{subtitulo}</div></div>'
        '<div class="itc-hero-paneles"><i></i><i></i><i></i></div></div>',
        unsafe_allow_html=True,
    )


def seccion(texto: str) -> None:
    st.markdown(f'<div class="itc-seccion">{texto}</div>', unsafe_allow_html=True)


def pie() -> None:
    st.markdown(
        '<div class="itc-pie"><div><b>ITC DEPORTES</b><br>'
        "© 2026 · Sistema de gestión deportiva</div>"
        "<div>Tabla · Calendario · Cuadro · Equipos</div></div>",
        unsafe_allow_html=True,
    )
