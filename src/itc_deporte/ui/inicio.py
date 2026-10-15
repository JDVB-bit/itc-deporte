"""La pantalla de entrada: lo primero que ve quien abre ITC Deportes.

Presenta los deportes de la ETITC y lleva a los Intercursos. No decide nada del
negocio: no llama a ningún servicio, así que no puede fallar por la base de datos
y tampoco tiene permisos que comprobar.

La navegación es una sola clave de sesión, `vista`: `"inicio"`, `"intercursos"` o
`"intercolegiados"`. Las dos últimas coinciden con los valores de `Torneo`.
El logo de la barra lateral y los botones de esta página solo la cambian.

Imágenes: las ilustraciones de los deportes son SVG incrustado, así que no hay
nada que descargar ni enlaces que se rompan. Si existen, se usan además:

- `static/logo_itc-deportes.png`: el logo (hero y barra lateral).
- `static/portada.jpg` (o `.png` / `.webp`): foto de fondo del hero.
"""

from __future__ import annotations

import base64
import struct
from dataclasses import asdict, dataclass, is_dataclass
from functools import lru_cache
from pathlib import Path

import streamlit as st

from . import tema

# En Streamlit Cloud el paquete se instala en site-packages, así que `static/` se
# busca desde donde corre la aplicación (la raíz del repositorio) y, por si
# acaso, desde la ubicación del código.
_CARPETAS = (Path.cwd() / "static", Path(__file__).resolve().parents[3] / "static")
_LIMITE_BYTES = 2_000_000

VISTAS = ("inicio", "intercursos", "intercolegiados")


# ── Paleta ──────────────────────────────────────────────────────────────────

_BASE = dict(
    ac="#D4A017", achi="#FFD040", bg="#0A0A0A", bgc="#141414", tx="#F5F0E8",
    tx2="#9A9080", tx3="#5A5550", grad="linear-gradient(135deg,#0A0A0A,#1A1200)",
    ico="🎨", lbl="Cambiar tema",
)


def _paleta() -> dict:
    """Los colores del tema activo, con valores de respaldo.

    Así la portada no se rompe si `tema.actual()` cambia de forma o le falta
    alguna clave.
    """
    try:
        actual = tema.actual()
    except Exception:
        actual = {}
    if is_dataclass(actual):
        actual = asdict(actual)
    if not isinstance(actual, dict):
        actual = {}
    return {**_BASE, **actual}


# ── Navegación ──────────────────────────────────────────────────────────────


def ir_a(vista: str) -> None:
    """Callback de botón: cambia de vista. Streamlit redibuja solo."""
    if vista not in VISTAS:
        raise ValueError(f"Vista desconocida: {vista!r}")
    st.session_state.vista = vista


# ── Imágenes ────────────────────────────────────────────────────────────────


def _buscar(*nombres: str) -> Path | None:
    for carpeta in _CARPETAS:
        for nombre in nombres:
            ruta = carpeta / nombre
            if ruta.is_file() and ruta.stat().st_size <= _LIMITE_BYTES:
                return ruta
    return None


@lru_cache(maxsize=8)
def _data_uri(ruta: str) -> str:
    archivo = Path(ruta)
    tipos = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
             ".webp": "image/webp", ".svg": "image/svg+xml"}
    tipo = tipos.get(archivo.suffix.lower(), "application/octet-stream")
    return f"data:{tipo};base64," + base64.b64encode(archivo.read_bytes()).decode()


def _logo() -> str:
    ruta = _buscar("logo_itc-deportes.png")
    return _data_uri(str(ruta)) if ruta else ""


def _portada() -> str:
    ruta = _buscar("portada.jpg", "portada.jpeg", "portada.png", "portada.webp")
    return _data_uri(str(ruta)) if ruta else ""


@lru_cache(maxsize=1)
def _proporcion_logo() -> str:
    """Ancho / alto del logo, para que el botón de la barra lateral conserve su
    forma al encoger o ampliar el menú. Se lee de la cabecera del PNG."""
    ruta = _buscar("logo_itc-deportes.png")
    if ruta is not None:
        with ruta.open("rb") as f:
            cabecera = f.read(24)
        if cabecera[:8] == b"\x89PNG\r\n\x1a\n":
            ancho, alto = struct.unpack(">II", cabecera[16:24])
            if ancho and alto:
                return f"{ancho} / {alto}"
    return "1 / 1"


