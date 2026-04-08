import json, random, datetime
import streamlit as st
from supabase import create_client, Client

def generar_cursos(grado, cantidad):
    return [f"{grado}{i:02d}" for i in range(1, cantidad + 1)]

CATEGORIAS_LOCAL = {
    "PRIMERA": generar_cursos(6, 9) + generar_cursos(7, 8),
    "SEGUNDA": generar_cursos(8, 8) + generar_cursos(9, 6),
    "TERCERA": generar_cursos(10, 3) + generar_cursos(11, 4),
}

EQUIPOS_POR_CURSO = {
    "601":"Halcones FC","602":"Pumas FC","603":"Condores FC","604":"Jaguares FC",
    "605":"Leones FC","606":"Dragones FC","607":"Guerreros FC","608":"Titanes FC",
    "609":"Aguilas FC","701":"Fenix FC","702":"Lobos FC","703":"Raptors FC",
    "704":"Tigres FC","705":"Spartans FC","706":"Truenos FC","707":"Centellas FC",
    "708":"Gladiadores FC","801":"Tiburones FC","802":"Panteras FC","803":"Escorpiones FC",
    "804":"Huracanes FC","805":"Toros FC","806":"Buhos FC","807":"Zorros FC","808":"Cobras FC",
    "901":"Lobos Negros FC","902":"Flamas FC","903":"Vikingos FC","904":"Corsarios FC",
    "905":"Rayos FC","906":"Cometas FC","1001":"Elite FC","1002":"Fenix D.C FC",
    "1003":"Eagles FC","1101":"Lobos Dorados FC","1102":"Raptors Sur FC",
    "1103":"Spartans Pro FC","1104":"Titanes Pro FC",
}

DEPORTES   = ["Balonmano", "Microfutbol", "Baloncesto", "Voleyball"]
ICONOS_DEP = {"Balonmano":"🤾","Microfutbol":"⚽","Baloncesto":"🏀","Voleyball":"🏐"}
USUARIOS      = {"admin": "1234"}
USUARIOS_TIPO = {"admin": "profesor"}

@st.cache_resource
def get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def db() -> Client:
    return get_supabase()

# ── EQUIPOS ────────────────────────────────────────────────────────────────────

def obtener_equipos(categoria, deporte):
    res = db().table("equipos").select("curso,nombre").eq("categoria",categoria).eq("deporte",deporte).execute()
    result = {}
    for r in res.data:
        result.setdefault(r["curso"], []).append(r["nombre"])
    return result

def agregar_equipo(categoria, deporte, curso, nombre):
    try:
        db().table("equipos").insert({"categoria":categoria,"deporte":deporte,"curso":curso,"nombre":nombre}).execute()
        return None
    except Exception as e:
        msg = str(e)
        return "Ese equipo ya existe." if "unique" in msg.lower() or "duplicate" in msg.lower() else f"Error: {msg}"

def eliminar_equipo(categoria, deporte, curso, nombre):
    db().table("equipos").delete().eq("categoria",categoria).eq("deporte",deporte).eq("curso",curso).eq("nombre",nombre).execute()
    # Eliminar también sus jugadores
    db().table("jugadores").delete().eq("categoria",categoria).eq("deporte",deporte).eq("curso",curso).eq("equipo",nombre).execute()

# ── JUGADORES ──────────────────────────────────────────────────────────────────

def obtener_jugadores(categoria, deporte, curso, equipo):
    res = db().table("jugadores").select("id,nombre,puntos").eq("categoria",categoria).eq("deporte",deporte).eq("curso",curso).eq("equipo",equipo).execute()
    return res.data

def agregar_jugador(categoria, deporte, curso, equipo, nombre):
    try:
        db().table("jugadores").insert({"categoria":categoria,"deporte":deporte,"curso":curso,"equipo":equipo,"nombre":nombre,"puntos":0}).execute()
        return None
    except Exception as e:
        msg = str(e)
        return "Ese jugador ya existe." if "unique" in msg.lower() or "duplicate" in msg.lower() else f"Error: {msg}"

def eliminar_jugador(jugador_id):
    db().table("jugadores").delete().eq("id", jugador_id).execute()

# ── PARTIDOS INTERCURSOS ───────────────────────────────────────────────────────

def obtener_partidos(categoria, deporte):
    res = db().table("partidos").select("id,fecha,enf,estado,g1,g2").eq("categoria",categoria).eq("deporte",deporte).order("fecha").execute()
    return [[r["id"],r["fecha"],r["enf"],r["estado"],r["g1"],r["g2"]] for r in res.data]

def actualizar_partido(partido_id, estado, g1, g2):
    db().table("partidos").update({"estado":estado,"g1":g1,"g2":g2}).eq("id",partido_id).execute()

def insertar_partido(categoria, deporte, fecha, enf, estado="Pendiente", g1=0, g2=0):
    db().table("partidos").insert({"categoria":categoria,"deporte":deporte,"fecha":fecha,"enf":enf,"estado":estado,"g1":g1,"g2":g2}).execute()

# ── LOGROS ─────────────────────────────────────────────────────────────────────

def obtener_logros():
    res = db().table("logros").select("id,anio,descripcion").order("anio", desc=True).execute()
    return [[r["id"],r["anio"],r["descripcion"]] for r in res.data]

def agregar_logro(anio, descripcion):
    db().table("logros").insert({"anio":anio,"descripcion":descripcion}).execute()

def eliminar_logro(logro_id):
    db().table("logros").delete().eq("id", logro_id).execute()

# ── PARTIDOS INTERCOLEGIADOS ───────────────────────────────────────────────────

