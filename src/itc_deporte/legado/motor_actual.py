"""Las partes puras del sistema actual, extraídas sin cambiarles el comportamiento.

Fase 0 del plan de refactor: separar de las llamadas HTTP lo que ya era código
puro, para poder fijarlo con tests antes de reescribirlo. Lo que hay aquí es el
comportamiento vigente —rarezas incluidas— y sirve como referencia contra la que
contrastar el motor nuevo.

Las rarezas están señaladas en los comentarios, y no se corrigen aquí: cambiarlas
sería mezclar refactor con cambio de comportamiento en el mismo commit.
"""

from __future__ import annotations

import re


def generar_cursos(grado: int, cantidad: int) -> list[str]:
    return [f"{grado}{i:02d}" for i in range(1, cantidad + 1)]


CATEGORIAS_LOCAL = {
    "PRIMERA": generar_cursos(6, 9) + generar_cursos(7, 8),
    "SEGUNDA": generar_cursos(8, 8) + generar_cursos(9, 6),
    "TERCERA": generar_cursos(10, 3) + generar_cursos(11, 4),
}

DEPORTES = ["Balonmano", "Microfutbol", "Baloncesto", "Voleyball"]

ICONOS_DEP = {
    "Balonmano": "🤾",
    "Microfutbol": "⚽",
    "Baloncesto": "🏀",
    "Voleyball": "🏐",
}

CURSOS_VALIDOS = set(
    generar_cursos(6, 9)
    + generar_cursos(7, 8)
    + generar_cursos(8, 8)
    + generar_cursos(9, 6)
    + generar_cursos(10, 3)
    + generar_cursos(11, 4)
)

# ── Parseo de enfrentamientos ────────────────────────────────────────────────
# La identidad de un equipo es el texto "Nombre (Curso)" y hay que recuperarla
# con expresiones regulares. Es el origen de la corrupción de datos que
# `limpiar_equipos_corruptos()` intenta contener. Muere en la Fase 7.


def parsear_lado(texto):
    texto = str(texto).strip()
    m = re.match(
        r"^[\(\[]\s*['\"](.+?)['\"]\s*,\s*['\"](.+?)['\"]\s*[\)\]](\s*\(\?\))?$", texto
    )
    if m:
        return m.group(1).strip(), m.group(2).strip()
    ultimo = texto.rfind("(")
    if ultimo != -1 and texto.endswith(")"):
        nombre = texto[:ultimo].strip()
        curso = texto[ultimo + 1 : -1].strip()
        if nombre:
            return nombre, curso
    return texto, "?"


def parsear_enf(enf):
    if not isinstance(enf, str):
        return None
    idx = enf.find(" vs ")
    if idx == -1:
        return None
    n1, c1 = parsear_lado(enf[:idx])
    n2, c2 = parsear_lado(enf[idx + 4 :])
    if not n1 or not n2:
        return None
    return n1, c1, n2, c2


def enf_limpio(enf):
    """Devuelve texto legible del enfrentamiento."""
    p = parsear_enf(enf)
    if p:
        return f"{p[0]} ({p[1]}) vs {p[2]} ({p[3]})"
    return enf


# ── Fixture ──────────────────────────────────────────────────────────────────