# ── Contenido ───────────────────────────────────────────────────────────────
# Para añadir un deporte basta con una línea aquí. `figura` elige la ilustración.


@dataclass(frozen=True)
class DeporteDeLaEscuela:
    nombre: str
    figura: str
    resumen: str
    regla: str


DEPORTES = (
    DeporteDeLaEscuela(
        "Microfútbol", "futbol",
        "El clásico del patio: espacios cortos, toque rápido y gol en cada jugada.",
        "Puntúa 3 / 1 / 0",
    ),
    DeporteDeLaEscuela(
        "Baloncesto", "baloncesto",
        "Ritmo, defensa y triples. Cada posesión puede cambiar el partido.",
        "Puntúa 3 / 1 / 0",
    ),
    DeporteDeLaEscuela(
        "Voleyball", "voleibol",
        "Se juega por sets: un 3-2 reparte puntos a los dos equipos.",
        "Puntúa por sets",
    ),
    DeporteDeLaEscuela(
        "Balonmano", "balonmano",
        "Velocidad, pase y potencia en una cancha que no perdona descuidos.",
        "Puntúa 3 / 1 / 0",
    ),
)

_FIGURAS = {
    "futbol": (
        '<circle cx="32" cy="32" r="28"/>'
        '<polygon points="32,21 42,28 38,40 26,40 22,28" fill="currentColor"/>'
        '<path d="M32 21V4M42 28l15-6M38 40l9 13M26 40l-9 13M22 28L7 22"/>'
    ),
    "baloncesto": (
        '<circle cx="32" cy="32" r="28"/>'
        '<path d="M4 32h56M32 4v56"/>'
        '<path d="M12 11c9 9 9 33 0 42M52 11c-9 9-9 33 0 42"/>'
    ),
    "voleibol": (
        '<circle cx="32" cy="32" r="28"/>'
        '<g id="a"><path d="M32 4C27 18 34 31 59 38"/></g>'
        '<use href="#a" transform="rotate(120 32 32)"/>'
        '<use href="#a" transform="rotate(240 32 32)"/>'
    ),
    "balonmano": (
        '<circle cx="32" cy="32" r="28"/>'
        '<polygon points="32,19 43,25.5 43,38.5 32,45 21,38.5 21,25.5"/>'
        '<path d="M32 19V4M43 25.5l13-7.5M43 38.5l13 7.5M32 45v15M21 38.5L8 46M21 25.5L8 18"/>'
    ),
}

#: Marcas de una cancha, usadas como textura del hero y del banner.
_MARCAS_DE_CANCHA = (
    '<rect x="20" y="20" width="760" height="360" rx="6"/>'
    '<path d="M400 20v360"/><circle cx="400" cy="200" r="70"/>'
    '<circle cx="400" cy="200" r="5" fill="currentColor"/>'
    '<rect x="20" y="110" width="110" height="180"/><rect x="670" y="110" width="110" height="180"/>'
    '<path d="M130 160a40 40 0 0 1 0 80M670 160a40 40 0 0 0 0 80"/>'
)


def _svg_como_imagen(svg: str, clase: str = "") -> str:
    """Un SVG como `<img>` con data URI.

    `st.markdown` no garantiza que deje pasar `<svg>` en línea según la versión
    de Streamlit; una imagen con data URI se pinta siempre. Como una imagen no
    hereda `currentColor`, el color del tema se escribe en el propio SVG.
    """
    uri = "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
    return f'<img class="{clase}" src="{uri}" alt="">'


def _figura(clave: str, clase: str = "") -> str:
    color = _paleta()["ac"]
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" '
        f'fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" '
        f'stroke-linejoin="round">{_FIGURAS[clave]}</svg>'
    ).replace('fill="currentColor"', f'fill="{color}"')
    return _svg_como_imagen(svg, clase)