def obtener_partidos_inter(deporte):
    res = db().table("partidos_inter").select("id,fecha,enf,estado").eq("deporte",deporte).order("fecha").execute()
    return [[r["id"],r["fecha"],r["enf"],r["estado"]] for r in res.data]

def agregar_partido_inter(deporte, fecha, enf, estado):
    db().table("partidos_inter").insert({"deporte":deporte,"fecha":fecha,"enf":enf,"estado":estado}).execute()

def eliminar_partido_inter(partido_id):
    db().table("partidos_inter").delete().eq("id", partido_id).execute()

# ── SORTEOS ────────────────────────────────────────────────────────────────────

def obtener_sorteo(clave):
    res = db().table("sorteos").select("*").eq("clave",clave).execute()
    if res.data:
        r = res.data[0]
        return {"fecha":r["fecha"],"n_equipos":r["n_equipos"],"equipos":json.loads(r["equipos"]) if r["equipos"] else []}
    return None

def guardar_sorteo(clave, fecha, n_equipos, equipos):
    db().table("sorteos").upsert({"clave":clave,"fecha":fecha,"n_equipos":n_equipos,"equipos":json.dumps(equipos,ensure_ascii=False)},on_conflict="clave").execute()

# ── SORTEO ROUND ROBIN ────────────────────────────────────────────────────────

def _generar_round_robin(equipos):
    eqs = list(equipos)
    if len(eqs) % 2 != 0:
        eqs.append("BYE")
    n, fijo, rotat, rondas = len(eqs), eqs[0], eqs[1:], []
    for ronda in range(n - 1):
        circulo = [fijo] + rotat
        enfs = []
        for i in range(n // 2):
            e1, e2 = circulo[i], circulo[n-1-i]
            enfs.append((e1,e2) if ronda%2==0 else (e2,e1))
        rondas.append(enfs)
        rotat = [rotat[-1]] + rotat[:-1]
    return [rondas[i % len(rondas)] for i in range(7)] if rondas else []

def realizar_sorteo(categoria, deporte):
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

    hoy = datetime.date.today()
    dias = (5 - hoy.weekday()) % 7 or 7
    fecha_base = hoy + datetime.timedelta(days=dias)

    db().table("partidos").delete().eq("categoria",categoria).eq("deporte",deporte).eq("estado","Pendiente").execute()

    for i, fecha_enfs in enumerate(fixture):
        fecha_str = (fecha_base + datetime.timedelta(weeks=i)).strftime("%Y-%m-%d 15:00")
        for e1, e2 in fecha_enfs:
            if "BYE" in (e1, e2):
                continue
            c1 = next((c for eq,c in equipos_con_curso if eq==e1), "?")
            c2 = next((c for eq,c in equipos_con_curso if eq==e2), "?")
            insertar_partido(categoria, deporte, fecha_str, f"{e1} ({c1}) vs {e2} ({c2})")

    guardar_sorteo(f"{categoria}_{deporte}", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                   len(equipos_con_curso), [f"{eq} ({cur})" for eq,cur in equipos_con_curso])
    return True, None

# ── TABLA DE POSICIONES ────────────────────────────────────────────────────────

def _parsear_lado(texto):
    texto = str(texto).strip()
    if len(texto) > 4 and texto[0] in "([" and texto[-1] in ")]":
        partes = texto[1:-1].split(",", 1)
        if len(partes) == 2:
            n = partes[0].strip().strip("'\"").strip()
            c = partes[1].strip().strip("'\"").strip()
            if n: return n, c
    ultimo = texto.rfind("(")
    if ultimo != -1 and texto.endswith(")"):
        return texto[:ultimo].strip(), texto[ultimo+1:-1].strip()
    return texto, "?"

def calcular_tabla(categoria, deporte):
    tabla = {}
    for p in obtener_partidos(categoria, deporte):
        _, fecha, enf, estado, g1, g2 = p
        if estado != "Finalizado": continue
        idx = enf.find(" vs ")
        if idx == -1: continue
        n1, c1 = _parsear_lado(enf[:idx])
        n2, c2 = _parsear_lado(enf[idx+4:])
        for n, c in [(n1,c1),(n2,c2)]:
            k = f"{n}|{c}"
            if k not in tabla:
                tabla[k] = dict(Equipo=n,Curso=c,PJ=0,PG=0,PE=0,PP=0,GF=0,GC=0,Pts=0)
        k1, k2 = f"{n1}|{c1}", f"{n2}|{c2}"
        for k in (k1,k2): tabla[k]["PJ"] += 1
        tabla[k1]["GF"]+=g1; tabla[k1]["GC"]+=g2
        tabla[k2]["GF"]+=g2; tabla[k2]["GC"]+=g1
        if   g1>g2: tabla[k1]["PG"]+=1; tabla[k1]["Pts"]+=3; tabla[k2]["PP"]+=1
        elif g2>g1: tabla[k2]["PG"]+=1; tabla[k2]["Pts"]+=3; tabla[k1]["PP"]+=1
        else:
            tabla[k1]["PE"]+=1; tabla[k1]["Pts"]+=1
            tabla[k2]["PE"]+=1; tabla[k2]["Pts"]+=1
    for cur, eqs in obtener_equipos(categoria, deporte).items():
        for eq in eqs:
            k = f"{eq}|{cur}"
            if k not in tabla:
                tabla[k] = dict(Equipo=eq,Curso=cur,PJ=0,PG=0,PE=0,PP=0,GF=0,GC=0,Pts=0)
    rows = sorted(tabla.values(), key=lambda x: (-x["Pts"],-(x["GF"]-x["GC"]),-x["GF"]))
    for i,r in enumerate(rows):
        r["#"] = i+1; r["DG"] = r["GF"]-r["GC"]
    return rows
