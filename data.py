"""
data.py — ITC Deportes con Supabase
Reemplaza el archivo JSON por una base de datos real.
"""
import json
import random
import datetime
import streamlit as st
from supabase import create_client, Client

# ── Constantes ─────────────────────────────────────────────────────────────────

def generar_cursos(grado, cantidad):
    return [f"{grado}{i:02d}" for i in range(1, cantidad + 1)]

CATEGORIAS_LOCAL = {
    "PRIMERA": generar_cursos(6, 9) + generar_cursos(7, 8),
    "SEGUNDA": generar_cursos(8, 8) + generar_cursos(9, 6),
    "TERCERA": generar_cursos(10, 3) + generar_cursos(11, 4),
}

EQUIPOS_POR_CURSO = {
    "601": "Halcones FC",      "602": "Pumas FC",         "603": "Condores FC",
    "604": "Jaguares FC",      "605": "Leones FC",        "606": "Dragones FC",
    "607": "Guerreros FC",     "608": "Titanes FC",       "609": "Aguilas FC",
    "701": "Fenix FC",         "702": "Lobos FC",         "703": "Raptors FC",
    "704": "Tigres FC",        "705": "Spartans FC",      "706": "Truenos FC",
    "707": "Centellas FC",     "708": "Gladiadores FC",
    "801": "Tiburones FC",     "802": "Panteras FC",      "803": "Escorpiones FC",
    "804": "Huracanes FC",     "805": "Toros FC",         "806": "Buhos FC",
    "807": "Zorros FC",        "808": "Cobras FC",
    "901": "Lobos Negros FC",  "902": "Flamas FC",        "903": "Vikingos FC",
    "904": "Corsarios FC",     "905": "Rayos FC",         "906": "Cometas FC",
    "1001": "Elite FC",        "1002": "Fenix D.C FC",    "1003": "Eagles FC",
    "1101": "Lobos Dorados FC","1102": "Raptors Sur FC",  "1103": "Spartans Pro FC",
    "1104": "Titanes Pro FC",
}

DEPORTES    = ["Balonmano", "Microfutbol", "Baloncesto", "Voleyball"]
ICONOS_DEP  = {"Balonmano":"🤾","Microfutbol":"⚽","Baloncesto":"🏀","Voleyball":"🏐"}

USUARIOS      = {"admin": "1234"}
USUARIOS_TIPO = {"admin": "profesor"}

# ── Conexión Supabase (cached para no reconectar en cada rerun) ─────────────────

@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def db() -> Client:
    return get_supabase()

# ── EQUIPOS ────────────────────────────────────────────────────────────────────

def obtener_equipos(categoria: str, deporte: str) -> dict:
    """Retorna {curso: [nombre, ...]} para la categoría y deporte dados."""
    res = (db().table("equipos")
               .select("curso, nombre")
               .eq("categoria", categoria)
               .eq("deporte", deporte)
               .execute())
    resultado = {}
    for row in res.data:
        resultado.setdefault(row["curso"], []).append(row["nombre"])
    return resultado


def agregar_equipo(categoria: str, deporte: str, curso: str, nombre: str) -> str | None:
    """Inserta un equipo. Retorna None si OK, mensaje de error si falla."""
    try:
        db().table("equipos").insert({
            "categoria": categoria,
            "deporte":   deporte,
            "curso":     curso,
            "nombre":    nombre,
        }).execute()
        return None
    except Exception as e:
        msg = str(e)
        if "unique" in msg.lower() or "duplicate" in msg.lower():
            return "Ese equipo ya existe."
        return f"Error: {msg}"

# ── JUGADORES ──────────────────────────────────────────────────────────────────

def obtener_jugadores(categoria: str, deporte: str, curso: str, equipo: str) -> list:
    """Retorna lista de dicts {nombre, puntos}."""
    res = (db().table("jugadores")
               .select("nombre, puntos")
               .eq("categoria", categoria)
               .eq("deporte",   deporte)
               .eq("curso",     curso)
               .eq("equipo",    equipo)
               .execute())
    return res.data


def agregar_jugador(categoria: str, deporte: str, curso: str,
                    equipo: str, nombre: str) -> str | None:
    try:
        db().table("jugadores").insert({
            "categoria": categoria,
            "deporte":   deporte,
            "curso":     curso,
            "equipo":    equipo,
            "nombre":    nombre,
            "puntos":    0,
        }).execute()
        return None
    except Exception as e:
        msg = str(e)
        if "unique" in msg.lower() or "duplicate" in msg.lower():
            return "Ese jugador ya existe."
        return f"Error: {msg}"

# ── PARTIDOS INTERCURSOS ───────────────────────────────────────────────────────

