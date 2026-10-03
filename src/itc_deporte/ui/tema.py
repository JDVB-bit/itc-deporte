"""Los dos temas de la aplicación.

Ambos son oscuros a propósito: `st.dataframe` se dibuja en un canvas que toma
sus colores de `.streamlit/config.toml` y no se puede tematizar con CSS, así
que una tabla oscura sobre una página clara sería ilegible.

El fallo anterior era que solo se cambiaba el fondo de la página. Los inputs,
selectores, pestañas, popovers y botones seguían con los colores del config, y
al alternar a "verde" quedaban superficies negras con texto crema sobre verde.
Ahora cada tema define una paleta completa como variables CSS y todos los
widgets de Streamlit la usan.

Contrastes (WCAG AA = 4.5:1 en texto): `tx`, `tx2` y `tx3` superan 5:1 sobre
`bg` y `bgc` en los dos temas, y `aco` (texto sobre botones de acento) supera 9:1.
"""

from __future__ import annotations

import html

import streamlit as st

TEMAS = {
    "oscuro": dict(
        ac="#F5B800", achi="#FFD54A", aco="#1A1200",
        bg="#0B0B10", bgc="#16161E", bga="#1F1F2A", bgs="#241C06",
        tx="#F7F2E9", tx2="#BDB5A5", tx3="#8F887B", sbg="#07070B",
        grad="linear-gradient(135deg,#1A1405 0%,#2E2206 50%,#14110A 100%)",
        ico="🌿", lbl="Cambiar a tema verde",
    ),
    "verde": dict(
        ac="#5FDB4A", achi="#9BF08A", aco="#04140A",
        bg="#07140C", bgc="#0F2217", bga="#163020", bgs="#12301F",
        tx="#EAF8E4", tx2="#B2D6A8", tx3="#86AB7E", sbg="#040C07",
        grad="linear-gradient(135deg,#06150A 0%,#0F3220 50%,#07140C 100%)",
        ico="✨", lbl="Cambiar a tema dorado",
    ),
}

_COLORES = ("ac", "achi", "aco", "bg", "bgc", "bga", "bgs", "tx", "tx2", "tx3", "sbg", "grad")


def actual() -> dict:
    return TEMAS[st.session_state.get("tema", "oscuro")]


def alternar() -> None:
    st.session_state.tema = "verde" if actual() is TEMAS["oscuro"] else "oscuro"


_FUENTES = (
    "@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue"
    "&family=Outfit:wght@400;500;600;700&display=swap');"
)