def generar_round_robin(equipos):
    """Round-robin por el método del círculo.

    Rareza vigente: en lugar de devolver las n-1 jornadas naturales, repite o
    trunca el calendario hasta dejar exactamente 7. Ver §12 del plan.
    """
    eqs = list(equipos)
    if len(eqs) % 2 != 0:
        eqs.append("BYE")
    n, fijo, rotat, rondas = len(eqs), eqs[0], eqs[1:], []
    for ronda in range(n - 1):
        circulo = [fijo] + rotat
        enfs = []
        for i in range(n // 2):
            e1, e2 = circulo[i], circulo[n - 1 - i]
            enfs.append((e1, e2) if ronda % 2 == 0 else (e2, e1))
        rondas.append(enfs)
        rotat = [rotat[-1]] + rotat[:-1]
    return [rondas[i % len(rondas)] for i in range(7)] if rondas else []


# ── Bracket ──────────────────────────────────────────────────────────────────

RONDA_ORDEN = ["OCTAVOS", "CUARTOS", "SEMIFINAL", "FINAL"]

RONDA_LABEL = {
    "OCTAVOS": "Octavos de Final",
    "CUARTOS": "Cuartos de Final",
    "SEMIFINAL": "Semifinal",
    "FINAL": "Final",
}


def tamano_bracket(n):
    """Rareza vigente: por encima de 16 se recorta a 16 en vez de crecer."""
    for size in (2, 4, 8, 16):
        if n <= size:
            return size
    return 16


def gen_seeds(size):
    """Orden de siembra estándar de bracket (1 vs último, 2 vs penúltimo, etc.)."""
    seeds = [1]
    while len(seeds) < size:
        n = len(seeds) * 2
        nuevos = []
        for s in seeds:
            nuevos.append(s)
            nuevos.append(n + 1 - s)
        seeds = nuevos
    return seeds


def ganador_llave(row):
    if row["estado"] != "Finalizado":
        return None, None
    if row["g1"] > row["g2"]:
        return row["equipo1"], row["curso1"]
    if row["g2"] > row["g1"]:
        return row["equipo2"], row["curso2"]
    return None, None


# ── Tabla de posiciones ──────────────────────────────────────────────────────


def calcular_tabla_desde(partidos, equipos):
    """Núcleo puro de `calcular_tabla`, sin las dos consultas a la base.

    `partidos` son filas `[id, fecha, enf, estado, g1, g2]`; `equipos` es el
    diccionario `{curso: [nombres]}`.

    Rarezas vigentes: puntúa 3/1/0 sobre "goles" para los cuatro deportes, de
    modo que un partido de voleibol puede terminar empatado (§12 y problema 6
    del diagnóstico).
    """
    tabla = {}
    for p in partidos:
        _, fecha, enf, estado, g1, g2 = p
        if estado != "Finalizado":
            continue
        parsed = parsear_enf(enf)
        if not parsed:
            continue
        n1, c1, n2, c2 = parsed
        if c1 not in CURSOS_VALIDOS or c2 not in CURSOS_VALIDOS:
            continue
        for n, c in [(n1, c1), (n2, c2)]:
            k = f"{n}|{c}"
            if k not in tabla:
                tabla[k] = dict(
                    Equipo=n, Curso=c, PJ=0, PG=0, PE=0, PP=0, GF=0, GC=0, Pts=0
                )
        k1, k2 = f"{n1}|{c1}", f"{n2}|{c2}"
        for k in (k1, k2):
            tabla[k]["PJ"] += 1
        tabla[k1]["GF"] += g1
        tabla[k1]["GC"] += g2
        tabla[k2]["GF"] += g2
        tabla[k2]["GC"] += g1
        if g1 > g2:
            tabla[k1]["PG"] += 1
            tabla[k1]["Pts"] += 3
            tabla[k2]["PP"] += 1
        elif g2 > g1:
            tabla[k2]["PG"] += 1
            tabla[k2]["Pts"] += 3
            tabla[k1]["PP"] += 1
        else:
            tabla[k1]["PE"] += 1
            tabla[k1]["Pts"] += 1
            tabla[k2]["PE"] += 1
            tabla[k2]["Pts"] += 1

    for cur, eqs in equipos.items():
        for eq in eqs:
            k = f"{eq}|{cur}"
            if k not in tabla:
                tabla[k] = dict(
                    Equipo=eq, Curso=cur, PJ=0, PG=0, PE=0, PP=0, GF=0, GC=0, Pts=0
                )

    rows = sorted(
        tabla.values(), key=lambda x: (-x["Pts"], -(x["GF"] - x["GC"]), -x["GF"])
    )
    for i, r in enumerate(rows):
        r["#"] = i + 1
        r["DG"] = r["GF"] - r["GC"]
    return rows
