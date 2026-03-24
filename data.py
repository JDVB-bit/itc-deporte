import json
import os
import random
import datetime

ARCHIVO_DATOS = "datos_app.json"

# ── Generación de cursos ──────────────────────────────────────────────────────

def generar_cursos(grado, cantidad):
    return [f"{grado}{i:02d}" for i in range(1, cantidad + 1)]

cursos_sexto_septimo = generar_cursos(6, 9) + generar_cursos(7, 8)
cursos_octavo_noveno = generar_cursos(8, 8) + generar_cursos(9, 6)
cursos_decimo_once   = generar_cursos(10, 3) + generar_cursos(11, 4)

CATEGORIAS_LOCAL = {
    "PRIMERA": cursos_sexto_septimo,
    "SEGUNDA": cursos_octavo_noveno,
    "TERCERA": cursos_decimo_once,
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

DEPORTES = ["Balonmano", "Microfutbol", "Baloncesto", "Voleyball"]
ICONOS_DEP = {"Balonmano": "🤾", "Microfutbol": "⚽", "Baloncesto": "🏀", "Voleyball": "🏐"}

# ── Datos por defecto ─────────────────────────────────────────────────────────

def _default_data():
    equipos_local = {
        "PRIMERA": {
            "Balonmano":   {"601": ["Halcones FC"], "602": ["Pumas FC"], "603": ["Condores FC"]},
            "Microfutbol": {"701": ["Fenix FC"],    "702": ["Lobos FC"], "703": ["Raptors FC"]},
            "Baloncesto":  {"704": ["Tigres FC"],   "705": ["Spartans FC"]},
            "Voleyball":   {"706": ["Truenos FC"],  "707": ["Centellas FC"]},
        },
        "SEGUNDA": {
            "Balonmano":   {"801": ["Tiburones FC"], "802": ["Panteras FC"]},
            "Microfutbol": {"901": ["Lobos Negros FC"], "902": ["Flamas FC"]},
            "Baloncesto":  {"803": ["Escorpiones FC"], "804": ["Huracanes FC"]},
            "Voleyball":   {"903": ["Vikingos FC"], "904": ["Corsarios FC"]},
        },
        "TERCERA": {
            "Balonmano":   {"1001": ["Elite FC"], "1002": ["Fenix D.C FC"]},
            "Microfutbol": {"1101": ["Lobos Dorados FC"], "1102": ["Raptors Sur FC"]},
            "Baloncesto":  {"1003": ["Eagles FC"], "1103": ["Spartans Pro FC"]},
            "Voleyball":   {"1104": ["Titanes Pro FC"]},
        },
    }

    jugadores_local = {
        cat: {
            dep: {cur: {eq: [] for eq in eqs}
                  for cur, eqs in deps.items()}
            for dep, deps in deportes.items()
        }
        for cat, deportes in equipos_local.items()
    }

    partidos_local = {
        "PRIMERA": {
            "Balonmano":   [["2025-10-15 15:00", "Halcones FC (601) vs Pumas FC (602)", "Pendiente", 0, 0]],
            "Microfutbol": [["2025-10-18 16:00", "Fenix FC (701) vs Lobos FC (702)", "Pendiente", 0, 0]],
            "Baloncesto":  [["2025-10-20 14:00", "Tigres FC (704) vs Spartans FC (705)", "Finalizado", 8, 6]],
            "Voleyball":   [["2025-10-25 13:00", "Truenos FC (706) vs Centellas FC (707)", "Pendiente", 0, 0]],
        },
        "SEGUNDA": {
            "Balonmano":   [["2025-10-11 15:30", "Tiburones FC (801) vs Panteras FC (802)", "Finalizado", 4, 3]],
            "Microfutbol": [["2025-10-19 17:00", "Lobos Negros FC (901) vs Flamas FC (902)", "Pendiente", 0, 0]],
            "Baloncesto":  [["2025-10-17 14:00", "Escorpiones FC (803) vs Huracanes FC (804)", "Pendiente", 0, 0]],
            "Voleyball":   [["2025-10-26 10:00", "Vikingos FC (903) vs Corsarios FC (904)", "Pendiente", 0, 0]],
        },
        "TERCERA": {
            "Balonmano":   [["2025-11-02 15:00", "Elite FC (1001) vs Fenix D.C FC (1002)", "Pendiente", 0, 0]],
            "Microfutbol": [["2025-11-03 16:00", "Lobos Dorados FC (1101) vs Raptors Sur FC (1102)", "Pendiente", 0, 0]],
            "Baloncesto":  [["2025-11-04 14:30", "Eagles FC (1003) vs Spartans Pro FC (1103)", "Pendiente", 0, 0]],
            "Voleyball":   [["2025-11-05 09:30", "Titanes Pro FC (1104) vs Lobos Dorados FC (1101)", "Pendiente", 0, 0]],
        },
    }

    return {
        "usuarios":      {"admin": "1234"},
        "usuarios_tipo": {"admin": "profesor"},
        "jugadores":     {d: [] for d in DEPORTES},
        "logros": [
            ["2023", "Balonmano - Campeón Nacional Sub-17"],
            ["2022", "Microfutbol - Subcampeón Intercursos"],
            ["2024", "Baloncesto - Primer puesto Torneo Distrital"],
        ],
        "partidos": {
            "Balonmano":   [["2025-10-15", "ITC vs Colegio San Jose",  "Pendiente"]],
            "Microfutbol": [["2025-10-20", "ITC vs Colegio El Rosario","Pendiente"]],
            "Baloncesto":  [["2025-10-25", "ITC vs Liceo Frances",     "Pendiente"]],
            "Voleyball":   [["2025-11-05", "ITC vs Colegio Mayor",     "Pendiente"]],
        },
        "equipos_local":   equipos_local,
        "jugadores_local": jugadores_local,
        "partidos_local":  partidos_local,
        "sorteo_realizado": {},
    }

# ── Persistencia ──────────────────────────────────────────────────────────────

def cargar_datos():
    if not os.path.exists(ARCHIVO_DATOS):
        return _default_data()
    try:
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return _default_data()

def guardar_datos(datos):
    try:
        with open(ARCHIVO_DATOS, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error al guardar: {e}")

# ── Lógica de sorteo ──────────────────────────────────────────────────────────

def generar_round_robin(equipos):
    eqs = list(equipos)
    if len(eqs) % 2 != 0:
        eqs.append("BYE")
    n = len(eqs)
    fijo = eqs[0]
    rotativos = eqs[1:]
    rondas = []
    for ronda in range(n - 1):
        circulo = [fijo] + rotativos
        mitad = n // 2
        enfrentamientos = []
        for i in range(mitad):
            e1 = circulo[i]
            e2 = circulo[n - 1 - i]
            enfrentamientos.append((e1, e2) if ronda % 2 == 0 else (e2, e1))
        rondas.append(enfrentamientos)
        rotativos = [rotativos[-1]] + rotativos[:-1]
    fechas_7 = [rondas[i % len(rondas)] for i in range(7)] if rondas else []
    return fechas_7

def realizar_sorteo(datos, categoria, deporte):
    """
    Recoge TODOS los equipos registrados en la categoria/deporte.
    Si un curso no tiene equipo registrado, usa el equipo predefinido.
    """
    equipos_con_curso = []
    cursos_cat = CATEGORIAS_LOCAL.get(categoria, [])

    for cur in cursos_cat:
        eqs_cur = datos["equipos_local"].get(categoria, {}).get(deporte, {}).get(cur, [])
        if eqs_cur:
            # Registrar TODOS los equipos del curso (no solo el primero)
            for eq in eqs_cur:
                equipos_con_curso.append((eq, cur))
        else:
            # Usar equipo predefinido si no hay ninguno registrado
            nombre_pred = EQUIPOS_POR_CURSO.get(cur)
            if nombre_pred:
                if categoria not in datos["equipos_local"]:
                    datos["equipos_local"][categoria] = {}
                if deporte not in datos["equipos_local"][categoria]:
                    datos["equipos_local"][categoria][deporte] = {}
                if cur not in datos["equipos_local"][categoria][deporte]:
                    datos["equipos_local"][categoria][deporte][cur] = []
                if categoria not in datos["jugadores_local"]:
                    datos["jugadores_local"][categoria] = {}
                if deporte not in datos["jugadores_local"][categoria]:
                    datos["jugadores_local"][categoria][deporte] = {}
                if cur not in datos["jugadores_local"][categoria][deporte]:
                    datos["jugadores_local"][categoria][deporte][cur] = {}
                eqs_lista = datos["equipos_local"][categoria][deporte][cur]
                if nombre_pred not in eqs_lista:
                    eqs_lista.append(nombre_pred)
                    datos["jugadores_local"][categoria][deporte][cur][nombre_pred] = []
                equipos_con_curso.append((nombre_pred, cur))

    if len(equipos_con_curso) < 2:
        return datos, None, "Se necesitan al menos 2 equipos para el sorteo."

    random.shuffle(equipos_con_curso)
    fixture = generar_round_robin(equipos_con_curso)

    hoy = datetime.date.today()
    dias_hasta_sab = (5 - hoy.weekday()) % 7 or 7
    fecha_base = hoy + datetime.timedelta(days=dias_hasta_sab)

    if categoria not in datos["partidos_local"]:
        datos["partidos_local"][categoria] = {}
    if deporte not in datos["partidos_local"][categoria]:
        datos["partidos_local"][categoria][deporte] = []

    partidos_con_resultado = [
        p for p in datos["partidos_local"][categoria][deporte]
        if p[2] == "Finalizado"
    ]
    nuevos_partidos = []
    resumen_fixture = []

    for i, fecha_enfs in enumerate(fixture):
        fecha_partido = fecha_base + datetime.timedelta(weeks=i)
        fecha_str = fecha_partido.strftime("%Y-%m-%d 15:00")
        partidos_jornada = []
        descanso = None

        for e1, e2 in fecha_enfs:
            if "BYE" in (e1, e2):
                descanso = e1 if e2 == "BYE" else e2
                continue
            c1 = next((c for eq, c in equipos_con_curso if eq == e1), "?")
            c2 = next((c for eq, c in equipos_con_curso if eq == e2), "?")
            enf = f"{e1} ({c1}) vs {e2} ({c2})"
            nuevos_partidos.append([fecha_str, enf, "Pendiente", 0, 0])
            partidos_jornada.append((e1, e2))

        resumen_fixture.append({
            "jornada": i + 1,
            "fecha": fecha_partido.strftime("%Y-%m-%d"),
            "partidos": partidos_jornada,
            "descanso": descanso,
        })

    datos["partidos_local"][categoria][deporte] = partidos_con_resultado + nuevos_partidos
    datos["sorteo_realizado"][f"{categoria}_{deporte}"] = {
        "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "equipos": [f"{eq} ({cur})" for eq, cur in equipos_con_curso],
        "n_equipos": len(equipos_con_curso),
    }
    return datos, resumen_fixture, None

# ── Tabla de posiciones ───────────────────────────────────────────────────────

def _limpiar_nombre(texto):
    """Extrae (nombre, curso) — soporta formato normal y formato tupla Python."""
    texto = str(texto).strip()
    # Formato tuple/list de Python: ('x', 'y') o ["x","y"]
    if len(texto) > 4 and texto[0] in "([" and texto[-1] in ")]":
        inner = texto[1:-1]
        partes = inner.split(",", 1)
        if len(partes) == 2:
            n = partes[0].strip().strip("\'\"").strip()
            c = partes[1].strip().strip("\'\"").strip()
            if n:
                return n, c
    # Formato normal: "Nombre Equipo (curso)"
    ultimo_par = texto.rfind("(")
    if ultimo_par != -1 and texto.endswith(")"):
        return texto[:ultimo_par].strip(), texto[ultimo_par+1:-1].strip()
    return texto, "?"

def _parsear_enf(enf):
    """Parsea 'Equipo A (c1) vs Equipo B (c2)' de forma robusta."""
    if not isinstance(enf, str):
        return None
    # Limpiar si toda la cadena es una tupla Python
    enf = enf.strip()
    idx = enf.find(" vs ")
    if idx == -1:
        return None
    n1, c1 = _limpiar_nombre(enf[:idx])
    n2, c2 = _limpiar_nombre(enf[idx+4:])
    if not n1 or not n2:
        return None
    return n1, c1, n2, c2

def calcular_tabla(datos, categoria, deporte):
    tabla = {}
    partidos = datos["partidos_local"].get(categoria, {}).get(deporte, [])

    for p in partidos:
        if len(p) < 5 or p[2] != "Finalizado":
            continue
        _, enf, _, g1, g2 = p
        parsed = _parsear_enf(enf)
        if not parsed:
            continue
        n1, c1, n2, c2 = parsed

        for n, c in [(n1, c1), (n2, c2)]:
            k = f"{n}|{c}"
            if k not in tabla:
                tabla[k] = dict(Equipo=n, Curso=c, PJ=0, PG=0, PE=0, PP=0, GF=0, GC=0, Pts=0)

        k1, k2 = f"{n1}|{c1}", f"{n2}|{c2}"
        for k in (k1, k2): tabla[k]["PJ"] += 1
        tabla[k1]["GF"] += g1; tabla[k1]["GC"] += g2
        tabla[k2]["GF"] += g2; tabla[k2]["GC"] += g1
        if g1 > g2:
            tabla[k1]["PG"] += 1; tabla[k1]["Pts"] += 3; tabla[k2]["PP"] += 1
        elif g2 > g1:
            tabla[k2]["PG"] += 1; tabla[k2]["Pts"] += 3; tabla[k1]["PP"] += 1
        else:
            tabla[k1]["PE"] += 1; tabla[k1]["Pts"] += 1
            tabla[k2]["PE"] += 1; tabla[k2]["Pts"] += 1

    # Agregar equipos sin partidos
    for cur, eqs in datos["equipos_local"].get(categoria, {}).get(deporte, {}).items():
        for eq in eqs:
            k = f"{eq}|{cur}"
            if k not in tabla:
                tabla[k] = dict(Equipo=eq, Curso=cur, PJ=0, PG=0, PE=0, PP=0, GF=0, GC=0, Pts=0)

    rows = sorted(tabla.values(), key=lambda x: (-x["Pts"], -(x["GF"] - x["GC"]), -x["GF"]))
    for i, r in enumerate(rows):
        r["#"] = i + 1
        r["DG"] = r["GF"] - r["GC"]
    return rows
