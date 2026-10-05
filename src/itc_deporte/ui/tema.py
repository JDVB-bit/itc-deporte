"""Identidad visual de ITC Deportes: una galería plana, negro y oro.

Dos referencias, cada una en lo suyo:

- **Nike** para la página: lienzo casi negro, hairlines en vez de sombras,
  fotografía a sangre, botones en píldora y tipografía contenida. Sin
  degradados decorativos: el único degradado es el velo que oscurece la foto
  del encabezado para que el texto se lea.
- **Uniswap Cup** para el cuadro final: diagrama plano de esquinas rectas,
  conectores de 1px en ángulo recto, números y etapas en monoespaciada, y el
  color de acento reservado para lo que avanza (ganadores, etapas, camino).

Dos paletas, las dos oscuras a propósito: `st.dataframe` se dibuja en un canvas
que toma sus colores de `.streamlit/config.toml` y no se puede tematizar con CSS.
Contraste: `tx`, `tx2` y `tx3` superan 5:1 sobre sus superficies, y `aco` (texto
sobre el acento) supera 7:1.
"""

from __future__ import annotations

import base64
import html
from pathlib import Path

import streamlit as st

INSTITUCION = "Escuela Tecnológica Instituto Técnico Central"

TEMAS = {
    "oscuro": dict(  # Negro y oro
        bg="#0C0C0C", bgc="#141414", bga="#1C1C1C", sbg="#0A0A0A", blush="#1A160A",
        line="#2B2B2B", tx="#F5F5F5", tx2="#A3A3A3", tx3="#8A8A8A",
        ac="#C9A227", aco="#111111", ico="", lbl="Cambiar tema",
    ),
    "verde": dict(  # Negro verdoso con el verde institucional
        bg="#08100C", bgc="#0F1913", bga="#15231B", sbg="#060D09", blush="#101C0E",
        line="#24372C", tx="#F2F7F4", tx2="#A5B8AD", tx3="#86A090",
        ac="#8DB63C", aco="#0B1405", ico="", lbl="Cambiar tema",
    ),
}

_COLORES = ("bg", "bgc", "bga", "sbg", "blush", "line", "tx", "tx2", "tx3", "ac", "aco")


def actual() -> dict:
    return TEMAS[st.session_state.get("tema", "oscuro")]


def alternar() -> None:
    st.session_state.tema = "verde" if actual() is TEMAS["oscuro"] else "oscuro"


_FUENTES = (
    "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600"
    "&family=Jost:wght@500;600&family=JetBrains+Mono:wght@500;700&display=swap');"
)

