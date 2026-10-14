"""La pantalla de entrada: lo primero que ve quien abre ITC Deportes.

Presenta los deportes de la ETITC y lleva a los Intercursos. No decide nada del
negocio: no llama a ningún servicio, así que no puede fallar por la base de datos
y tampoco tiene permisos que comprobar.

La navegación es una sola clave de sesión, `vista`: `"inicio"` o `"intercursos"`.
El logo de la barra lateral y los botones de esta página solo la cambian.

Imágenes: las ilustraciones de los deportes son SVG incrustado, así que no hay
nada que descargar ni enlaces que se rompan. Si existen, se usan además:

- `static/logo_itc-deportes.png`: el logo (hero y barra lateral).
- `static/portada.jpg` (o `.png` / `.webp`): foto de fondo del hero.
"""

from __future__ import annotations

import base64
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

VISTAS = ("inicio", "intercursos")


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


# ── Contenido ───────────────────────────────────────────────────────────────
# Para añadir un deporte basta con una línea aquí. `figura` elige la ilustración.


@dataclass(frozen=True)
class DeporteDeLaEscuela:
    nombre: str
    figura: str
    resumen: str
    datos: tuple[str, ...]


DEPORTES = (
    DeporteDeLaEscuela(
        "Microfútbol", "futbol",
        "El clásico del patio: espacios cortos, toque rápido y gol en cada jugada.",
        ("Equipos", "Puntúa 3 / 1 / 0"),
    ),
    DeporteDeLaEscuela(
        "Baloncesto", "baloncesto",
        "Ritmo, defensa y triples. Cada posesión puede cambiar el partido.",
        ("Equipos", "Puntúa 3 / 1 / 0"),
    ),
    DeporteDeLaEscuela(
        "Voleyball", "voleibol",
        "Se juega por sets: un 3-2 reparte puntos a los dos equipos.",
        ("Equipos", "Puntúa por sets"),
    ),
    DeporteDeLaEscuela(
        "Balonmano", "balonmano",
        "Velocidad, pase y potencia en una cancha que no perdona descuidos.",
        ("Equipos", "Puntúa 3 / 1 / 0"),
    ),
)