_ESTILO = """
:root{
  --brd:color-mix(in srgb,var(--ac) 28%,transparent);
  --brd-suave:color-mix(in srgb,var(--ac) 14%,transparent);
  --brillo:color-mix(in srgb,var(--ac) 35%,transparent);
  --radio:14px;
}

/* ── Base y fondo ─────────────────────────────────────────────────────── */
.stApp{
  background:
    radial-gradient(900px 500px at 88% -8%,color-mix(in srgb,var(--ac) 16%,transparent),transparent 60%),
    radial-gradient(700px 420px at -8% 35%,color-mix(in srgb,var(--ac) 9%,transparent),transparent 55%),
    var(--bg);
  background-attachment:fixed;
  color:var(--tx);
  font-family:'Outfit',system-ui,sans-serif;
}
[data-testid="stHeader"]{background:transparent;}
.stApp h1,.stApp h2,.stApp h3{color:var(--ac);}
.stApp h2{font-family:'Bebas Neue',Impact,sans-serif;font-weight:400;letter-spacing:2px;font-size:2.1rem;}
[data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li{color:var(--tx);}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p{color:var(--tx2);}
.stApp label,.stApp label p,[data-testid="stWidgetLabel"] p{color:var(--tx2);}
.stApp hr{border-color:var(--brd-suave);}

/* ── Barra lateral ────────────────────────────────────────────────────── */
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg,var(--sbg),var(--bg));
  border-right:1px solid var(--brd-suave);
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label{
  background:var(--bgc);border:1px solid var(--brd-suave);border-radius:12px;
  padding:8px 12px;margin-bottom:6px;width:100%;transition:all .18s ease;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label p{color:var(--tx);}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{
  border-color:var(--ac);transform:translateX(4px);
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked){
  background:linear-gradient(90deg,color-mix(in srgb,var(--ac) 24%,var(--bgc)),var(--bgc));
  border-color:var(--ac);box-shadow:0 0 18px color-mix(in srgb,var(--ac) 22%,transparent);
}

/* ── Botones ──────────────────────────────────────────────────────────── */
div[data-testid="stButton"] button,
div[data-testid="stFormSubmitButton"] button{
  background:var(--bgc);color:var(--tx);border:1px solid var(--brd);
  border-radius:12px;font-weight:600;transition:all .18s ease;
}
div[data-testid="stButton"] button p,
div[data-testid="stFormSubmitButton"] button p{color:inherit;}
div[data-testid="stButton"] button:hover:not(:disabled),
div[data-testid="stFormSubmitButton"] button:hover:not(:disabled){
  background:linear-gradient(135deg,var(--ac),var(--achi));color:var(--aco);
  border-color:var(--ac);transform:translateY(-2px);
  box-shadow:0 8px 22px var(--brillo);
}
div[data-testid="stButton"] button:active:not(:disabled),
div[data-testid="stFormSubmitButton"] button:active:not(:disabled){transform:translateY(0) scale(.98);}
div[data-testid="stFormSubmitButton"] button{
  background:linear-gradient(135deg,var(--ac),var(--achi));color:var(--aco);border-color:var(--ac);
}
div[data-testid="stButton"] button:disabled{
  background:color-mix(in srgb,var(--ac) 14%,var(--bgc));color:var(--ac);
  border-color:var(--ac);opacity:1;cursor:default;
}

/* ── Pestañas en píldora ──────────────────────────────────────────────── */
[data-baseweb="tab-list"]{gap:8px;flex-wrap:wrap;border-bottom:none;padding-bottom:6px;}
[data-baseweb="tab-highlight"],[data-baseweb="tab-border"]{display:none;}
button[data-baseweb="tab"]{
  background:var(--bgc);border:1px solid var(--brd-suave);border-radius:999px;
  padding:8px 18px;color:var(--tx2);transition:all .18s ease;
}
button[data-baseweb="tab"] p{color:inherit;font-weight:600;}
button[data-baseweb="tab"]:hover{border-color:var(--ac);color:var(--tx);transform:translateY(-1px);}
button[data-baseweb="tab"][aria-selected="true"]{
  background:linear-gradient(135deg,var(--ac),var(--achi));color:var(--aco);
  border-color:var(--ac);box-shadow:0 6px 18px var(--brillo);
}
div[data-baseweb="tab-panel"]{animation:itc-entrar .4s ease both;}

/* ── Inputs, selectores y calendarios ─────────────────────────────────── */
[data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="textarea"],
[data-baseweb="select"]>div{
  background:var(--bga);border-color:var(--brd-suave);border-radius:10px;color:var(--tx);
}
[data-baseweb="input"]:focus-within,[data-baseweb="select"]>div:focus-within{
  border-color:var(--ac);box-shadow:0 0 0 2px var(--brillo);
}
.stApp input,.stApp textarea{color:var(--tx);-webkit-text-fill-color:var(--tx);}
.stApp input::placeholder,.stApp textarea::placeholder{color:var(--tx3);-webkit-text-fill-color:var(--tx3);}
[data-baseweb="select"] svg,[data-testid="stNumberInput"] button{color:var(--tx2);}
[data-baseweb="popover"] [data-baseweb="menu"],[data-baseweb="popover"] ul,
[data-baseweb="calendar"]{background:var(--bgc);color:var(--tx);}
[data-baseweb="popover"] li{color:var(--tx);}
[data-baseweb="popover"] li:hover,[data-baseweb="popover"] li[aria-selected="true"]{background:var(--bga);}
[data-testid="stPopoverBody"]{background:var(--bgc);border:1px solid var(--brd);border-radius:var(--radio);}

/* ── Expanders, tablas y avisos ───────────────────────────────────────── */
[data-testid="stExpander"] details{
  background:var(--bgc);border:1px solid var(--brd-suave);border-radius:var(--radio);
  transition:border-color .18s ease;
}
[data-testid="stExpander"] details:hover{border-color:var(--brd);}
[data-testid="stExpander"] summary,[data-testid="stExpander"] summary p{color:var(--tx);font-weight:600;}
[data-testid="stDataFrame"]{
  border:1px solid var(--brd);border-radius:var(--radio);overflow:hidden;
  box-shadow:0 10px 30px rgba(0,0,0,.35);
}
[data-testid="stAlert"]{border-radius:var(--radio);border:1px solid var(--brd-suave);}
[data-testid="stAlert"] p{color:var(--tx);}

/* ── Componentes propios ──────────────────────────────────────────────── */
.itc-hero{
  position:relative;overflow:hidden;
  background:var(--grad);background-size:220% 220%;animation:itc-flujo 14s ease infinite;
  border-left:6px solid var(--ac);border-radius:0 18px 18px 0;
  padding:22px 26px;margin-bottom:20px;
  box-shadow:0 14px 44px color-mix(in srgb,var(--ac) 16%,transparent);
}
.itc-hero::after{
  content:"⚽ 🏀 🏐 🤾";position:absolute;right:22px;top:50%;
  font-size:1.8rem;letter-spacing:6px;animation:itc-flotar 4s ease-in-out infinite;
}
.itc-titulo{
  font-family:'Bebas Neue',Impact,sans-serif;font-size:2.8rem;color:var(--ac);
  letter-spacing:5px;line-height:1.05;text-shadow:0 0 28px var(--brillo);
}
.itc-sub{color:var(--tx2);font-size:.9rem;margin-top:4px;}
.itc-seccion{
  display:flex;align-items:center;gap:10px;color:var(--ac);font-size:.8rem;
  letter-spacing:2px;text-transform:uppercase;margin:20px 0 10px;font-weight:700;
}
.itc-seccion::after{content:"";flex:1;height:1px;background:linear-gradient(90deg,var(--brd),transparent);}
.itc-tarjeta{
  background:var(--bgc);border-left:3px solid var(--tx3);padding:10px 14px;
  margin-bottom:8px;border-radius:0 12px 12px 0;transition:all .18s ease;
}
.itc-tarjeta:hover{transform:translateX(4px);background:var(--bga);}
.itc-tarjeta.jugado{border-left-color:var(--ac);}
.itc-marcador{
  display:inline-block;min-width:78px;text-align:center;
  font-family:'Bebas Neue',Impact,sans-serif;font-size:1.6rem;letter-spacing:3px;
  color:var(--achi);background:var(--bga);border:1px solid var(--brd);
  border-radius:10px;padding:0 12px;text-shadow:0 0 14px var(--brillo);
}
.itc-casilla{
  background:var(--bgc);border:1px solid var(--brd-suave);border-radius:12px;
  padding:10px 14px;margin-bottom:10px;font-size:.88rem;color:var(--tx);
  transition:all .18s ease;
}
.itc-casilla:hover{transform:translateY(-3px);border-color:var(--brd);box-shadow:0 8px 20px rgba(0,0,0,.35);}
.itc-casilla.ganador{
  border-color:var(--ac);color:var(--achi);
  background:linear-gradient(135deg,color-mix(in srgb,var(--ac) 16%,var(--bgc)),var(--bgc));
  animation:itc-pulso 2.8s ease-in-out infinite;
}
.itc-vacia{color:var(--tx3);font-style:italic;}
.itc-campeon{
  display:flex;align-items:center;gap:18px;padding:18px 24px;margin:6px 0 18px;
  border-radius:18px;color:var(--aco);
  background:linear-gradient(110deg,var(--ac),var(--achi),var(--ac));background-size:220% 100%;
  animation:itc-brillo 5s linear infinite;box-shadow:0 14px 40px var(--brillo);
}
.itc-copa{font-size:3rem;animation:itc-rebote 1.8s ease-in-out infinite;}
.itc-campeon-et{font-size:.8rem;letter-spacing:3px;text-transform:uppercase;font-weight:700;opacity:.8;}
.itc-campeon-nom{font-family:'Bebas Neue',Impact,sans-serif;font-size:2.4rem;letter-spacing:3px;line-height:1;}

/* ── Animaciones ──────────────────────────────────────────────────────── */
@keyframes itc-entrar{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
@keyframes itc-flujo{0%,100%{background-position:0% 50%}50%{background-position:100% 50%}}
@keyframes itc-flotar{0%,100%{transform:translateY(-50%)}50%{transform:translateY(-62%)}}
@keyframes itc-pulso{0%,100%{box-shadow:0 0 0 0 transparent}50%{box-shadow:0 0 22px var(--brillo)}}
@keyframes itc-brillo{from{background-position:0% 0}to{background-position:220% 0}}
@keyframes itc-rebote{0%,100%{transform:translateY(0) rotate(-6deg)}50%{transform:translateY(-8px) rotate(6deg)}}
@media (max-width:700px){.itc-hero::after{display:none}.itc-titulo{font-size:2.1rem}}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""


def _variables(t: dict) -> str:
    return ":root{" + ";".join(f"--{k}:{t[k]}" for k in _COLORES) + "}"


def aplicar() -> None:
    css = _FUENTES + _variables(actual()) + _ESTILO
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def hero(titulo: str, subtitulo: str) -> None:
    st.markdown(
        f'<div class="itc-hero"><div class="itc-titulo">{titulo}</div>'
        f'<div class="itc-sub">{subtitulo}</div></div>',
        unsafe_allow_html=True,
    )


def seccion(texto: str) -> None:
    st.markdown(f'<div class="itc-seccion">{texto}</div>', unsafe_allow_html=True)


def campeon(nombre: str) -> None:
    """Banner del campeón, con la copa rebotando y un brillo que lo recorre."""
    st.markdown(
        '<div class="itc-campeon"><span class="itc-copa">🏆</span><div>'
        '<div class="itc-campeon-et">Campeón</div>'
        f'<div class="itc-campeon-nom">{html.escape(nombre)}</div></div></div>',
        unsafe_allow_html=True,
    )