_ESTILO = """
:root{
  --wire:color-mix(in srgb,var(--tx) 24%,transparent);
  --display:'Jost','Futura','Century Gothic',sans-serif;
  --mono:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace;
}
.stApp{background:var(--bg);color:var(--tx);font-family:'Inter',system-ui,sans-serif;}
[data-testid="stHeader"]{background:transparent;}
.block-container{max-width:1440px;padding-top:1.6rem;}
.stApp h1,.stApp h2,.stApp h3{font-family:var(--display);font-weight:500;color:var(--tx);letter-spacing:0;}
.stApp h2{font-size:1.9rem;text-transform:uppercase;}
[data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li{color:var(--tx);}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p{color:var(--tx2);}
.stApp label,.stApp label p,[data-testid="stWidgetLabel"] p{color:var(--tx2);font-weight:500;}
.stApp hr{border-color:var(--line);}
.stApp a{color:var(--ac);}

/* Barra lateral */
section[data-testid="stSidebar"]{background:var(--sbg);border-right:1px solid var(--line);}
section[data-testid="stSidebar"] [data-testid="stImage"] img{border-radius:0;}
.itc-side-card{border:1px solid var(--line);background:var(--bgc);padding:12px;margin:8px 0;}
.itc-side-user{display:flex;align-items:center;gap:12px;}
.itc-side-avatar{width:36px;height:36px;display:grid;place-items:center;background:var(--ac);color:var(--aco);font-weight:600;flex:none;}
.itc-side-name{font-weight:600;font-size:.95rem;overflow-wrap:anywhere;}
.itc-side-role{font:500 12px/1.4 var(--mono);color:var(--tx2);}
section[data-testid="stSidebar"] [data-testid="stRadio"] label{
  border:1px solid var(--line);border-radius:0;padding:10px 12px;margin:0 0 -1px;width:100%;background:var(--bgc);transition:background .15s;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label p{color:var(--tx);font-weight:500;}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{background:var(--bga);}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked){background:var(--bga);box-shadow:inset 3px 0 0 var(--ac);}

/* Botones: píldora, sin sombra */
div[data-testid="stButton"] button,div[data-testid="stFormSubmitButton"] button{
  min-height:44px;border-radius:30px;padding:6px 20px;font-weight:500;
  background:transparent;color:var(--tx);border:1px solid var(--wire);transition:background .15s,border-color .15s,opacity .15s;
}
div[data-testid="stButton"] button p,div[data-testid="stFormSubmitButton"] button p{color:inherit;}
div[data-testid="stButton"] button:hover:not(:disabled){background:var(--bga);border-color:var(--tx);}
div[data-testid="stFormSubmitButton"] button{background:var(--ac);color:var(--aco);border-color:var(--ac);}
div[data-testid="stFormSubmitButton"] button:hover{opacity:.85;background:var(--ac);color:var(--aco);}
div[data-testid="stButton"] button:disabled{color:var(--ac);border-color:var(--ac);opacity:1;}
.stApp button:focus-visible,.stApp input:focus-visible{outline:2px solid var(--ac);outline-offset:2px;}

/* Pestañas: enlaces subrayados */
[data-baseweb="tab-list"]{gap:28px;border-bottom:1px solid var(--line);overflow-x:auto;scrollbar-width:none;padding-bottom:0;}
[data-baseweb="tab-list"]::-webkit-scrollbar{display:none;}
[data-baseweb="tab-highlight"],[data-baseweb="tab-border"]{display:none;}
button[data-baseweb="tab"]{flex:0 0 auto;background:transparent;border:none;border-bottom:2px solid transparent;border-radius:0;padding:12px 0;color:var(--tx2);margin-bottom:-1px;}
button[data-baseweb="tab"] p{color:inherit;font-weight:500;}
button[data-baseweb="tab"]:hover{color:var(--tx);}
button[data-baseweb="tab"][aria-selected="true"]{color:var(--tx);border-bottom-color:var(--ac);}

/* Campos y contenedores nativos: esquinas rectas */
[data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="textarea"],[data-baseweb="select"]>div{background:var(--bgc);border-color:var(--line);border-radius:0;color:var(--tx);}
[data-baseweb="input"]:focus-within,[data-baseweb="select"]>div:focus-within{border-color:var(--ac);box-shadow:none;}
.stApp input,.stApp textarea{color:var(--tx);-webkit-text-fill-color:var(--tx);}
.stApp input::placeholder,.stApp textarea::placeholder{color:var(--tx3);-webkit-text-fill-color:var(--tx3);}
[data-baseweb="select"] svg,[data-testid="stNumberInput"] button{color:var(--tx2);}
[data-baseweb="popover"] [data-baseweb="menu"],[data-baseweb="popover"] ul,[data-baseweb="calendar"]{background:var(--bgc);color:var(--tx);border-radius:0;}
[data-baseweb="popover"] li{color:var(--tx);}
[data-baseweb="popover"] li:hover,[data-baseweb="popover"] li[aria-selected="true"]{background:var(--bga);}
[data-testid="stPopoverBody"]{background:var(--bgc);border:1px solid var(--wire);border-radius:0;box-shadow:none;}
[data-testid="stExpander"] details{background:transparent;border:1px solid var(--line);border-radius:0;}
[data-testid="stExpander"] summary,[data-testid="stExpander"] summary p{color:var(--tx);font-weight:500;}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:0;}
[data-testid="stAlert"]{border-radius:0;border:1px solid var(--line);}
[data-testid="stAlert"] p{color:var(--tx);}
[data-testid="stForm"]{background:var(--bgc);border:1px solid var(--line);border-radius:0;padding:16px;}
[data-testid="stCheckbox"] label p{color:var(--tx);}

/* Encabezado editorial con la rueda de imágenes */
.itc-hero{position:relative;overflow:hidden;min-height:clamp(270px,36vw,420px);display:flex;flex-direction:column;justify-content:flex-end;
  padding:clamp(18px,3.5vw,40px);margin-bottom:24px;background:var(--bgc);border:1px solid var(--line);}
.itc-fondo{position:absolute;inset:0;z-index:0;}
.itc-fondo i{position:absolute;inset:0;background-size:cover;background-position:center;opacity:0;filter:grayscale(.25);}
.itc-hero::after{content:"";position:absolute;inset:0;z-index:1;background:linear-gradient(0deg,rgba(0,0,0,.88),rgba(0,0,0,.45) 55%,rgba(0,0,0,.6));}
.itc-hero>*:not(.itc-fondo){position:relative;z-index:2;}
.itc-eyebrow{font:500 12px/1.4 var(--mono);color:#D6D6D6;margin-bottom:10px;}
.itc-titulo{font-family:var(--display);font-weight:500;line-height:1;font-size:clamp(2.4rem,8.5vw,4.75rem);color:#FFFFFF;}
.itc-sub{color:#E0E0E0;font-size:clamp(.95rem,2.4vw,1.05rem);margin-top:10px;}
.itc-chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px;}
.itc-chip{border:1px solid rgba(255,255,255,.55);border-radius:30px;padding:5px 14px;font-size:.82rem;font-weight:500;color:#FFFFFF;}
.itc-chip:first-child{background:var(--ac);border-color:var(--ac);color:var(--aco);}

/* Secciones, partidos y banner del campeón */
.itc-seccion{font-family:var(--display);font-weight:500;font-size:1.25rem;color:var(--tx);margin:28px 0 12px;padding-bottom:8px;border-bottom:1px solid var(--line);}
.itc-marcador{display:inline-block;min-width:68px;text-align:center;font:700 1.25rem/1.6 var(--mono);letter-spacing:-.02em;color:var(--aco);background:var(--ac);padding:0 12px;}
.itc-vacia{color:var(--tx3);font-style:italic;}
.itc-partido{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:14px;background:var(--bgc);border:1px solid var(--line);padding:10px 16px;margin-bottom:-1px;}
.itc-partido .eq{font-weight:500;overflow-wrap:anywhere;}.itc-partido .eq.v{text-align:right;}
.itc-partido .vs{min-width:68px;text-align:center;font:500 12px/1 var(--mono);color:var(--tx3);}
.itc-campeon{display:flex;flex-direction:column;gap:6px;padding:20px 24px;margin:6px 0 20px;background:var(--ac);color:var(--aco);}
.itc-campeon-et{font:500 12px/1 var(--mono);}
.itc-campeon-nom{font-family:var(--display);font-weight:500;font-size:clamp(1.8rem,6vw,2.8rem);line-height:1;text-transform:uppercase;}

/* Tabla de posiciones */
.itc-tabla-wrap{overflow-x:auto;border:1px solid var(--line);}
table.itc-tabla{width:100%;border-collapse:collapse;min-width:360px;}
.itc-tabla th{font:500 12px/1 var(--mono);color:var(--tx2);text-align:center;padding:12px 8px;border-bottom:1px solid var(--wire);background:var(--bgc);}
.itc-tabla th.eqc{text-align:left;padding-left:16px;}
.itc-tabla td{padding:10px 8px;text-align:center;background:var(--bg);border-bottom:1px solid var(--line);font:500 14px/1.2 var(--mono);color:var(--tx2);}
.itc-tabla tr:last-child td{border-bottom:none;}
.itc-tabla td.eqc{text-align:left;position:sticky;left:0;padding-left:12px;font-family:'Inter',sans-serif;}
.itc-tabla tr.cl td.eqc{box-shadow:inset 3px 0 0 var(--ac);}
.itc-tabla .eqw{display:flex;align-items:center;gap:12px;}
.itc-tabla .rk{display:inline-grid;place-items:center;width:26px;height:26px;flex:none;font:700 13px/1 var(--mono);background:var(--bga);color:var(--tx2);border:1px solid var(--line);}
.itc-tabla .r1{background:var(--ac);color:var(--aco);border-color:var(--ac);}
.itc-tabla .nm{font-weight:600;font-size:.95rem;color:var(--tx);white-space:nowrap;}
.itc-tabla .cu{font:500 11px/1.3 var(--mono);color:var(--tx3);margin-top:2px;}
.itc-tabla td.pts{font-weight:700;font-size:16px;color:var(--ac);}
.itc-tabla th.pts{color:var(--ac);}
.itc-leyenda{display:flex;align-items:center;gap:8px;margin:10px 2px 0;font:500 12px/1 var(--mono);color:var(--tx2);}
.itc-leyenda i{width:10px;height:10px;background:var(--ac);}

/* Cuadro final: diagrama plano */
.itc-llave-wrap{overflow-x:auto;padding:12px 0 20px;}
.itc-llave{display:flex;gap:28px;align-items:stretch;min-height:300px;}
.itc-llave .col{flex:1 1 180px;min-width:170px;display:flex;flex-direction:column;}
.itc-ronda{height:34px;display:flex;justify-content:center;align-items:flex-start;}
.itc-tag{display:inline-block;background:var(--ac);color:var(--aco);font:500 12px/1 var(--mono);padding:6px 8px;}
.itc-llave .cuerpo{flex:1;display:flex;flex-direction:column;}
.itc-llave .par{flex:1;display:flex;flex-direction:column;position:relative;}
.itc-llave .mw{flex:1;display:flex;align-items:center;padding:6px 0;position:relative;}
.itc-m{width:100%;background:var(--bgc);border:1px solid var(--line);}
.itc-m.dec{background:var(--blush);border-color:var(--wire);}
.itc-m .t{display:grid;grid-template-columns:1fr auto;align-items:stretch;}
.itc-m .t+.t{border-top:1px solid var(--line);}
.itc-m .n{padding:7px 10px;font-size:.85rem;font-weight:500;color:var(--tx2);overflow:hidden;}
.itc-m .n b{display:block;font-weight:inherit;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.itc-m .n small{display:block;font:500 11px/1.3 var(--mono);color:var(--tx3);}
.itc-m .t.v .n{color:var(--tx3);font-style:italic;font-weight:400;}
.itc-m .s{min-width:30px;display:grid;place-items:center;border-left:1px solid var(--line);font:700 14px/1 var(--mono);color:var(--tx2);}
.itc-m .t.w .n{color:var(--tx);font-weight:600;}
.itc-m .t.w .s{background:var(--ac);color:var(--aco);border-left-color:var(--ac);}
.itc-m .nota{font:500 11px/1.3 var(--mono);color:var(--tx3);padding:5px 10px;border-top:1px dashed var(--line);}
.itc-m .vs{text-align:center;font:700 28px/1 var(--mono);letter-spacing:-.02em;color:var(--ac);padding:10px 0;border-top:1px solid var(--line);}
.itc-llave .cen .s{min-width:44px;font-size:22px;}
.itc-llave .cen .itc-m{border-color:var(--ac);}
.itc-llave .cen .cuerpo{justify-content:center;}
.itc-llave .cen .mw{flex:0 0 auto;}
.itc-llave .cen .itc-tag.camp{position:absolute;bottom:100%;left:0;margin-bottom:6px;}
.itc-llave .mw::after,.itc-llave .par::after{content:"";position:absolute;top:50%;height:1px;width:14px;background:var(--wire);}
.itc-llave .iz .mw::after{left:100%;}.itc-llave .de .mw::after{right:100%;}
.itc-llave .iz .par::after{left:calc(100% + 14px);}.itc-llave .de .par::after{right:calc(100% + 14px);}
.itc-llave .par>.mw::before{content:"";position:absolute;width:1px;background:var(--wire);}
.itc-llave .iz .par>.mw::before{left:calc(100% + 14px);}.itc-llave .de .par>.mw::before{right:calc(100% + 14px);}
.itc-llave .par>.mw:first-child::before{top:50%;bottom:0;}
.itc-llave .par>.mw:last-child::before{top:0;bottom:50%;}
.itc-llave .iz .solo::after,.itc-llave .de .solo::after{width:28px;}
.itc-llave .cen .mw::after{display:none;}
.itc-llave .mw.g::after,.itc-llave .par>.mw.g::before,.itc-llave .par.g::after{background:var(--ac);}
.itc-hint{display:none;color:var(--tx3);font:500 12px/1 var(--mono);margin:0 0 6px;}

/* Pie institucional */
.itc-pie{margin-top:48px;padding:20px 0 8px;border-top:1px solid var(--line);display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;color:var(--tx2);font-size:.85rem;}
.itc-pie b{color:var(--tx);font-weight:600;}
.itc-pie span{font-family:var(--mono);font-size:12px;}

@media (max-width:900px){.block-container{padding:1rem 1rem 3rem;}.itc-hint{display:block;}}
@media (max-width:640px){
  .block-container{padding:.8rem .75rem 3rem;}
  .itc-partido{grid-template-columns:1fr;gap:6px;text-align:center;padding:12px;}
  .itc-partido .eq,.itc-partido .eq.v{text-align:center;}
  .itc-partido .itc-marcador,.itc-partido .vs{justify-self:center;}
  .itc-tabla .hm{display:none;}.itc-tabla td,.itc-tabla th{padding:10px 5px;}
  .itc-tabla .nm{white-space:normal;}
  button[data-baseweb="tab"]{padding:12px 0;}
  .stApp input,.stApp textarea{font-size:16px;}
}
@media (prefers-reduced-motion:reduce){.itc-fondo i{animation:none!important;}.itc-fondo i:first-child{opacity:1;}*{transition:none!important}}
"""