def obtener_partidos(categoria: str, deporte: str) -> list:
    """Retorna lista de [fecha, enf, estado, g1, g2]."""
    res = (db().table("partidos")
               .select("id, fecha, enf, estado, g1, g2")
               .eq("categoria", categoria)
               .eq("deporte",   deporte)
               .order("fecha")
               .execute())
    return [[r["id"], r["fecha"], r["enf"], r["estado"], r["g1"], r["g2"]]
            for r in res.data]


def actualizar_partido(partido_id: int, estado: str, g1: int, g2: int):
    db().table("partidos").update({
        "estado": estado,
        "g1":     g1,
        "g2":     g2,
    }).eq("id", partido_id).execute()


def insertar_partido(categoria: str, deporte: str,
                     fecha: str, enf: str, estado: str = "Pendiente",
                     g1: int = 0, g2: int = 0):
    db().table("partidos").insert({
        "categoria": categoria,
        "deporte":   deporte,
        "fecha":     fecha,
        "enf":       enf,
        "estado":    estado,
        "g1":        g1,
        "g2":        g2,
    }).execute()

# ── LOGROS ─────────────────────────────────────────────────────────────────────

def obtener_logros() -> list:
    """Retorna lista de [anio, descripcion]."""
    res = db().table("logros").select("anio, descripcion").order("anio", desc=True).execute()
    return [[r["anio"], r["descripcion"]] for r in res.data]


def agregar_logro(anio: str, descripcion: str):
    db().table("logros").insert({"anio": anio, "descripcion": descripcion}).execute()

# ── PARTIDOS INTERCOLEGIADOS ───────────────────────────────────────────────────

def obtener_partidos_inter(deporte: str) -> list:
    res = (db().table("partidos_inter")
               .select("fecha, enf, estado")
               .eq("deporte", deporte)
               .order("fecha")
               .execute())
    return [[r["fecha"], r["enf"], r["estado"]] for r in res.data]


def agregar_partido_inter(deporte: str, fecha: str, enf: str, estado: str):
    db().table("partidos_inter").insert({
        "deporte": deporte,
        "fecha":   fecha,
        "enf":     enf,
        "estado":  estado,
    }).execute()

# ── SORTEOS ────────────────────────────────────────────────────────────────────

def obtener_sorteo(clave: str) -> dict | None:
    res = db().table("sorteos").select("*").eq("clave", clave).execute()
    if res.data:
        r = res.data[0]
        return {
            "fecha":    r["fecha"],
            "n_equipos": r["n_equipos"],
            "equipos":  json.loads(r["equipos"]) if r["equipos"] else [],
        }
    return None


def guardar_sorteo(clave: str, fecha: str, n_equipos: int, equipos: list):
    datos = {
        "clave":     clave,
        "fecha":     fecha,
        "n_equipos": n_equipos,
        "equipos":   json.dumps(equipos, ensure_ascii=False),
    }
    # Upsert: inserta o actualiza si ya existe
    db().table("sorteos").upsert(datos, on_conflict="clave").execute()

# ── LÓGICA DE SORTEO ───────────────────────────────────────────────────────────

def _generar_round_robin(equipos: list) -> list:
    eqs = list(equipos)
    if len(eqs) % 2 != 0:
        eqs.append("BYE")
    n      = len(eqs)
    fijo   = eqs[0]
    rotat  = eqs[1:]
    rondas = []
    for ronda in range(n - 1):
        circulo = [fijo] + rotat
        mitad   = n // 2
        enfs    = []
        for i in range(mitad):
            e1, e2 = circulo[i], circulo[n - 1 - i]
            enfs.append((e1, e2) if ronda % 2 == 0 else (e2, e1))
        rondas.append(enfs)
        rotat = [rotat[-1]] + rotat[:-1]
    return [rondas[i % len(rondas)] for i in range(7)] if rondas else []


