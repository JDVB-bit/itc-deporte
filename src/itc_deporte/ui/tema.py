"""Identidad visual de ITC Deportes: negro y oro, con una variante verde cancha.

Los dos temas son oscuros a propósito: `st.dataframe` se dibuja en un canvas que
toma sus colores de `.streamlit/config.toml` y no se puede tematizar con CSS.
Cada tema es una paleta completa en variables CSS que usan todos los widgets.

Contraste: `tx`, `tx2` y `tx3` superan 5:1 sobre sus superficies; `aco`, el texto
sobre el degradado de marca, supera 6:1. Responsivo: tablet < 900px, móvil < 640px.
"""

from __future__ import annotations

import html

import streamlit as st

TEMAS = {
    "oscuro": dict(  # Negro y oro
        g1="#FFE08A", g2="#F5B800", g3="#C98A00", ac="#F5B800", achi="#FFD966",
        aco="#1A1200", bg="#070707", bgc="#131313", bga="#1E1B13", bgs="#0D0C08",
        tx="#F8F3E6", tx2="#C9C0A8", tx3="#988F78", sbg="#050505", malla="#2B2007",
        ico="", lbl="Cambiar tema",
    ),
    "verde": dict(  # Cancha: negro verdoso con degradado esmeralda → lima
        g1="#B6F36B", g2="#3DD68C", g3="#12A37A", ac="#3DD68C", achi="#B6F36B",
        aco="#03140C", bg="#050D0A", bgc="#0D1B15", bga="#13291F", bgs="#08130E",
        tx="#EAFBF2", tx2="#A8D8C0", tx3="#78B397", sbg="#030906", malla="#0A3A2A",
        ico="", lbl="Cambiar tema",
    ),
}

_COLORES = ("g1", "g2", "g3", "ac", "achi", "aco", "bg", "bgc", "bga", "bgs",
            "tx", "tx2", "tx3", "sbg", "malla")


def actual() -> dict:
    return TEMAS[st.session_state.get("tema", "oscuro")]


def alternar() -> None:
    st.session_state.tema = "verde" if actual() is TEMAS["oscuro"] else "oscuro"


_FUENTES = (
    "@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700"
    "&family=DM+Sans:wght@400;500;600;700&display=swap');"
)

