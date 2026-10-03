"""Identidad visual de ITC Deportes: una noche de torneo bajo los focos.

Dos temas, los dos oscuros a propósito: `st.dataframe` se dibuja en un canvas
que toma sus colores de `.streamlit/config.toml` y no se puede tematizar con
CSS. Cada tema es una paleta completa en variables CSS que usan todos los
widgets, y la maqueta es responsiva (tablet < 900px, móvil < 640px).

Contraste: `tx`, `tx2` y `tx3` superan 5:1 sobre sus superficies; `aco`, el
texto sobre el degradado de marca, supera 6:1.
"""

from __future__ import annotations

import html

import streamlit as st

TEMAS = {
    "oscuro": dict(  # Noche: índigo profundo con degradado rosa → naranja → oro
        g1="#FF4D8D", g2="#FF9A3D", g3="#FFD23F", ac="#FFB02E", achi="#FFD23F",
        aco="#1B0B1F", bg="#0A0B1E", bgc="#14163A", bga="#1F2257", bgs="#0D0F2B",
        tx="#F4F5FF", tx2="#B9BCE6", tx3="#8E92C9", sbg="#070817",
        malla="#3B1A6B", ico="🌿", lbl="Cambiar a tema cancha",
    ),
    "verde": dict(  # Cancha: verde petróleo con degradado turquesa → lima
        g1="#00D4A0", g2="#7BE04A", g3="#D8F43C", ac="#7BE04A", achi="#D8F43C",
        aco="#03181A", bg="#04161A", bgc="#0B2A2C", bga="#11393A", bgs="#071F22",
        tx="#EAFBF5", tx2="#A9DCCB", tx3="#7FB8A5", sbg="#030F12",
        malla="#0B5A4A", ico="🌙", lbl="Cambiar a tema noche",
    ),
}

_COLORES = ("g1", "g2", "g3", "ac", "achi", "aco", "bg", "bgc", "bga", "bgs",
            "tx", "tx2", "tx3", "sbg", "malla")


def actual() -> dict:
    return TEMAS[st.session_state.get("tema", "oscuro")]


def alternar() -> None:
    st.session_state.tema = "verde" if actual() is TEMAS["oscuro"] else "oscuro"


_FUENTES = (
    "@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:ital,wght@1,700;1,800"
    "&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');"
)