def realizar_sorteo(categoria: str, deporte: str):
    """
    Genera fixture Round-Robin de 7 jornadas y lo guarda en Supabase.
    Retorna (fixture, error_msg).
    """
    # Recoger equipos: todos los registrados + predefinidos si faltan
    equipos_con_curso = []
    for cur in CATEGORIAS_LOCAL.get(categoria, []):
        eqs = obtener_equipos(categoria, deporte).get(cur, [])
        if eqs:
            for eq in eqs:
                equipos_con_curso.append((eq, cur))
        else:
            pred = EQUIPOS_POR_CURSO.get(cur)
            if pred:
                err = agregar_equipo(categoria, deporte, cur, pred)
                if not err:
                    equipos_con_curso.append((pred, cur))

    if len(equipos_con_curso) < 2:
        return None, "Se necesitan al menos 2 equipos para el sorteo."

    random.shuffle(equipos_con_curso)
    fixture = _generar_round_robin(equipos_con_curso)

    hoy             = datetime.date.today()
    dias_hasta_sab  = (5 - hoy.weekday()) % 7 or 7
    fecha_base      = hoy + datetime.timedelta(days=dias_hasta_sab)

    # Borrar partidos pendientes anteriores (conservar finalizados)
    db().table("partidos") \
        .delete() \
        .eq("categoria", categoria) \
        .eq("deporte",   deporte) \
        .eq("estado",    "Pendiente") \
        .execute()

    resumen = []
    for i, fecha_enfs in enumerate(fixture):
        fecha_partido = fecha_base + datetime.timedelta(weeks=i)
        fecha_str     = fecha_partido.strftime("%Y-%m-%d 15:00")
        partidos_j    = []
        descanso      = None

        for e1, e2 in fecha_enfs:
            if "BYE" in (e1, e2):
                descanso = e1 if e2 == "BYE" else e2
                continue
            c1  = next((c for eq, c in equipos_con_curso if eq == e1), "?")
            c2  = next((c for eq, c in equipos_con_curso if eq == e2), "?")
            enf = f"{e1} ({c1}) vs {e2} ({c2})"
            insertar_partido(categoria, deporte, fecha_str, enf)
            partidos_j.append((e1, e2))

        resumen.append({
            "jornada":  i + 1,
            "fecha":    fecha_partido.strftime("%Y-%m-%d"),
            "partidos": partidos_j,
            "descanso": descanso,
        })

    # Guardar registro del sorteo
    clave = f"{categoria}_{deporte}"
    guardar_sorteo(
        clave     = clave,
        fecha     = datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        n_equipos = len(equipos_con_curso),
        equipos   = [f"{eq} ({cur})" for eq, cur in equipos_con_curso],
    )

    return resumen, None

# ── TABLA DE POSICIONES ────────────────────────────────────────────────────────

def _limpiar_nombre(texto: str):
    """Extrae (nombre, curso) de 'Nombre (curso)' o formato tupla Python."""
    texto = str(texto).strip()
    if len(texto) > 4 and texto[0] in "([" and texto[-1] in ")]":
        inner  = texto[1:-1]
        partes = inner.split(",", 1)
        if len(partes) == 2:
            n = partes[0].strip().strip("'\"").strip()
            c = partes[1].strip().strip("'\"").strip()
            if n:
                return n, c
    ultimo = texto.rfind("(")
    if ultimo != -1 and texto.endswith(")"):
        return texto[:ultimo].strip(), texto[ultimo+1:-1].strip()
    return texto, "?"


def calcular_tabla(categoria: str, deporte: str) -> list:
    tabla    = {}
    partidos = obtener_partidos(categoria, deporte)

    for p in partidos:
        _, fecha, enf, estado, g1, g2 = p
        if estado != "Finalizado":
            continue
        idx = enf.find(" vs ")
        if idx == -1:
            continue
        n1, c1 = _limpiar_nombre(enf[:idx])
        n2, c2 = _limpiar_nombre(enf[idx+4:])

        for n, c in [(n1, c1), (n2, c2)]:
            k = f"{n}|{c}"
            if k not in tabla:
                tabla[k] = dict(Equipo=n, Curso=c,
                                PJ=0, PG=0, PE=0, PP=0,
                                GF=0, GC=0, Pts=0)

        k1, k2 = f"{n1}|{c1}", f"{n2}|{c2}"
        for k in (k1, k2): tabla[k]["PJ"] += 1
        tabla[k1]["GF"] += g1; tabla[k1]["GC"] += g2
        tabla[k2]["GF"] += g2; tabla[k2]["GC"] += g1
        if   g1 > g2: tabla[k1]["PG"]+=1; tabla[k1]["Pts"]+=3; tabla[k2]["PP"]+=1
        elif g2 > g1: tabla[k2]["PG"]+=1; tabla[k2]["Pts"]+=3; tabla[k1]["PP"]+=1
        else:
            tabla[k1]["PE"]+=1; tabla[k1]["Pts"]+=1
            tabla[k2]["PE"]+=1; tabla[k2]["Pts"]+=1

    # Agregar equipos sin partidos
    for cur, eqs in obtener_equipos(categoria, deporte).items():
        for eq in eqs:
            k = f"{eq}|{cur}"
            if k not in tabla:
                tabla[k] = dict(Equipo=eq, Curso=cur,
                                PJ=0, PG=0, PE=0, PP=0,
                                GF=0, GC=0, Pts=0)

    rows = sorted(tabla.values(),
                  key=lambda x: (-x["Pts"], -(x["GF"]-x["GC"]), -x["GF"]))
    for i, r in enumerate(rows):
        r["#"]  = i + 1
        r["DG"] = r["GF"] - r["GC"]
    return rows