def _cancha() -> str:
    color = _paleta()["ac"]
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" width="800" height="400" '
        f'fill="none" stroke="{color}" stroke-width="3">{_MARCAS_DE_CANCHA}</svg>'
    ).replace('fill="currentColor"', f'fill="{color}"')
    return f'<div class="in-cancha">{_svg_como_imagen(svg)}</div>'


def _titulo(nivel: int, clase: str, texto: str) -> str:
    """Un título como `div` con rol de encabezado.

    Los `h1`/`h2`/`h3` de `st.markdown` heredan los estilos globales del tema
    (fuente, color, enlace de ancla) y pisaban los de la portada. Un `div` con
    `role="heading"` es igual de accesible y no los hereda.
    """
    return f'<div class="{clase}" role="heading" aria-level="{nivel}">{texto}</div>'


# ── Estilos ─────────────────────────────────────────────────────────────────

_FUENTES = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Bebas+Neue&family=Barlow+Condensed:wght@500;600;700"
    "&family=DM+Sans:wght@400;500;700&display=swap');"
)

_CSS = """
.in-nav{display:flex;gap:14px;align-items:baseline;flex-wrap:wrap;font-family:'DM Sans',sans-serif;
  color:var(--tx2);font-size:.9rem;padding:.55rem 0}
.in-nav b{color:var(--ac);font-family:'Barlow Condensed',sans-serif;font-size:1.15rem;letter-spacing:1px}
.in-nav a{color:var(--achi);text-decoration:none;border-bottom:1px solid transparent}
.in-nav a:hover{border-bottom-color:var(--achi)}
.in-hero{position:relative;overflow:hidden;border-radius:22px;background:var(--grad);background-size:cover;
  background-position:center;border:1px solid color-mix(in srgb,var(--ac) 40%,transparent);
  display:flex;flex-direction:column;min-height:clamp(380px,50vw,540px)}
.in-cancha{position:absolute;inset:0;color:var(--ac);opacity:.11;pointer-events:none}
.in-cancha img{width:100%;height:100%;object-fit:cover;display:block}
.in-fila{position:relative;z-index:1;flex:1;display:flex;align-items:center;justify-content:space-between;
  gap:28px;flex-wrap:wrap;padding:clamp(24px,5vw,64px) clamp(22px,5vw,64px) clamp(16px,3vw,28px)}
.in-hero-txt{flex:1 1 380px}
.in-chip{display:inline-block;font-family:'Barlow Condensed',sans-serif;font-weight:600;font-size:1rem;
  letter-spacing:.5px;color:var(--achi);border:1px solid var(--ac);border-radius:999px;padding:.2rem .9rem;margin-bottom:1rem}
.in-hero .in-titulo{font-family:'Bebas Neue',Impact,sans-serif !important;font-size:clamp(3.6rem,13vw,9rem);
  line-height:.88;letter-spacing:.04em;font-weight:400;margin:0 0 .6rem;
  background:linear-gradient(95deg,var(--ac),var(--achi));-webkit-background-clip:text;background-clip:text;
  -webkit-text-fill-color:transparent;color:transparent;
  filter:drop-shadow(0 6px 24px color-mix(in srgb,var(--ac) 35%,transparent))}
.in-lema{font-family:'DM Sans',sans-serif;font-size:clamp(1rem,2.2vw,1.25rem);color:var(--tx);
  max-width:34ch;line-height:1.5;margin:0;text-shadow:0 2px 10px rgba(0,0,0,.6)}
.in-logo{flex:0 0 auto;display:flex;align-items:center;justify-content:center}
.in-logo img{width:clamp(120px,22vw,250px);filter:drop-shadow(0 10px 30px rgba(0,0,0,.55));
  animation:in-flota 5s ease-in-out infinite}
.in-logo img.in-bola{width:clamp(120px,20vw,220px)}
@keyframes in-flota{0%,100%{transform:translateY(0)}50%{transform:translateY(-12px)}}
.in-barra{position:relative;z-index:1;display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));
  margin:0 clamp(14px,3vw,34px) clamp(14px,3vw,34px);border-radius:16px;overflow:hidden;
  background:rgba(8,8,8,.58);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px)}
.in-dato{padding:14px 16px;text-align:center;border-left:1px solid rgba(255,255,255,.15)}
.in-dato:first-child{border-left:none}
.in-dato b{display:block;font-family:'Bebas Neue',sans-serif;font-weight:400;font-size:2rem;line-height:1;
  color:var(--achi);letter-spacing:2px}
.in-dato span{font-family:'DM Sans',sans-serif;font-size:.82rem;color:#E8E8E8}
.in-banner{position:relative;overflow:hidden;border-radius:22px;padding:clamp(24px,4vw,44px);margin-top:1.2rem;
  background:linear-gradient(120deg,color-mix(in srgb,var(--ac) 26%,var(--bg)),var(--bgc) 75%);
  border:1px solid var(--ac)}
.in-banner .in-cancha{opacity:.08}
.in-banner-grid{position:relative;display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:24px;align-items:center}
.in-banner .in-h-grande{font-family:'Bebas Neue',sans-serif !important;font-weight:400;
  font-size:clamp(2.6rem,7vw,4.8rem);letter-spacing:3px;line-height:.95;margin:0 0 .6rem;color:var(--tx)}
.in-banner p{font-family:'DM Sans',sans-serif;color:var(--tx);line-height:1.6;margin:0;max-width:52ch}
.in-cats{display:grid;gap:8px}
.in-cat{background:color-mix(in srgb,var(--bg) 72%,transparent);border-left:4px solid var(--ac);
  border-radius:0 12px 12px 0;padding:9px 14px;display:flex;justify-content:space-between;gap:12px;align-items:baseline}
.in-cat b{font-family:'Barlow Condensed',sans-serif;font-size:1.2rem;color:var(--achi);font-weight:700}
.in-cat span{font-family:'DM Sans',sans-serif;font-size:.85rem;color:var(--tx2)}
.in-banner.in-colegios{background:linear-gradient(240deg,color-mix(in srgb,var(--ac) 20%,var(--bg)),var(--bgc) 75%)}
.in-deps{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
.in-chipdep{display:flex;align-items:center;gap:10px;background:color-mix(in srgb,var(--bg) 72%,transparent);
  border-radius:12px;padding:8px 12px}
.in-chipdep img{width:34px;height:34px;flex:0 0 auto}
.in-chipdep span{font-family:'Barlow Condensed',sans-serif;font-weight:600;font-size:1.1rem;color:var(--tx)}
.in-h2{font-family:'Bebas Neue',sans-serif !important;font-weight:400;font-size:clamp(1.9rem,4.5vw,2.7rem);
  letter-spacing:3px;color:var(--tx);margin:2.2rem 0 .2rem;line-height:1}
.in-h2 em{font-style:normal;color:var(--ac)}
.in-sub{font-family:'DM Sans',sans-serif;color:var(--tx2);margin:0 0 1rem;max-width:62ch;line-height:1.55}
.in-deportes{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1px;
  background:color-mix(in srgb,var(--tx3) 60%,transparent);
  border:1px solid color-mix(in srgb,var(--tx3) 60%,transparent);border-radius:18px;overflow:hidden}
.in-dep{background:var(--bgc);padding:30px 22px 24px;text-align:center;transition:background .2s}
.in-dep:hover{background:color-mix(in srgb,var(--ac) 10%,var(--bgc))}
.in-dep img{width:68px;height:68px;display:block;margin:0 auto 14px;transition:transform .25s}
.in-dep:hover img{transform:translateY(-4px) rotate(-8deg)}
.in-dep .in-nombre{font-family:'Bebas Neue',sans-serif !important;font-weight:400;font-size:1.8rem;
  letter-spacing:2px;color:var(--tx);margin:0 0 6px;line-height:1.1}
.in-dep p{font-family:'DM Sans',sans-serif;font-size:.9rem;line-height:1.5;color:var(--tx2);margin:0 0 14px}
.in-regla{display:block;font-family:'Barlow Condensed',sans-serif;font-weight:600;font-size:1rem;letter-spacing:.5px;
  color:var(--achi);padding-top:10px;border-top:1px solid color-mix(in srgb,var(--tx3) 60%,transparent)}
.in-info{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}
.in-bloque{background:var(--bgc);border-left:3px solid var(--ac);border-radius:0 14px 14px 0;padding:18px 20px}
.in-bloque .in-nombre-b{font-family:'Barlow Condensed',sans-serif !important;font-size:1.4rem;font-weight:700;
  color:var(--achi);margin:0 0 4px}
.in-bloque p{font-family:'DM Sans',sans-serif;font-size:.92rem;line-height:1.55;color:var(--tx2);margin:0}
.in-pasos{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:0;counter-reset:paso}
.in-paso{padding:16px 18px 10px 0;border-top:3px solid var(--tx3)}
.in-paso:first-child{border-top-color:var(--ac)}
.in-paso::before{counter-increment:paso;content:counter(paso);font-family:'Bebas Neue',sans-serif;font-size:2.4rem;
  color:var(--ac);display:block;line-height:1;margin-bottom:4px}
.in-paso b{font-family:'Barlow Condensed',sans-serif;font-size:1.25rem;color:var(--tx);display:block}
.in-paso span{font-family:'DM Sans',sans-serif;font-size:.88rem;color:var(--tx2);line-height:1.5}
.in-pie{font-family:'DM Sans',sans-serif;text-align:center;color:var(--tx3);font-size:.78rem;
  margin:1.4rem 0 0;padding-top:.7rem;border-top:1px solid var(--tx3)}
.in-pie b{color:var(--ac);font-family:'Bebas Neue',sans-serif;letter-spacing:3px;font-size:1rem;font-weight:400;margin-right:.5rem}
.in-pie a{color:var(--tx2)}
[class*="st-key-entrar_"] button{width:100%;justify-content:center;min-height:4rem;margin-top:.5rem;
  background:linear-gradient(95deg,var(--ac),var(--achi));border:none;border-radius:16px;
  box-shadow:0 8px 28px color-mix(in srgb,var(--ac) 40%,transparent);transition:transform .15s,box-shadow .15s}
[class*="st-key-entrar_"] button:hover{transform:translateY(-2px);box-shadow:0 12px 34px color-mix(in srgb,var(--ac) 55%,transparent)}
[class*="st-key-entrar_"] button p{font-family:'Barlow Condensed',sans-serif;font-weight:700;
  font-size:clamp(1.3rem,3vw,1.7rem);letter-spacing:2px;color:#0A0A0A;text-transform:uppercase}
.st-key-tema_inicio button{border:1px solid var(--ac);border-radius:999px;background:transparent}
.st-key-tema_inicio button p{font-family:'Barlow Condensed',sans-serif;font-weight:600;font-size:1.05rem;color:var(--ac)}
@media (max-width:760px){.in-banner-grid{grid-template-columns:1fr}.in-logo{order:-1}.in-dato{border-left:none}
  .in-barra{grid-template-columns:repeat(2,1fr)}}
@media (prefers-reduced-motion:reduce){.in-logo img{animation:none}.in-dep,.in-dep img{transition:none}}
"""