_ESTILO = """
:root{
  --marca:linear-gradient(120deg,var(--g1),var(--g2) 55%,var(--g3));
  --brd:color-mix(in srgb,var(--g2) 30%,transparent);
  --brd2:color-mix(in srgb,var(--tx) 10%,transparent);
  --glow:color-mix(in srgb,var(--g2) 40%,transparent);
  --vidrio:color-mix(in srgb,var(--bgc) 72%,transparent);
  --display:'Barlow Condensed',Impact,sans-serif;
}

/* ── Lienzo ───────────────────────────────────────────────────────────── */
.stApp{
  background:
    radial-gradient(1000px 600px at 90% -10%,color-mix(in srgb,var(--g1) 30%,transparent),transparent 60%),
    radial-gradient(800px 600px at -10% 20%,var(--malla),transparent 62%),
    radial-gradient(700px 500px at 60% 110%,color-mix(in srgb,var(--g3) 14%,transparent),transparent 60%),
    var(--bg);
  background-attachment:fixed;color:var(--tx);
  font-family:'Plus Jakarta Sans',system-ui,sans-serif;
}
[data-testid="stHeader"]{background:transparent;}
.block-container{max-width:1180px;padding-top:2.2rem;}
.stApp h1,.stApp h2,.stApp h3{color:var(--tx);}
.stApp h2{font-family:var(--display);font-style:italic;font-weight:800;font-size:2.4rem;letter-spacing:.5px;
  background:var(--marca);-webkit-background-clip:text;background-clip:text;color:transparent;display:inline-block;}
[data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li{color:var(--tx);}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p{color:var(--tx2);}
.stApp label,.stApp label p,[data-testid="stWidgetLabel"] p{color:var(--tx2);font-weight:500;}
.stApp hr{border-color:var(--brd2);}

/* ── Barra lateral ────────────────────────────────────────────────────── */
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg,var(--sbg),var(--bgs) 60%,color-mix(in srgb,var(--malla) 55%,var(--sbg)));
  border-right:1px solid var(--brd2);
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label{
  background:var(--vidrio);border:1px solid var(--brd2);border-radius:14px;
  padding:10px 14px;margin-bottom:8px;width:100%;transition:transform .2s,border-color .2s,box-shadow .2s;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label p{color:var(--tx);font-weight:600;}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{border-color:var(--g2);transform:translateX(4px);}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked){
  background:linear-gradient(120deg,color-mix(in srgb,var(--g1) 34%,var(--bgc)),color-mix(in srgb,var(--g3) 22%,var(--bgc)));
  border-color:var(--g2);box-shadow:0 8px 26px var(--glow);
}

/* ── Botones ──────────────────────────────────────────────────────────── */
div[data-testid="stButton"] button,div[data-testid="stFormSubmitButton"] button{
  min-height:46px;background:var(--vidrio);color:var(--tx);border:1px solid var(--brd);
  border-radius:14px;font-weight:700;backdrop-filter:blur(8px);transition:transform .2s,box-shadow .2s,background .2s;
}
div[data-testid="stButton"] button p,div[data-testid="stFormSubmitButton"] button p{color:inherit;}
div[data-testid="stButton"] button:hover:not(:disabled),div[data-testid="stFormSubmitButton"] button:hover:not(:disabled){
  background:var(--marca);color:var(--aco);border-color:transparent;transform:translateY(-2px);box-shadow:0 10px 28px var(--glow);
}
div[data-testid="stButton"] button:active:not(:disabled),div[data-testid="stFormSubmitButton"] button:active:not(:disabled){transform:scale(.97);}
div[data-testid="stFormSubmitButton"] button{background:var(--marca);color:var(--aco);border-color:transparent;box-shadow:0 8px 22px var(--glow);}
div[data-testid="stButton"] button:disabled{background:color-mix(in srgb,var(--g2) 16%,var(--bgc));color:var(--achi);border-color:var(--g2);opacity:1;}
.stApp button:focus-visible,.stApp input:focus-visible{outline:2px solid var(--g3);outline-offset:2px;}

/* ── Pestañas ─────────────────────────────────────────────────────────── */
[data-baseweb="tab-list"]{gap:8px;border-bottom:none;padding:4px 2px 10px;overflow-x:auto;scrollbar-width:none;}
[data-baseweb="tab-list"]::-webkit-scrollbar{display:none;}
[data-baseweb="tab-highlight"],[data-baseweb="tab-border"]{display:none;}
button[data-baseweb="tab"]{
  flex:0 0 auto;background:var(--vidrio);border:1px solid var(--brd2);border-radius:999px;
  padding:10px 20px;color:var(--tx2);transition:all .2s;
}
button[data-baseweb="tab"] p{color:inherit;font-weight:700;}
button[data-baseweb="tab"]:hover{border-color:var(--g2);color:var(--tx);}
button[data-baseweb="tab"][aria-selected="true"]{background:var(--marca);color:var(--aco);border-color:transparent;box-shadow:0 8px 24px var(--glow);}
div[data-baseweb="tab-panel"]{animation:itc-entrar .45s ease both;}

/* ── Inputs ───────────────────────────────────────────────────────────── */
[data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="textarea"],[data-baseweb="select"]>div{
  background:var(--bga);border-color:var(--brd2);border-radius:12px;color:var(--tx);
}
[data-baseweb="input"]:focus-within,[data-baseweb="select"]>div:focus-within{border-color:var(--g2);box-shadow:0 0 0 3px var(--glow);}
.stApp input,.stApp textarea{color:var(--tx);-webkit-text-fill-color:var(--tx);}
.stApp input::placeholder,.stApp textarea::placeholder{color:var(--tx3);-webkit-text-fill-color:var(--tx3);}
[data-baseweb="select"] svg,[data-testid="stNumberInput"] button{color:var(--tx2);}
[data-baseweb="popover"] [data-baseweb="menu"],[data-baseweb="popover"] ul,[data-baseweb="calendar"]{background:var(--bgc);color:var(--tx);}
[data-baseweb="popover"] li{color:var(--tx);}
[data-baseweb="popover"] li:hover,[data-baseweb="popover"] li[aria-selected="true"]{background:var(--bga);}
[data-testid="stPopoverBody"]{background:var(--bgc);border:1px solid var(--brd);border-radius:16px;box-shadow:0 20px 50px rgba(0,0,0,.5);}

/* ── Contenedores nativos ─────────────────────────────────────────────── */
[data-testid="stExpander"] details{background:var(--vidrio);border:1px solid var(--brd2);border-radius:16px;backdrop-filter:blur(8px);}
[data-testid="stExpander"] details[open]{border-color:var(--brd);}
[data-testid="stExpander"] summary,[data-testid="stExpander"] summary p{color:var(--tx);font-weight:700;}
[data-testid="stDataFrame"]{border:1px solid var(--brd);border-radius:16px;overflow:hidden;box-shadow:0 14px 40px rgba(0,0,0,.4);}
[data-testid="stAlert"]{border-radius:16px;border:1px solid var(--brd2);backdrop-filter:blur(8px);}
[data-testid="stAlert"] p{color:var(--tx);}
[data-testid="stForm"]{background:var(--vidrio);border:1px solid var(--brd2);border-radius:20px;padding:1.2rem;backdrop-filter:blur(10px);}

/* ── Hero ─────────────────────────────────────────────────────────────── */
.itc-hero{
  position:relative;overflow:hidden;border-radius:28px;padding:clamp(22px,4vw,44px);margin-bottom:26px;
  background:
    radial-gradient(500px 260px at 100% 0%,color-mix(in srgb,var(--g1) 55%,transparent),transparent 70%),
    radial-gradient(420px 260px at 0% 100%,color-mix(in srgb,var(--g3) 28%,transparent),transparent 70%),
    linear-gradient(135deg,var(--bgc),var(--bga));
  border:1px solid var(--brd);box-shadow:0 24px 70px color-mix(in srgb,var(--g1) 22%,transparent);
  animation:itc-entrar .7s ease both;
}
.itc-hero::before{ /* líneas de cancha */
  content:"";position:absolute;right:-60px;top:-60px;width:300px;height:300px;border-radius:50%;
  border:2px solid color-mix(in srgb,var(--tx) 14%,transparent);box-shadow:0 0 0 38px color-mix(in srgb,var(--tx) 5%,transparent);
}
.itc-hero::after{content:"⚽";position:absolute;right:clamp(14px,5vw,60px);bottom:14px;font-size:clamp(2.4rem,7vw,4.6rem);animation:itc-rodar 6s ease-in-out infinite;}
.itc-titulo{
  position:relative;font-family:var(--display);font-style:italic;font-weight:800;line-height:.95;
  font-size:clamp(2.6rem,9vw,5.2rem);letter-spacing:1px;
  background:var(--marca);-webkit-background-clip:text;background-clip:text;color:transparent;
}
.itc-sub{position:relative;color:var(--tx2);font-size:clamp(.9rem,2.4vw,1.05rem);margin-top:10px;max-width:46ch;}
.itc-chips{position:relative;display:flex;flex-wrap:wrap;gap:8px;margin-top:18px;}
.itc-chip{background:color-mix(in srgb,var(--tx) 10%,transparent);border:1px solid var(--brd2);border-radius:999px;
  padding:6px 14px;font-size:.85rem;font-weight:600;color:var(--tx);backdrop-filter:blur(6px);}

/* ── Secciones, partidos, cuadro ──────────────────────────────────────── */
.itc-seccion{display:flex;align-items:center;gap:12px;color:var(--tx);font-size:1.05rem;font-weight:700;margin:26px 0 12px;}
.itc-seccion::before{content:"";width:6px;height:22px;border-radius:4px;background:var(--marca);}
.itc-seccion::after{content:"";flex:1;height:1px;background:linear-gradient(90deg,var(--brd),transparent);}
.itc-tarjeta{background:var(--vidrio);border:1px solid var(--brd2);border-left:4px solid var(--tx3);padding:12px 16px;margin-bottom:8px;border-radius:14px;}
.itc-tarjeta.jugado{border-left-color:var(--g2);}
.itc-marcador{display:inline-block;min-width:84px;text-align:center;font-family:var(--display);font-style:italic;font-weight:800;
  font-size:1.9rem;line-height:1.2;padding:0 14px;border-radius:12px;color:var(--aco);background:var(--marca);box-shadow:0 6px 18px var(--glow);}
.itc-vacia{color:var(--tx3);font-style:italic;}
.itc-partido{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:14px;background:var(--vidrio);
  border:1px solid var(--brd2);border-radius:18px;padding:12px 18px;margin-bottom:8px;backdrop-filter:blur(8px);}
.itc-partido .eq{font-weight:700;font-size:1.02rem;overflow-wrap:anywhere;}
.itc-partido .eq.v{text-align:right;}
.itc-partido .vs{min-width:84px;text-align:center;color:var(--tx3);font-weight:700;}
.itc-casilla{background:var(--vidrio);border:1px solid var(--brd2);border-radius:16px;padding:12px 16px;margin-bottom:10px;
  font-size:.92rem;color:var(--tx);backdrop-filter:blur(8px);transition:transform .2s,border-color .2s,box-shadow .2s;}
.itc-casilla:hover{transform:translateY(-3px);border-color:var(--brd);box-shadow:0 12px 28px rgba(0,0,0,.4);}
.itc-casilla.ganador{border-color:var(--g2);background:linear-gradient(135deg,color-mix(in srgb,var(--g2) 22%,var(--bgc)),var(--bgc));
  color:var(--achi);box-shadow:0 0 26px var(--glow);}

/* ── Podio y campeón ──────────────────────────────────────────────────── */
.itc-podio{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;align-items:end;margin:6px 0 20px;}
.itc-puesto{border-radius:20px 20px 12px 12px;padding:14px 10px;text-align:center;border:1px solid var(--brd2);
  background:linear-gradient(180deg,color-mix(in srgb,var(--g2) 24%,var(--bgc)),var(--bgc));}
.itc-puesto.p1{min-height:170px;border-color:var(--g3);background:var(--marca);color:var(--aco);box-shadow:0 18px 44px var(--glow);}
.itc-puesto.p2{min-height:132px;}.itc-puesto.p3{min-height:108px;}
.itc-puesto .med{font-size:2rem;}
.itc-puesto .nom{font-weight:800;overflow-wrap:anywhere;}
.itc-puesto .pts{font-family:var(--display);font-style:italic;font-weight:800;font-size:1.7rem;}
.itc-campeon{display:flex;align-items:center;gap:18px;padding:20px 26px;margin:6px 0 20px;border-radius:24px;color:var(--aco);
  background:linear-gradient(110deg,var(--g1),var(--g2),var(--g3),var(--g2),var(--g1));background-size:240% 100%;
  animation:itc-brillo 6s linear infinite;box-shadow:0 18px 50px var(--glow);}
.itc-copa{font-size:3.2rem;animation:itc-rebote 1.8s ease-in-out infinite;}
.itc-campeon-et{font-size:.9rem;font-weight:700;opacity:.85;}
.itc-campeon-nom{font-family:var(--display);font-style:italic;font-weight:800;font-size:clamp(1.8rem,6vw,2.8rem);line-height:1;}

@keyframes itc-entrar{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
@keyframes itc-rodar{0%,100%{transform:translateY(0) rotate(0)}50%{transform:translateY(-14px) rotate(180deg)}}
@keyframes itc-brillo{from{background-position:0 0}to{background-position:240% 0}}
@keyframes itc-rebote{0%,100%{transform:translateY(0) rotate(-6deg)}50%{transform:translateY(-8px) rotate(6deg)}}

/* ── Tablet y móvil ───────────────────────────────────────────────────── */
@media (max-width:900px){
  .block-container{padding:1.4rem 1.1rem 3rem;}
  .stApp h2{font-size:2rem;}
}
@media (max-width:640px){
  .block-container{padding:1rem .8rem 3rem;}
  .itc-hero{border-radius:22px;}
  .itc-hero::before{width:200px;height:200px;right:-70px;top:-70px;}
  .itc-partido{grid-template-columns:1fr;gap:6px;text-align:center;padding:14px;}
  .itc-partido .eq,.itc-partido .eq.v{text-align:center;}
  .itc-partido .vs,.itc-partido .itc-marcador{justify-self:center;}
  .itc-podio{gap:6px;}.itc-puesto{padding:10px 4px;}.itc-puesto .nom{font-size:.8rem;}
  .itc-campeon{padding:16px;gap:12px;border-radius:20px;}.itc-copa{font-size:2.4rem;}
  button[data-baseweb="tab"]{padding:10px 16px;}
  .stApp input,.stApp textarea{font-size:16px;} /* evita el zoom automático de iOS */
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""


def _variables(t: dict) -> str:
    return ":root{" + ";".join(f"--{k}:{t[k]}" for k in _COLORES) + "}"


def aplicar() -> None:
    st.markdown(f"<style>{_FUENTES}{_variables(actual())}{_ESTILO}</style>", unsafe_allow_html=True)


def hero(titulo: str, subtitulo: str, chips: tuple[str, ...] = ()) -> None:
    fichas = "".join(f'<span class="itc-chip">{html.escape(c)}</span>' for c in chips)
    st.markdown(
        f'<div class="itc-hero"><div class="itc-titulo">{titulo}</div>'
        f'<div class="itc-sub">{subtitulo}</div>'
        f'{f"<div class=itc-chips>{fichas}</div>" if fichas else ""}</div>',
        unsafe_allow_html=True,
    )


def seccion(texto: str) -> None:
    st.markdown(f'<div class="itc-seccion">{texto}</div>', unsafe_allow_html=True)


def partido(local: str, visitante: str, marcador=None) -> None:
    """Un cruce como tarjeta: en móvil se apila y sigue legible."""
    centro = (
        f'<div class="itc-marcador">{marcador.local} - {marcador.visitante}</div>'
        if marcador else '<div class="vs">vs</div>'
    )
    st.markdown(
        f'<div class="itc-partido"><div class="eq">{html.escape(local)}</div>{centro}'
        f'<div class="eq v">{html.escape(visitante)}</div></div>',
        unsafe_allow_html=True,
    )


def podio(puestos: list[tuple[str, int]]) -> None:
    """Los tres primeros, con el líder en el centro. `puestos` = [(nombre, puntos)]."""
    if len(puestos) < 3:
        return
    medallas = ("🥇", "🥈", "🥉")
    orden = (1, 0, 2)  # plata, oro, bronce
    celdas = "".join(
        f'<div class="itc-puesto p{i + 1}"><div class="med">{medallas[i]}</div>'
        f'<div class="nom">{html.escape(puestos[i][0])}</div>'
        f'<div class="pts">{puestos[i][1]} pts</div></div>'
        for i in orden
    )
    st.markdown(f'<div class="itc-podio">{celdas}</div>', unsafe_allow_html=True)


def campeon(nombre: str) -> None:
    st.markdown(
        '<div class="itc-campeon"><span class="itc-copa">🏆</span><div>'
        '<div class="itc-campeon-et">Campeón del torneo</div>'
        f'<div class="itc-campeon-nom">{html.escape(nombre)}</div></div></div>',
        unsafe_allow_html=True,
    )