_FIGURAS = {
    "futbol": (
        '<circle cx="32" cy="32" r="28"/>'
        '<polygon points="32,20 43,28 39,41 25,41 21,28" fill="currentColor"/>'
        '<path d="M32 20V5M43 28l14-5M39 41l8 12M25 41l-8 12M21 28L7 23"/>'
    ),
    "baloncesto": (
        '<circle cx="32" cy="32" r="28"/>'
        '<path d="M4 32h56M32 4v56M11 11c11 11 11 31 0 42M53 11c-11 11-11 31 0 42"/>'
    ),
    "voleibol": (
        '<circle cx="32" cy="32" r="28"/>'
        '<path d="M32 4c1 14 9 23 24 27M10 14c12 3 20 10 22 18M8 44c13-5 24-3 31 10'
        'M32 32c-4 9-4 18 0 28"/>'
    ),
    "balonmano": (
        '<circle cx="32" cy="32" r="28"/>'
        '<path d="M32 4v56M7 22c16 7 34 7 50 0M7 42c16-7 34-7 50 0"/>'
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


# ── Estilos ─────────────────────────────────────────────────────────────────

_FUENTES = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Bebas+Neue&family=Barlow+Condensed:wght@500;600;700"
    "&family=DM+Sans:wght@400;500;700&display=swap');"
)

_CSS = """
.in-nav{font-family:'DM Sans',sans-serif;color:var(--tx2);font-size:.9rem;padding:.55rem 0}
.in-nav b{color:var(--ac);font-family:'Barlow Condensed',sans-serif;font-size:1.15rem;letter-spacing:1px}
.in-hero{position:relative;overflow:hidden;border-radius:22px;
  padding:clamp(28px,6vw,76px);background:var(--grad);background-size:cover;background-position:center;
  border:1px solid color-mix(in srgb,var(--ac) 40%,transparent);
  display:flex;align-items:center;justify-content:space-between;gap:28px;flex-wrap:wrap}
.in-cancha{position:absolute;inset:0;color:var(--ac);opacity:.11}
.in-cancha img{width:100%;height:100%;object-fit:cover;display:block}
.in-hero-txt{position:relative;z-index:1;flex:1 1 380px}
.in-chip{display:inline-block;font-family:'Barlow Condensed',sans-serif;font-weight:600;font-size:1rem;
  letter-spacing:.5px;color:var(--achi);border:1px solid var(--ac);border-radius:999px;padding:.2rem .9rem;margin-bottom:1rem}
.in-titulo{font-family:'Bebas Neue',Impact,sans-serif;font-size:clamp(3.6rem,13vw,9rem);line-height:.88;
  letter-spacing:.04em;margin:0 0 .6rem;
  background:linear-gradient(95deg,var(--ac),var(--achi));-webkit-background-clip:text;background-clip:text;
  color:transparent;filter:drop-shadow(0 6px 24px color-mix(in srgb,var(--ac) 35%,transparent))}
.in-lema{font-family:'DM Sans',sans-serif;font-size:clamp(1rem,2.2vw,1.25rem);color:var(--tx);
  max-width:34ch;line-height:1.5;margin:0}
.in-logo{position:relative;z-index:1;flex:0 0 auto;display:flex;align-items:center;justify-content:center}
.in-logo img{width:clamp(120px,22vw,250px);filter:drop-shadow(0 10px 30px rgba(0,0,0,.55));
  animation:in-flota 5s ease-in-out infinite}
.in-logo img.in-bola{width:clamp(120px,20vw,220px)}
@keyframes in-flota{0%,100%{transform:translateY(0)}50%{transform:translateY(-12px)}}
.in-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:18px 0 6px}
.in-stat{background:var(--bgc);border-radius:14px;padding:16px 18px;border-bottom:3px solid var(--ac)}
.in-stat b{display:block;font-family:'Bebas Neue',sans-serif;font-size:2.4rem;line-height:1;color:var(--achi);letter-spacing:2px}
.in-stat span{font-family:'DM Sans',sans-serif;font-size:.85rem;color:var(--tx2)}
.in-h2{font-family:'Bebas Neue',sans-serif;font-size:clamp(2rem,5vw,3rem);letter-spacing:3px;color:var(--tx);
  margin:2.4rem 0 .2rem;line-height:1}
.in-h2 em{font-style:normal;color:var(--ac)}
.in-sub{font-family:'DM Sans',sans-serif;color:var(--tx2);margin:0 0 1rem;max-width:62ch;line-height:1.55}
.in-deportes{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px}
.in-dep{position:relative;overflow:hidden;background:var(--bgc);border-radius:18px;padding:24px 22px 22px;
  border:1px solid color-mix(in srgb,var(--tx3) 60%,transparent);transition:transform .2s,border-color .2s}
.in-dep:hover{transform:translateY(-5px);border-color:var(--ac)}
.in-dep img{width:100%;height:auto;display:block}
.in-dep .in-fig{position:absolute;right:-18px;top:-18px;width:120px;color:var(--ac);opacity:.14}
.in-dep .in-ico{width:54px;color:var(--ac);display:block;margin-bottom:14px}
.in-dep h3{font-family:'Bebas Neue',sans-serif;font-size:2rem;letter-spacing:2px;margin:0 0 6px;color:var(--tx)}
.in-dep p{font-family:'DM Sans',sans-serif;font-size:.93rem;line-height:1.5;color:var(--tx2);margin:0 0 14px}
.in-etq{display:flex;gap:6px;flex-wrap:wrap}
.in-etq span{font-family:'Barlow Condensed',sans-serif;font-weight:600;font-size:.95rem;color:var(--achi);
  background:color-mix(in srgb,var(--ac) 14%,transparent);border-radius:8px;padding:.1rem .6rem}
.in-banner{position:relative;overflow:hidden;border-radius:22px;padding:clamp(26px,5vw,56px);margin-top:2.2rem;
  background:linear-gradient(120deg,color-mix(in srgb,var(--ac) 28%,var(--bg)),var(--bgc) 70%);
  border:1px solid var(--ac)}
.in-banner .in-cancha{opacity:.08}
.in-banner h2{position:relative;font-family:'Bebas Neue',sans-serif;font-size:clamp(2.4rem,7vw,4.6rem);
  letter-spacing:3px;line-height:.95;margin:0 0 .6rem;color:var(--tx)}
.in-banner p{position:relative;font-family:'DM Sans',sans-serif;color:var(--tx);max-width:58ch;line-height:1.6;margin:0 0 1rem}
.in-cats{position:relative;display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:0 0 .4rem}
.in-cat{background:color-mix(in srgb,var(--bg) 70%,transparent);border-left:4px solid var(--ac);
  border-radius:0 12px 12px 0;padding:10px 14px}
.in-cat b{font-family:'Barlow Condensed',sans-serif;font-size:1.2rem;color:var(--achi);display:block}
.in-cat span{font-family:'DM Sans',sans-serif;font-size:.85rem;color:var(--tx2)}
.in-info{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px}
.in-bloque{background:var(--bgc);border-radius:16px;padding:22px;border-top:3px solid var(--ac)}
.in-bloque h3{font-family:'Barlow Condensed',sans-serif;font-size:1.5rem;font-weight:700;color:var(--achi);margin:0 0 6px}
.in-bloque p{font-family:'DM Sans',sans-serif;font-size:.93rem;line-height:1.55;color:var(--tx2);margin:0}
.in-pasos{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:0;counter-reset:paso}
.in-paso{position:relative;padding:18px 18px 18px 0;border-top:3px solid var(--tx3)}
.in-paso:first-child{border-top-color:var(--ac)}
.in-paso::before{counter-increment:paso;content:counter(paso);font-family:'Bebas Neue',sans-serif;font-size:2.6rem;
  color:var(--ac);display:block;line-height:1;margin-bottom:4px}
.in-paso b{font-family:'Barlow Condensed',sans-serif;font-size:1.25rem;color:var(--tx);display:block}
.in-paso span{font-family:'DM Sans',sans-serif;font-size:.88rem;color:var(--tx2);line-height:1.5}
.in-pie{font-family:'DM Sans',sans-serif;text-align:center;color:var(--tx3);font-size:.82rem;
  margin:3rem 0 1rem;padding-top:1.2rem;border-top:1px solid var(--tx3)}
.in-pie b{color:var(--ac);font-family:'Bebas Neue',sans-serif;letter-spacing:3px;font-size:1.1rem;font-weight:400}
[class*="st-key-entrar_"] button{background:linear-gradient(95deg,var(--ac),var(--achi));border:none;
  border-radius:999px;padding:.65rem 2.2rem;box-shadow:0 8px 26px color-mix(in srgb,var(--ac) 40%,transparent);
  transition:transform .15s,box-shadow .15s}
[class*="st-key-entrar_"] button:hover{transform:translateY(-2px) scale(1.02)}
[class*="st-key-entrar_"] button p{font-family:'Barlow Condensed',sans-serif;font-weight:700;font-size:1.35rem;
  letter-spacing:1.5px;color:#0A0A0A}
.st-key-tema_inicio button{border:1px solid var(--ac);border-radius:999px;background:transparent}
.st-key-tema_inicio button p{font-family:'Barlow Condensed',sans-serif;font-weight:600;font-size:1.05rem;color:var(--ac)}
:is(.in-dep,.in-bloque,.in-stat):focus-within{outline:2px solid var(--ac)}
@media (max-width:640px){.in-hero{text-align:left}.in-logo{order:-1}.in-paso{padding-right:8px}}
@media (prefers-reduced-motion:reduce){.in-logo img{animation:none}.in-dep{transition:none}}
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
    if logo:
        # Con logo, el botón ES el logo: la imagen de fondo y la etiqueta oculta
        # (sigue ahí para lectores de pantalla).
        marca = (
            ".st-key-logo_inicio button{background-color:transparent;border:none;"
            f"background-image:url({logo});background-repeat:no-repeat;"
            "background-position:center;background-size:contain;min-height:110px;"
            "transition:transform .15s,filter .15s}"
            ".st-key-logo_inicio button p{font-size:0;color:transparent}"
            ".st-key-logo_inicio button:hover{transform:scale(1.04);filter:brightness(1.15)}"
        )
    else:
        marca = (
            ".st-key-logo_inicio button{background:transparent;border:none;"
            "justify-content:flex-start;min-height:3rem}"
            ".st-key-logo_inicio button p{font-family:'Bebas Neue',Impact,sans-serif;"
            "font-size:1.9rem;letter-spacing:4px;color:var(--ac);line-height:1}"
            ".st-key-logo_inicio button:hover p{color:var(--achi)}"
        )
    st.markdown(
        f"<style>{_FUENTES}{variables}{_CSS}{marca}</style>", unsafe_allow_html=True
    )


# ── Piezas de la página ─────────────────────────────────────────────────────


def _hero() -> str:
    portada = _portada()
    fondo = (
        f' style="background-image:linear-gradient(95deg,rgba(0,0,0,.82),rgba(0,0,0,.35)),url({portada})"'
        if portada
        else ""
    )
    logo = _logo()
    imagen = f'<img src="{logo}" alt="Logo de ITC Deportes">' if logo else _figura("futbol", "in-bola")
    return (
        f'<section class="in-hero"{fondo}>'
        f'{_cancha()}'
        '<div class="in-hero-txt">'
        '<span class="in-chip">Escuela Tecnológica Instituto Técnico Central</span>'
        '<h1 class="in-titulo">ITC Deportes</h1>'
        '<p class="in-lema">Todos los deportes de la ETITC en un solo lugar. '
        "Mira tablas, calendarios y cuadros finales sin tener que preguntar a nadie.</p>"
        "</div>"
        f'<div class="in-logo">{imagen}</div>'
        "</section>"
    )


def _estadisticas() -> str:
    datos = (
        (str(len(DEPORTES)), "deportes en un mismo sitio"),
        ("3", "categorías: Primera, Segunda y Tercera"),
        ("6° a 11°", "cursos que compiten"),
        ("1", "campeón por competición"),
    )
    celdas = "".join(f'<div class="in-stat"><b>{n}</b><span>{d}</span></div>' for n, d in datos)
    return f'<div class="in-stats">{celdas}</div>'


def _deportes() -> str:
    tarjetas = "".join(
        '<article class="in-dep">'
        f'<div class="in-fig">{_figura(d.figura)}</div>'
        f'<div class="in-ico">{_figura(d.figura)}</div>'
        f"<h3>{d.nombre}</h3><p>{d.resumen}</p>"
        f'<div class="in-etq">{"".join(f"<span>{x}</span>" for x in d.datos)}</div>'
        "</article>"
        for d in DEPORTES
    )
    return (
        '<h2 class="in-h2">Los deportes de la <em>ETITC</em></h2>'
        '<p class="in-sub">Cada deporte tiene su propia forma de puntuar, y la tabla '
        "de posiciones la respeta.</p>"
        f'<div class="in-deportes">{tarjetas}</div>'
    )


def _banner() -> str:
    categorias = (
        ("Primera", "Cursos 601 a 708"),
        ("Segunda", "Cursos 801 a 906"),
        ("Tercera", "Cursos 1001 a 1104"),
    )
    cats = "".join(
        f'<div class="in-cat"><b>{n}</b><span>{d}</span></div>' for n, d in categorias
    )
    return (
        '<section class="in-banner">'
        f'{_cancha()}'
        "<h2>Intercursos</h2>"
        "<p>El torneo donde cada curso defiende sus colores. Empieza con una fase de "
        "grupos, sigue con eliminación directa y termina con un campeón.</p>"
        f'<div class="in-cats">{cats}</div>'
        "</section>"
    )


def _informacion() -> str:
    bloques = (
        ("Consulta sin cuenta",
         "Cualquiera puede ver tablas, resultados y calendarios. No hace falta registrarse."),
        ("Sigue el cuadro final",
         "Cuando termina la fase de grupos, los mejores clasificados pasan al cuadro y "
         "cada ganador avanza solo a la ronda siguiente."),
        ("Registra los resultados",
         "Los profesores y estudiantes autorizados cargan los marcadores de su competición. "
         "Si se equivocan, pueden corregirlos."),
    )
    tarjetas = "".join(
        f'<div class="in-bloque"><h3>{t}</h3><p>{p}</p></div>' for t, p in bloques
    )
    pasos = (
        ("Inscripción", "Cada curso inscribe a su equipo."),
        ("Sorteo", "El sistema arma el calendario de jornadas."),
        ("Jornadas", "Se juegan los partidos y se anotan los marcadores."),
        ("Cuadro final", "Los mejores clasificados se enfrentan hasta quedar uno."),
    )
    lista = "".join(f"<div class=\"in-paso\"><b>{t}</b><span>{d}</span></div>" for t, d in pasos)
    return (
        '<h2 class="in-h2">Qué puedes hacer <em>aquí</em></h2>'
        f'<div class="in-info">{tarjetas}</div>'
        '<h2 class="in-h2">Cómo se juega un <em>torneo</em></h2>'
        '<p class="in-sub">Así avanza una competición, de la inscripción al campeón.</p>'
        f'<div class="in-pasos">{lista}</div>'
    )


def _pie() -> str:
    return (
        '<div class="in-pie"><b>ITC Deportes</b><br>'
        "Sistema de gestión deportiva de la Escuela Tecnológica Instituto Técnico Central.</div>"
    )


def _boton_de_entrada(clave: str) -> None:
    st.button(
        "Entrar a los Intercursos",
        key=clave,
        type="primary",
        on_click=ir_a,
        args=("intercursos",),
    )


def pagina() -> None:
    """Dibuja la portada completa."""
    t = _paleta()
    izquierda, derecha = st.columns([4, 1])
    izquierda.markdown(
        '<div class="in-nav"><b>ETITC</b> Bogotá, Colombia</div>', unsafe_allow_html=True
    )
    derecha.button(
        f"{t['ico']} {t['lbl']}",
        key="tema_inicio",
        on_click=tema.alternar,
        width="stretch",
    )

    st.markdown(_hero(), unsafe_allow_html=True)
    _boton_de_entrada("entrar_hero")
    st.markdown(_estadisticas(), unsafe_allow_html=True)
    st.markdown(_deportes(), unsafe_allow_html=True)
    st.markdown(_banner(), unsafe_allow_html=True)
    _boton_de_entrada("entrar_banner")
    st.markdown(_informacion(), unsafe_allow_html=True)
    st.markdown(_pie(), unsafe_allow_html=True)