def estilos() -> None:
    """Fuentes y estilos de la portada y del logo de la barra lateral.

    Se aplica en todas las vistas porque el logo vive en la barra lateral. Los
    colores salen del tema activo, así que cambiar de tema recolorea todo.
    """
    t = _paleta()
    variables = (
        f":root{{--ac:{t['ac']};--achi:{t['achi']};--bg:{t['bg']};--bgc:{t['bgc']};"
        f"--tx:{t['tx']};--tx2:{t['tx2']};--tx3:{t['tx3']};--grad:{t['grad']}}}"
    )
    logo = _logo()
    # El selector lleva el prefijo de la barra lateral y `!important` porque el
    # tema ya estiliza todos los botones como píldoras con fondo propio, y sin
    # esto ese estilo gana y el logo no se ve.
    lateral = 'section[data-testid="stSidebar"] .st-key-logo_inicio button'
    if logo:
        # Con logo, el botón ES el logo. Ocupa todo el ancho del menú y su alto
        # sale de la proporción de la imagen (`aspect-ratio`), así que crece y
        # encoge junto con la barra lateral sin deformarse.
        marca = (
            f"{lateral}{{background:url(\"{logo}\") center/contain no-repeat transparent !important;"
            "border:none !important;box-shadow:none !important;border-radius:0 !important;"
            "padding:0 !important;width:100% !important;height:auto !important;"
            f"min-height:0 !important;aspect-ratio:{_proporcion_logo()};"
            "transition:transform .15s,filter .15s}"
            f"{lateral} p{{font-size:0 !important;color:transparent !important}}"
            f"{lateral}:hover{{transform:scale(1.03);filter:brightness(1.15)}}"
        )
    else:
        marca = (
            f"{lateral}{{background:transparent !important;border:none !important;"
            "box-shadow:none !important;justify-content:flex-start;min-height:3rem}"
            f"{lateral} p{{font-family:'Bebas Neue',Impact,sans-serif;"
            "font-size:1.9rem;letter-spacing:4px;color:var(--ac);line-height:1}"
            f"{lateral}:hover p{{color:var(--achi)}}"
        )
    st.markdown(
        f"<style>{_FUENTES}{variables}{_CSS}{marca}</style>", unsafe_allow_html=True
    )