_ESTILO = """
:root{
  --marca:linear-gradient(120deg,var(--g1),var(--g2) 55%,var(--g3));
  --brd:color-mix(in srgb,var(--g2) 32%,transparent);
  --brd2:color-mix(in srgb,var(--tx) 10%,transparent);
  --glow:color-mix(in srgb,var(--g2) 38%,transparent);
  --ln:color-mix(in srgb,var(--g2) 60%,transparent);
  --vidrio:color-mix(in srgb,var(--bgc) 80%,transparent);
  --display:'Oswald',Impact,sans-serif;
}
.stApp{
  background:
    radial-gradient(900px 520px at 92% -8%,color-mix(in srgb,var(--g2) 20%,transparent),transparent 62%),
    radial-gradient(760px 560px at -8% 28%,var(--malla),transparent 64%),
    radial-gradient(700px 420px at 55% 112%,color-mix(in srgb,var(--g3) 14%,transparent),transparent 60%),
    var(--bg);
  background-attachment:fixed;color:var(--tx);font-family:'DM Sans',system-ui,sans-serif;
}
[data-testid="stHeader"]{background:transparent;}
.block-container{max-width:1200px;padding-top:2.2rem;}
.stApp h1,.stApp h2,.stApp h3{color:var(--tx);font-family:var(--display);font-weight:600;letter-spacing:.3px;}
.stApp h2{font-size:2.2rem;background:var(--marca);-webkit-background-clip:text;background-clip:text;color:transparent;display:inline-block;}
[data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li{color:var(--tx);}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p{color:var(--tx2);}
.stApp label,.stApp label p,[data-testid="stWidgetLabel"] p{color:var(--tx2);font-weight:500;}
.stApp hr{border-color:var(--brd2);}

/* Barra lateral */
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg,var(--sbg),var(--bgs) 65%,color-mix(in srgb,var(--malla) 60%,var(--sbg)));
  border-right:1px solid var(--brd);
}
section[data-testid="stSidebar"] [data-testid="stImage"] img{border-radius:18px;box-shadow:0 10px 34px var(--glow);}
section[data-testid="stSidebar"] [data-testid="stRadio"] label{
  background:var(--vidrio);border:1px solid var(--brd2);border-radius:14px;padding:10px 14px;margin-bottom:8px;
  width:100%;transition:transform .2s,border-color .2s,box-shadow .2s;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label p{color:var(--tx);font-weight:600;}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{border-color:var(--g2);transform:translateX(4px);}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked){
  background:linear-gradient(120deg,color-mix(in srgb,var(--g2) 30%,var(--bgc)),var(--bgc));
  border-color:var(--g2);box-shadow:0 8px 26px var(--glow);
}

/* Botones */
div[data-testid="stButton"] button,div[data-testid="stFormSubmitButton"] button{
  min-height:46px;background:var(--vidrio);color:var(--tx);border:1px solid var(--brd);border-radius:14px;
  font-weight:700;transition:transform .2s,box-shadow .2s,background .2s;
}
div[data-testid="stButton"] button p,div[data-testid="stFormSubmitButton"] button p{color:inherit;}
div[data-testid="stButton"] button:hover:not(:disabled),div[data-testid="stFormSubmitButton"] button:hover:not(:disabled){
  background:var(--marca);color:var(--aco);border-color:transparent;transform:translateY(-2px);box-shadow:0 10px 28px var(--glow);
}
div[data-testid="stButton"] button:active:not(:disabled),div[data-testid="stFormSubmitButton"] button:active:not(:disabled){transform:scale(.97);}
div[data-testid="stFormSubmitButton"] button{background:var(--marca);color:var(--aco);border-color:transparent;box-shadow:0 8px 22px var(--glow);}
div[data-testid="stButton"] button:disabled{background:color-mix(in srgb,var(--g2) 16%,var(--bgc));color:var(--achi);border-color:var(--g2);opacity:1;}
.stApp button:focus-visible,.stApp input:focus-visible{outline:2px solid var(--g1);outline-offset:2px;}

/* Pestañas */
[data-baseweb="tab-list"]{gap:8px;border-bottom:none;padding:4px 2px 10px;overflow-x:auto;scrollbar-width:none;}
[data-baseweb="tab-list"]::-webkit-scrollbar{display:none;}
[data-baseweb="tab-highlight"],[data-baseweb="tab-border"]{display:none;}
button[data-baseweb="tab"]{flex:0 0 auto;background:var(--vidrio);border:1px solid var(--brd2);border-radius:999px;padding:10px 20px;color:var(--tx2);transition:all .2s;}
button[data-baseweb="tab"] p{color:inherit;font-weight:700;}
button[data-baseweb="tab"]:hover{border-color:var(--g2);color:var(--tx);}
button[data-baseweb="tab"][aria-selected="true"]{background:var(--marca);color:var(--aco);border-color:transparent;box-shadow:0 8px 24px var(--glow);}
div[data-baseweb="tab-panel"]{animation:itc-entrar .45s ease both;}

/* Inputs y contenedores nativos */
[data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="textarea"],[data-baseweb="select"]>div{background:var(--bga);border-color:var(--brd2);border-radius:12px;color:var(--tx);}
[data-baseweb="input"]:focus-within,[data-baseweb="select"]>div:focus-within{border-color:var(--g2);box-shadow:0 0 0 3px var(--glow);}
.stApp input,.stApp textarea{color:var(--tx);-webkit-text-fill-color:var(--tx);}
.stApp input::placeholder,.stApp textarea::placeholder{color:var(--tx3);-webkit-text-fill-color:var(--tx3);}
[data-baseweb="select"] svg,[data-testid="stNumberInput"] button{color:var(--tx2);}
[data-baseweb="popover"] [data-baseweb="menu"],[data-baseweb="popover"] ul,[data-baseweb="calendar"]{background:var(--bgc);color:var(--tx);}
[data-baseweb="popover"] li{color:var(--tx);}
[data-baseweb="popover"] li:hover,[data-baseweb="popover"] li[aria-selected="true"]{background:var(--bga);}
[data-testid="stPopoverBody"]{background:var(--bgc);border:1px solid var(--brd);border-radius:16px;box-shadow:0 20px 50px rgba(0,0,0,.6);}
[data-testid="stExpander"] details{background:var(--vidrio);border:1px solid var(--brd2);border-radius:16px;}
[data-testid="stExpander"] details[open]{border-color:var(--brd);}
[data-testid="stExpander"] summary,[data-testid="stExpander"] summary p{color:var(--tx);font-weight:700;}
[data-testid="stDataFrame"]{border:1px solid var(--brd);border-radius:16px;overflow:hidden;}
[data-testid="stAlert"]{border-radius:16px;border:1px solid var(--brd2);}
[data-testid="stAlert"] p{color:var(--tx);}
[data-testid="stForm"]{background:var(--vidrio);border:1px solid var(--brd2);border-radius:20px;padding:1.2rem;}

/* Hero */
.itc-hero{
  position:relative;overflow:hidden;border-radius:26px;padding:clamp(22px,4vw,42px);margin-bottom:26px;
  background:
    radial-gradient(520px 260px at 100% 0%,color-mix(in srgb,var(--g2) 34%,transparent),transparent 70%),
    radial-gradient(420px 240px at 0% 100%,color-mix(in srgb,var(--g3) 22%,transparent),transparent 70%),
    linear-gradient(135deg,var(--bgc),var(--bga));
  border:1px solid var(--brd);box-shadow:0 24px 70px color-mix(in srgb,var(--g2) 18%,transparent),inset 0 1px 0 rgba(255,255,255,.07);
  animation:itc-entrar .6s ease both;
}
.itc-hero::before{content:"";position:absolute;left:0;top:0;right:0;height:3px;background:var(--marca);}
.itc-hero::after{ /* un solo destello al cargar */
  content:"";position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(115deg,transparent 35%,color-mix(in srgb,var(--g1) 22%,transparent) 48%,transparent 60%);
  background-size:250% 100%;background-position:150% 0;animation:itc-barrido 1.6s ease .4s 1 both;
}
.itc-titulo{position:relative;font-family:var(--display);font-weight:700;line-height:1;font-size:clamp(2.4rem,8vw,4.6rem);
  letter-spacing:2px;background:var(--marca);-webkit-background-clip:text;background-clip:text;color:transparent;}
.itc-sub{position:relative;color:var(--tx2);font-size:clamp(.92rem,2.4vw,1.05rem);margin-top:10px;}
.itc-chips{position:relative;display:flex;flex-wrap:wrap;gap:8px;margin-top:18px;}
.itc-chip{background:color-mix(in srgb,var(--g2) 12%,transparent);border:1px solid var(--brd);border-radius:999px;padding:6px 14px;font-size:.85rem;font-weight:600;color:var(--achi);}

/* Secciones, partidos y banner */
.itc-seccion{display:flex;align-items:center;gap:12px;color:var(--tx);font-family:var(--display);font-size:1.2rem;font-weight:600;margin:26px 0 12px;}
.itc-seccion::before{content:"";width:6px;height:22px;border-radius:4px;background:var(--marca);}
.itc-seccion::after{content:"";flex:1;height:1px;background:linear-gradient(90deg,var(--brd),transparent);}
.itc-marcador{display:inline-block;min-width:84px;text-align:center;font-family:var(--display);font-weight:700;font-size:1.7rem;line-height:1.25;padding:0 14px;border-radius:12px;color:var(--aco);background:var(--marca);box-shadow:0 6px 18px var(--glow);}
.itc-vacia{color:var(--tx3);font-style:italic;}
.itc-partido{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:14px;background:var(--vidrio);border:1px solid var(--brd2);border-radius:18px;padding:12px 18px;margin-bottom:8px;}
.itc-partido .eq{font-weight:700;overflow-wrap:anywhere;}.itc-partido .eq.v{text-align:right;}
.itc-partido .vs{min-width:84px;text-align:center;color:var(--tx3);font-weight:700;}
.itc-campeon{display:flex;align-items:center;gap:18px;padding:20px 26px;margin:6px 0 20px;border-radius:24px;color:var(--aco);
  background:linear-gradient(110deg,var(--g3),var(--g2),var(--g1),var(--g2),var(--g3));background-size:240% 100%;animation:itc-brillo 6s linear infinite;box-shadow:0 18px 50px var(--glow);}
.itc-copa{font-size:3.2rem;}
.itc-campeon-et{font-size:.9rem;font-weight:700;opacity:.85;}
.itc-campeon-nom{font-family:var(--display);font-weight:700;font-size:clamp(1.8rem,6vw,2.8rem);line-height:1;}

/* Tabla de posiciones */
.itc-tabla-wrap{overflow-x:auto;border-radius:20px;border:1px solid var(--brd);box-shadow:0 18px 50px rgba(0,0,0,.45);}
table.itc-tabla{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;min-width:360px;}
.itc-tabla th{background:var(--marca);color:var(--aco);font-family:var(--display);font-weight:600;font-size:.9rem;padding:12px 8px;text-align:center;letter-spacing:.5px;}
.itc-tabla th.eqc{text-align:left;padding-left:16px;}
.itc-tabla td{padding:12px 8px;text-align:center;background:var(--bgc);border-bottom:1px solid var(--brd2);color:var(--tx2);font-weight:500;}
.itc-tabla tr:nth-child(even) td{background:var(--bga);}
.itc-tabla td.eqc{text-align:left;position:sticky;left:0;color:var(--tx);font-weight:700;padding-left:12px;white-space:nowrap;}
.itc-tabla tr.cl td.eqc{box-shadow:inset 4px 0 0 var(--g2);}
.itc-tabla td.pts,.itc-tabla th.pts{font-family:var(--display);font-size:1.15rem;}
.itc-tabla td.pts{color:var(--achi);background:color-mix(in srgb,var(--g2) 16%,var(--bgc))!important;font-weight:700;}
.itc-tabla .rk{display:inline-grid;place-items:center;width:28px;height:28px;margin-right:10px;border-radius:50%;font-family:var(--display);font-size:.9rem;background:var(--bga);color:var(--tx2);border:1px solid var(--brd2);}
.itc-tabla .r1{background:var(--marca);color:var(--aco);border-color:transparent;}
.itc-tabla .r2{background:#D9DDE3;color:#14161A;border-color:transparent;}
.itc-tabla .r3{background:#CD7F32;color:#1A0E02;border-color:transparent;}
.itc-leyenda{display:flex;align-items:center;gap:8px;margin:10px 4px 0;font-size:.85rem;color:var(--tx2);}
.itc-leyenda i{width:4px;height:16px;border-radius:2px;background:var(--g2);}

/* Cuadro final simétrico */
.itc-llave-wrap{overflow-x:auto;padding:8px 4px 18px;}
.itc-llave{display:flex;gap:28px;align-items:stretch;min-height:300px;}
.itc-llave .col{flex:1 1 170px;min-width:160px;display:flex;flex-direction:column;}
.itc-ronda{height:34px;text-align:center;font-family:var(--display);font-weight:600;font-size:1rem;color:var(--g2);}
.itc-llave .cuerpo{flex:1;display:flex;flex-direction:column;}
.itc-llave .par{flex:1;display:flex;flex-direction:column;position:relative;}
.itc-llave .mw{flex:1;display:flex;align-items:center;padding:5px 0;position:relative;}
.itc-m{width:100%;background:var(--bgc);border:1px solid var(--brd2);border-radius:12px;overflow:hidden;box-shadow:0 6px 18px rgba(0,0,0,.35);}
.itc-m .t{display:flex;justify-content:space-between;gap:8px;padding:8px 10px;font-size:.86rem;font-weight:600;color:var(--tx2);}
.itc-m .t+.t{border-top:1px solid var(--brd2);}
.itc-m .t.v{color:var(--tx3);font-style:italic;font-weight:500;}
.itc-m .t.w{background:linear-gradient(90deg,color-mix(in srgb,var(--g2) 30%,var(--bgc)),var(--bgc));color:var(--achi);font-weight:800;}
.itc-m .n{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.itc-m .s{font-family:var(--display);font-size:1rem;}
.itc-m .nota{font-size:.72rem;color:var(--tx3);padding:4px 10px 7px;border-top:1px dashed var(--brd2);}
.itc-llave .iz .par::after,.itc-llave .de .par::after{content:"";position:absolute;top:25%;height:50%;width:14px;border:2px solid var(--ln);}
.itc-llave .iz .par::after{left:100%;border-left:none;}
.itc-llave .de .par::after{right:100%;border-right:none;}
.itc-llave .iz .par::before,.itc-llave .de .par::before{content:"";position:absolute;top:50%;width:14px;border-top:2px solid var(--ln);}
.itc-llave .iz .par::before{left:calc(100% + 14px);}
.itc-llave .de .par::before{right:calc(100% + 14px);}
.itc-llave .iz .solo::after,.itc-llave .de .solo::after{content:"";position:absolute;top:50%;width:28px;border-top:2px solid var(--ln);}
.itc-llave .iz .solo::after{left:100%;}.itc-llave .de .solo::after{right:100%;}
.itc-llave .cen .cuerpo{justify-content:center;}
.itc-llave .cen .mw{flex:0 0 auto;}
.itc-llave .cen .itc-m{border-color:var(--g2);box-shadow:0 0 34px var(--glow);}
.itc-trofeo{position:absolute;bottom:calc(100% + 6px);left:50%;transform:translateX(-50%);font-size:3.4rem;filter:drop-shadow(0 6px 18px var(--glow));}
.itc-hint{display:none;color:var(--tx3);font-size:.8rem;margin:0 4px 4px;}

@keyframes itc-entrar{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
@keyframes itc-barrido{to{background-position:-60% 0}}
@keyframes itc-brillo{from{background-position:0 0}to{background-position:240% 0}}

@media (max-width:900px){
  .block-container{padding:1.4rem 1.1rem 3rem;}
  .itc-hint{display:block;}
}
@media (max-width:640px){
  .block-container{padding:1rem .8rem 3rem;}
  .itc-hero{border-radius:20px;}
  .itc-partido{grid-template-columns:1fr;gap:6px;text-align:center;padding:14px;}
  .itc-partido .eq,.itc-partido .eq.v{text-align:center;}
  .itc-partido .itc-marcador,.itc-partido .vs{justify-self:center;}
  .itc-campeon{padding:16px;gap:12px;border-radius:20px;}.itc-copa{font-size:2.4rem;}
  .itc-tabla .hm{display:none;}.itc-tabla td,.itc-tabla th{padding:10px 5px;}
  .itc-tabla .rk{width:24px;height:24px;margin-right:6px;}
  button[data-baseweb="tab"]{padding:10px 16px;}
  .stApp input,.stApp textarea{font-size:16px;}
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
    centro = (
        f'<div class="itc-marcador">{marcador.local} - {marcador.visitante}</div>'
        if marcador else '<div class="vs">vs</div>'
    )
    st.markdown(
        f'<div class="itc-partido"><div class="eq">{html.escape(local)}</div>{centro}'
        f'<div class="eq v">{html.escape(visitante)}</div></div>',
        unsafe_allow_html=True,
    )


def campeon(nombre: str) -> None:
    st.markdown(
        '<div class="itc-campeon"><span class="itc-copa">🏆</span><div>'
        '<div class="itc-campeon-et">Campeón del torneo</div>'
        f'<div class="itc-campeon-nom">{html.escape(nombre)}</div></div></div>',
        unsafe_allow_html=True,
    )


def tabla(filas, nombres: dict, clasifican: int = 0) -> None:
    """Tabla de posiciones. `clasifican` marca los primeros puestos que pasan al cuadro."""
    cuerpo = ""
    for pos, f in enumerate(filas, start=1):
        dif = f"{f.diferencia:+d}" if f.diferencia else "0"
        marca = " cl" if clasifican and pos <= clasifican else ""
        rk = f"rk r{pos}" if pos <= 3 else "rk"
        nombre = html.escape(nombres.get(f.participante_id, f.participante_id))
        cuerpo += (
            f'<tr class="{marca.strip()}"><td class="eqc"><span class="{rk}">{pos}</span>{nombre}</td>'
            f"<td>{f.jugados}</td><td>{f.ganados}</td><td>{f.empatados}</td><td>{f.perdidos}</td>"
            f'<td class="hm">{f.a_favor}</td><td class="hm">{f.en_contra}</td>'
            f'<td>{dif}</td><td class="pts">{f.puntos}</td></tr>'
        )
    cabecera = (
        '<tr><th class="eqc">Equipo</th><th>PJ</th><th>PG</th><th>PE</th><th>PP</th>'
        '<th class="hm">GF</th><th class="hm">GC</th><th>+/-</th><th class="pts">PTS</th></tr>'
    )
    leyenda = (
        '<div class="itc-leyenda"><i></i>Clasifican al cuadro final</div>' if clasifican else ""
    )
    st.markdown(
        f'<div class="itc-tabla-wrap"><table class="itc-tabla"><thead>{cabecera}</thead>'
        f"<tbody>{cuerpo}</tbody></table></div>{leyenda}",
        unsafe_allow_html=True,
    )


def llave(rondas, nombres: dict, nombre_de_ronda) -> None:
    """Cuadro simétrico: la mitad de cada ronda a cada lado y la final al centro."""

    def etiqueta(p):
        return html.escape(nombres.get(p, p))

    def cruce(c) -> str:
        g, m = c.ganador(), c.marcador

        def fila(p, goles):
            if p is None:
                return f'<div class="t v"><span class="n">{"bye" if c.es_bye else "por definir"}</span></div>'
            s = f'<span class="s">{goles}</span>' if m else ""
            return f'<div class="t{" w" if p == g else ""}"><span class="n">{etiqueta(p)}</span>{s}</div>'

        nota = "pasa sin jugar" if c.es_bye else "esperando rival" if c.espera_rival else ""
        return (
            f'<div class="itc-m">{fila(c.local, m.local if m else "")}'
            f'{fila(c.visitante, m.visitante if m else "")}'
            f'{f"<div class=nota>{nota}</div>" if nota else ""}</div>'
        )

    def columna(clase, titulo, casillas, ultima=False) -> str:
        if ultima:
            cuerpo = f'<div class="mw solo">{cruce(casillas[0])}</div>'
        else:
            cuerpo = "".join(
                f'<div class="par"><div class="mw">{cruce(casillas[i])}</div>'
                f'<div class="mw">{cruce(casillas[i + 1])}</div></div>'
                for i in range(0, len(casillas), 2)
            )
        return f'<div class="col {clase}"><div class="itc-ronda">{titulo}</div><div class="cuerpo">{cuerpo}</div></div>'

    total = len(rondas)
    izquierda, derecha = [], []
    for r in range(total - 1):
        mitad = len(rondas[r]) // 2
        titulo = nombre_de_ronda(len(rondas[r]))
        ultima = r == total - 2
        izquierda.append(columna("iz", titulo, rondas[r][:mitad], ultima))
        derecha.insert(0, columna("de", titulo, rondas[r][mitad:], ultima))

    final = (
        '<div class="col cen"><div class="itc-ronda">Final</div><div class="cuerpo">'
        f'<div class="mw"><span class="itc-trofeo">🏆</span>{cruce(rondas[-1][0])}</div></div></div>'
    )
    columnas = total * 2 - 1
    st.markdown(
        '<div class="itc-hint">Desliza para ver todo el cuadro</div>'
        f'<div class="itc-llave-wrap"><div class="itc-llave" style="min-width:{columnas * 190}px">'
        f'{"".join(izquierda)}{final}{"".join(derecha)}</div></div>',
        unsafe_allow_html=True,
    )