def _variables(t: dict) -> str:
    return ":root{" + ";".join(f"--{k}:{t[k]}" for k in _COLORES) + "}"


def aplicar() -> None:
    st.markdown(f"<style>{_FUENTES}{_variables(actual())}{_ESTILO}</style>", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _leer_fondos(directorio: str) -> tuple[str, ...]:
    """Las imágenes `fondo_*` de la carpeta, como URIs de datos (vacío si no hay)."""
    carpeta = Path(directorio)
    if not carpeta.is_dir():
        return ()
    tipos = {".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png", ".webp": "webp"}
    uris = []
    for archivo in sorted(carpeta.glob("fondo_*")):
        tipo = tipos.get(archivo.suffix.lower())
        if tipo:
            datos = base64.b64encode(archivo.read_bytes()).decode("ascii")
            uris.append(f"data:image/{tipo};base64,{datos}")
    return tuple(uris)


def fondos(directorio: str | Path | None = None) -> tuple[str, ...]:
    """Imágenes de la rueda del encabezado. Sin carpeta, busca `static/` junto al guion."""
    candidatos = [Path(directorio)] if directorio else [
        Path.cwd() / "static",
        Path(__file__).resolve().parents[3] / "static",
    ]
    for carpeta in candidatos:
        uris = _leer_fondos(str(carpeta))
        if uris:
            return uris
    return ()


def _rueda(uris: tuple[str, ...], segundos: int = 6) -> str:
    """Fundido cruzado en CSS puro: sin JavaScript, sin dependencias, sin reruns."""
    if not uris:
        return ""
    n, ciclo = len(uris), len(uris) * segundos
    entra = 1.2 / ciclo * 100  # ~1,2 s de fundido, en % del ciclo
    visible = 100 / n
    estilo = (
        f"@keyframes itc-rueda{{0%{{opacity:0}}{entra:.2f}%{{opacity:1}}"
        f"{visible:.2f}%{{opacity:1}}{visible + entra:.2f}%{{opacity:0}}100%{{opacity:0}}}}"
    )
    capas = ""
    for i, uri in enumerate(uris):
        estilo += (
            f".itc-fondo i:nth-child({i + 1}){{background-image:url({uri});"
            f"animation:itc-rueda {ciclo}s linear {i * segundos}s infinite;}}"
        )
        capas += "<i></i>"
    return f"<style>{estilo}</style><div class='itc-fondo'>{capas}</div>"


def hero(titulo: str, subtitulo: str, chips: tuple[str, ...] = (), fondos: tuple[str, ...] = ()) -> None:
    fichas = "".join(f'<span class="itc-chip">{html.escape(c)}</span>' for c in chips)
    st.markdown(
        f'<div class="itc-hero">{_rueda(fondos)}'
        f'<div class="itc-eyebrow">{INSTITUCION}</div>'
        f'<div class="itc-titulo">{titulo}</div><div class="itc-sub">{subtitulo}</div>'
        f'{f"<div class=itc-chips>{fichas}</div>" if fichas else ""}</div>',
        unsafe_allow_html=True,
    )


def seccion(texto: str) -> None:
    st.markdown(f'<div class="itc-seccion">{texto}</div>', unsafe_allow_html=True)


def pie() -> None:
    st.markdown(
        f'<div class="itc-pie"><div><b>ITC Deportes</b><br>{INSTITUCION} · '
        "Establecimiento Público de Educación Superior</div><span>2026</span></div>",
        unsafe_allow_html=True,
    )


def partido(local: str, visitante: str, marcador=None) -> None:
    centro = (
        f'<div class="itc-marcador">{marcador.local} - {marcador.visitante}</div>'
        if marcador else '<div class="vs">VS</div>'
    )
    st.markdown(
        f'<div class="itc-partido"><div class="eq">{html.escape(local)}</div>{centro}'
        f'<div class="eq v">{html.escape(visitante)}</div></div>',
        unsafe_allow_html=True,
    )


def campeon(nombre: str) -> None:
    st.markdown(
        '<div class="itc-campeon"><div class="itc-campeon-et">CAMPEÓN</div>'
        f'<div class="itc-campeon-nom">{html.escape(nombre)}</div></div>',
        unsafe_allow_html=True,
    )


def tabla(filas, nombres: dict, cursos: dict | None = None, clasifican: int = 0) -> None:
    """Tabla de posiciones; bajo cada equipo, en pequeño, su curso."""
    cursos = cursos or {}
    cuerpo = ""
    for pos, f in enumerate(filas, start=1):
        dif = f"{f.diferencia:+d}" if f.diferencia else "0"
        curso = cursos.get(f.participante_id)
        sub = f'<div class="cu">Curso {html.escape(str(curso))}</div>' if curso else ""
        nombre = html.escape(nombres.get(f.participante_id, f.participante_id))
        marca = "cl" if clasifican and pos <= clasifican else ""
        cuerpo += (
            f'<tr class="{marca}"><td class="eqc"><div class="eqw">'
            f'<span class="rk{" r1" if pos == 1 else ""}">{pos}</span>'
            f'<div><div class="nm">{nombre}</div>{sub}</div></div></td>'
            f"<td>{f.jugados}</td><td>{f.ganados}</td><td>{f.empatados}</td><td>{f.perdidos}</td>"
            f'<td class="hm">{f.a_favor}</td><td class="hm">{f.en_contra}</td>'
            f'<td>{dif}</td><td class="pts">{f.puntos}</td></tr>'
        )
    cabecera = (
        '<tr><th class="eqc">EQUIPO</th><th>PJ</th><th>PG</th><th>PE</th><th>PP</th>'
        '<th class="hm">GF</th><th class="hm">GC</th><th>+/-</th><th class="pts">PTS</th></tr>'
    )
    leyenda = '<div class="itc-leyenda"><i></i>Clasifican al cuadro final</div>' if clasifican else ""
    st.markdown(
        f'<div class="itc-tabla-wrap"><table class="itc-tabla"><thead>{cabecera}</thead>'
        f"<tbody>{cuerpo}</tbody></table></div>{leyenda}",
        unsafe_allow_html=True,
    )


def llave(rondas, nombres: dict, nombre_de_ronda, cursos: dict | None = None) -> None:
    """Cuadro simétrico: la mitad de cada ronda a cada lado y la final al centro.

    Es de solo lectura (Streamlit no admite widgets dentro de HTML); los
    marcadores se cargan en el panel que lo acompaña.
    """
    cursos = cursos or {}

    def equipo(p) -> str:
        curso = cursos.get(p)
        extra = f"<small>Curso {html.escape(str(curso))}</small>" if curso else ""
        return f"<b>{html.escape(nombres.get(p, p))}</b>{extra}"

    def cruce(c, final: bool = False) -> str:
        g, m = c.ganador(), c.marcador

        def fila(p, goles) -> str:
            if p is None:
                return f'<div class="t v"><div class="n">{"bye" if c.es_bye else "por definir"}</div></div>'
            s = f'<div class="s">{goles}</div>' if m else ""
            return f'<div class="t{" w" if p == g else ""}"><div class="n">{equipo(p)}</div>{s}</div>'

        nota = "pasa sin jugar" if c.es_bye else "esperando rival" if c.espera_rival else ""
        medio = '<div class="vs">VS</div>' if final else ""
        return (
            f'<div class="itc-m{" dec" if g else ""}">{fila(c.local, m.local if m else "")}{medio}'
            f'{fila(c.visitante, m.visitante if m else "")}'
            f'{f"<div class=nota>{nota}</div>" if nota else ""}</div>'
        )

    def nodo(c, extra: str = "") -> str:
        return f'<div class="mw{" g" if c.ganador() else ""}{extra}">{cruce(c)}</div>'

    def columna(clase, titulo, casillas, ultima=False) -> str:
        if ultima:
            cuerpo = nodo(casillas[0], " solo")
        else:
            cuerpo = "".join(
                f'<div class="par{" g" if casillas[i].ganador() or casillas[i + 1].ganador() else ""}">'
                f"{nodo(casillas[i])}{nodo(casillas[i + 1])}</div>"
                for i in range(0, len(casillas), 2)
            )
        return (
            f'<div class="col {clase}"><div class="itc-ronda"><span class="itc-tag">{titulo}</span></div>'
            f'<div class="cuerpo">{cuerpo}</div></div>'
        )

    total = len(rondas)
    izquierda, derecha = [], []
    for r in range(total - 1):
        mitad = len(rondas[r]) // 2
        titulo = nombre_de_ronda(len(rondas[r]))
        ultima = r == total - 2
        izquierda.append(columna("iz", titulo, rondas[r][:mitad], ultima))
        derecha.insert(0, columna("de", titulo, rondas[r][mitad:], ultima))

    f = rondas[-1][0]
    campeon_tag = '<span class="itc-tag camp">CAMPEÓN</span>' if f.ganador() else ""
    final = (
        '<div class="col cen"><div class="itc-ronda"><span class="itc-tag">Final</span></div>'
        f'<div class="cuerpo"><div class="mw">{campeon_tag}{cruce(f, final=True)}</div></div></div>'
    )
    st.markdown(
        '<div class="itc-hint">Desliza para ver todo el cuadro</div>'
        f'<div class="itc-llave-wrap"><div class="itc-llave" style="min-width:{(total * 2 - 1) * 190}px">'
        f'{"".join(izquierda)}{final}{"".join(derecha)}</div></div>',
        unsafe_allow_html=True,
    )