# ── Piezas de la página ─────────────────────────────────────────────────────

_SITIO_OFICIAL = "https://www.etitc.edu.co/es/"


def _nav() -> str:
    return (
        '<div class="in-nav"><b>ETITC</b><span>Bogotá, Colombia</span>'
        f'<a href="{_SITIO_OFICIAL}" target="_blank" rel="noopener noreferrer">Sitio oficial</a></div>'
    )


def _datos() -> str:
    datos = (
        (str(len(DEPORTES)), "deportes"),
        ("3", "categorías"),
        ("6° a 11°", "cursos"),
        ("1", "campeón por torneo"),
    )
    celdas = "".join(f'<div class="in-dato"><b>{n}</b><span>{d}</span></div>' for n, d in datos)
    return f'<div class="in-barra">{celdas}</div>'


def _hero() -> str:
    portada = _portada()
    fondo = (
        f' style="background-image:linear-gradient(95deg,rgba(0,0,0,.82),rgba(0,0,0,.30)),url({portada})"'
        if portada
        else ""
    )
    logo = _logo()
    imagen = f'<img src="{logo}" alt="Logo de ITC Deportes">' if logo else _figura("futbol", "in-bola")
    return (
        f'<section class="in-hero"{fondo}>'
        f"{_cancha()}"
        '<div class="in-fila"><div class="in-hero-txt">'
        '<span class="in-chip">Escuela Tecnológica Instituto Técnico Central</span>'
        f'{_titulo(1, "in-titulo", "ITC Deportes")}'
        '<p class="in-lema">Todos los deportes de la ETITC en un solo lugar. '
        "Mira tablas, calendarios y cuadros finales sin tener que preguntar a nadie.</p>"
        f'</div><div class="in-logo">{imagen}</div></div>'
        f"{_datos()}"
        "</section>"
    )


def _banner() -> str:
    categorias = (
        ("Primera", "601 a 708"),
        ("Segunda", "801 a 906"),
        ("Tercera", "1001 a 1104"),
    )
    cats = "".join(f'<div class="in-cat"><b>{n}</b><span>Cursos {d}</span></div>' for n, d in categorias)
    return (
        '<section class="in-banner">'
        f"{_cancha()}"
        '<div class="in-banner-grid"><div>'
        f'{_titulo(2, "in-h-grande", "Intercursos")}'
        "<p>El torneo donde cada curso defiende sus colores. Empieza con una fase de "
        "grupos, sigue con eliminación directa y termina con un campeón.</p></div>"
        f'<div class="in-cats">{cats}</div></div>'
        "</section>"
    )


def _banner_intercolegiados() -> str:
    deportes = "".join(
        f'<div class="in-chipdep">{_figura(d.figura)}<span>{d.nombre}</span></div>'
        for d in DEPORTES
    )
    return (
        '<section class="in-banner in-colegios">'
        f"{_cancha()}"
        '<div class="in-banner-grid"><div>'
        f'{_titulo(2, "in-h-grande", "Intercolegiados")}'
        "<p>Cuando la ETITC sale a competir con otros colegios. Los equipos "
        "institucionales representan a la escuela en los cuatro deportes.</p></div>"
        f'<div class="in-deps">{deportes}</div></div>'
        "</section>"
    )


def _deportes(titulo: str = "Los deportes de la <em>ETITC</em>", resumen: str = "Cada deporte tiene su propia forma de puntuar, y la tabla de posiciones la respeta.") -> str:
    tarjetas = "".join(
        '<article class="in-dep">'
        f'{_figura(d.figura)}'
        f'{_titulo(3, "in-nombre", d.nombre)}<p>{d.resumen}</p>'
        f'<span class="in-regla">{d.regla}</span>'
        "</article>"
        for d in DEPORTES
    )
    return (
        f'{_titulo(2, "in-h2", titulo)}'
        f'<p class="in-sub">{resumen}</p>'
        f'<div class="in-deportes">{tarjetas}</div>'
    )


def _informacion() -> str:
    bloques = (
        ("Consulta sin cuenta",
         "Cualquiera puede ver tablas, resultados y calendarios. No hace falta registrarse."),
        ("Sigue el cuadro final",
         "Los mejores de la fase de grupos pasan al cuadro, y cada ganador avanza solo a la ronda siguiente."),
        ("Registra los resultados",
         "Quienes tienen permiso cargan los marcadores de su competición y pueden corregirlos."),
    )
    tarjetas = "".join(
        f'<div class="in-bloque">{_titulo(3, "in-nombre-b", t)}<p>{p}</p></div>' for t, p in bloques
    )
    pasos = (
        ("Inscripción", "Cada curso inscribe a su equipo."),
        ("Sorteo", "El sistema arma el calendario de jornadas."),
        ("Jornadas", "Se juegan los partidos y se anotan los marcadores."),
        ("Cuadro final", "Los mejores clasificados se enfrentan hasta quedar uno."),
    )
    lista = "".join(f'<div class="in-paso"><b>{t}</b><span>{d}</span></div>' for t, d in pasos)
    return (
        f'{_titulo(2, "in-h2", "Qué puedes hacer <em>aquí</em>")}'
        f'<div class="in-info">{tarjetas}</div>'
        f'{_titulo(2, "in-h2", "Cómo se juega un <em>torneo</em>")}'
        f'<div class="in-pasos">{lista}</div>'
    )


def _pie() -> str:
    return (
        '<div class="in-pie"><b>ITC Deportes</b>Sistema de gestión deportiva de la '
        f'<a href="{_SITIO_OFICIAL}" target="_blank" rel="noopener noreferrer">ETITC</a></div>'
    )


def _cabecera() -> None:
    """Barra superior con el tema; la comparten la portada y los Intercolegiados."""
    t = _paleta()
    st.markdown(
        "<style>[data-testid='stMainBlockContainer'],.stMain .block-container"
        "{padding-bottom:1.2rem !important}</style>",
        unsafe_allow_html=True,
    )
    izquierda, derecha = st.columns([4, 1])
    izquierda.markdown(_nav(), unsafe_allow_html=True)
    derecha.button(
        f"{t['ico']} {t['lbl']}",
        key="tema_inicio",
        on_click=tema.alternar,
        width="stretch",
    )


def _boton_de_entrada(clave: str, texto: str, vista: str) -> None:
    st.button(
        texto, key=clave, type="primary", on_click=ir_a, args=(vista,), width="stretch"
    )


def pagina() -> None:
    """Dibuja la portada completa.

    El orden es el de importancia: lo primero que se ve es a dónde entrar
    (Intercursos e Intercolegiados), y el resto es información de apoyo.
    """
    _cabecera()
    st.markdown(_hero(), unsafe_allow_html=True)
    st.markdown(_banner(), unsafe_allow_html=True)
    _boton_de_entrada("entrar_intercursos", "Entrar a los Intercursos", "intercursos")
    st.markdown(_banner_intercolegiados(), unsafe_allow_html=True)
    _boton_de_entrada(
        "entrar_intercolegiados", "Entrar a los Intercolegiados", "intercolegiados"
    )
    st.markdown(_deportes(), unsafe_allow_html=True)
    st.markdown(_informacion(), unsafe_allow_html=True)
    st.markdown(_pie(), unsafe_allow_html=True)
