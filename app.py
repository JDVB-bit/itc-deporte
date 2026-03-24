import streamlit as st
from data import cargar_datos, guardar_datos, ICONOS_DEP, DEPORTES, CATEGORIAS_LOCAL, calcular_tabla, realizar_sorteo

st.set_page_config(
    page_title="ITC Deportes",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state ──────────────────────────────────────────────────────────────
if "datos" not in st.session_state:
    st.session_state.datos = cargar_datos()
if "rol" not in st.session_state:
    st.session_state.rol = "invitado"
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "tema" not in st.session_state:
    st.session_state.tema = "oscuro"

datos = st.session_state.datos

# ── Paletas de tema ────────────────────────────────────────────────────────────
TEMAS = {
    "oscuro": {
        "acento":      "#D4A017",
        "acento_hi":   "#FFD040",
        "bg":          "#0A0A0A",
        "bg_card":     "#141414",
        "bg_alt":      "#101010",
        "bg_section":  "#1A1200",
        "text":        "#F5F0E8",
        "text2":       "#9A9080",
        "text3":       "#5A5550",
        "sidebar_bg":  "#050505",
        "btn_fg":      "#050505",
        "hero_grad":   "linear-gradient(135deg,#0A0A0A,#1A1200)",
        "icono_tema":  "🟢",
        "label_tema":  "Tema Verde",
    },
    "verde": {
        "acento":      "#4CAF28",
        "acento_hi":   "#7FD44A",
        "bg":          "#0D1F0F",
        "bg_card":     "#122516",
        "bg_alt":      "#0F1E12",
        "bg_section":  "#0A1A08",
        "text":        "#E8F5E0",
        "text2":       "#8AB880",
        "text3":       "#507848",
        "sidebar_bg":  "#071208",
        "btn_fg":      "#071208",
        "hero_grad":   "linear-gradient(135deg,#071208,#0D2010)",
        "icono_tema":  "🌙",
        "label_tema":  "Tema Oscuro",
    },
}

def T():
    return TEMAS[st.session_state.tema]

# ── CSS dinámico ───────────────────────────────────────────────────────────────
def inyectar_css():
    t = T()
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow:wght@400;600;700&display=swap');
html, body, [class*="css"] {{
    font-family: 'Barlow', sans-serif;
    background-color: {t['bg']} !important;
    color: {t['text']} !important;
}}
[data-testid="stAppViewContainer"] {{ background-color: {t['bg']} !important; }}
[data-testid="stSidebar"] {{ background-color: {t['sidebar_bg']} !important; border-right: 1px solid {t['bg_card']}; }}
[data-testid="stSidebar"] * {{ color: {t['text2']} !important; }}
[data-testid="stSidebar"] h2 {{ color: {t['acento']} !important; font-size:1.3rem; }}
.stTabs [data-baseweb="tab-list"] {{ background: {t['bg_card']}; border-radius: 8px; padding: 4px; gap: 4px; }}
.stTabs [data-baseweb="tab"] {{ background: transparent; color: {t['text2']} !important; border-radius: 6px; padding: 8px 16px; font-weight: 600; }}
.stTabs [aria-selected="true"] {{ background: {t['acento']} !important; color: {t['btn_fg']} !important; }}
.stExpander {{ background: {t['bg_card']} !important; border: 1px solid {t['bg_alt']} !important; border-radius: 8px !important; }}
.stExpander summary {{ color: {t['acento']} !important; font-weight: 700 !important; }}
.stSelectbox > div > div, .stTextInput > div > div > input, .stNumberInput > div > div > input {{
    background: {t['bg_alt']} !important;
    color: {t['text']} !important;
    border-color: {t['bg_card']} !important;
    border-radius: 6px !important;
}}
.stButton > button {{
    background: {t['acento']} !important;
    color: {t['btn_fg']} !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 8px 20px !important;
}}
.stButton > button:hover {{ background: {t['acento_hi']} !important; }}
.stRadio > div > label > div {{ color: {t['text2']} !important; }}
.stCheckbox > label > div {{ color: {t['text']} !important; }}
div[data-testid="stMarkdownContainer"] p {{ color: {t['text']} !important; }}
.stInfo {{ background: {t['bg_card']} !important; border-left: 3px solid {t['acento']} !important; color: {t['text2']} !important; }}
</style>
""", unsafe_allow_html=True)

inyectar_css()
t = T()

# ── Helpers ────────────────────────────────────────────────────────────────────
def badge_html(estado):
    if estado == "Finalizado":
        return '<span style="background:#1A6020;color:#90FF90;padding:3px 12px;border-radius:20px;font-size:0.75rem;font-weight:700;white-space:nowrap;">✓ Finalizado</span>'
    if estado == "Pendiente":
        return f'<span style="background:{t["bg_section"]};color:{t["acento"]};padding:3px 12px;border-radius:20px;font-size:0.75rem;font-weight:700;border:1px solid {t["acento"]};white-space:nowrap;">⏳ Pendiente</span>'
    return '<span style="background:#3A0A0A;color:#FFB0B0;padding:3px 12px;border-radius:20px;font-size:0.75rem;font-weight:700;white-space:nowrap;">✗ Aplazado</span>'

def partido_card(enf, hora, estado, g1=0, g2=0):
    marcador = f'<div style="background:{t["acento"]};color:{t["btn_fg"]};padding:6px 16px;border-radius:6px;font-weight:700;font-size:1.1rem;font-family:monospace;">{g1} — {g2}</div>' if estado == "Finalizado" else ""
    return f"""
<div style="background:{t['bg_card']};border-left:4px solid {t['acento']};border-radius:0 8px 8px 0;
     padding:14px 18px;margin-bottom:8px;display:flex;align-items:center;justify-content:space-between;
     box-shadow:0 1px 3px rgba(0,0,0,0.4);">
  <div>
    <div style="font-weight:700;color:{t['text']};font-size:1rem;margin-bottom:3px;">{enf}</div>
    <div style="color:{t['text3']};font-size:0.8rem;">🕐 {hora} hrs</div>
  </div>
  <div style="display:flex;align-items:center;gap:10px;">{marcador}{badge_html(estado)}</div>
</div>"""

def seccion_titulo(txt):
    return f'<div style="font-size:0.7rem;font-weight:700;letter-spacing:2px;color:{t["text3"]};text-transform:uppercase;margin:16px 0 8px;padding-left:4px;">{txt}</div>'

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"## ⚽ ITC Deportes")
    st.markdown("---")

    # Toggle de tema
    tema_btn = T()["label_tema"]
    tema_ico = T()["icono_tema"]
    if st.button(f"{tema_ico} {tema_btn}", key="btn_tema"):
        st.session_state.tema = "verde" if st.session_state.tema == "oscuro" else "oscuro"
        st.rerun()

    st.markdown("---")

    if st.session_state.rol == "invitado":
        st.markdown("**👤 Modo Invitado**")
        with st.expander("🔐 Iniciar sesión"):
            user = st.text_input("Usuario", key="sb_user")
            pwd  = st.text_input("Contraseña", type="password", key="sb_pwd")
            if st.button("Entrar", key="btn_login"):
                if (user in datos["usuarios"]
                        and datos["usuarios"][user] == pwd
                        and datos["usuarios_tipo"].get(user) == "profesor"):
                    st.session_state.rol = "profesor"
                    st.session_state.usuario = user
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas.")
    else:
        st.markdown(f"**★ {st.session_state.usuario.upper()}**")
        st.caption("Profesor")
        if st.button("Cerrar sesión", key="btn_logout"):
            st.session_state.rol = "invitado"
            st.session_state.usuario = None
            st.rerun()

    st.markdown("---")
    torneo = st.radio("Torneo", ["🏆 Intercolegiados", "🎯 Intercursos"], key="torneo_sel")

    if torneo == "🎯 Intercursos":
        st.markdown("**Categoría**")
        categoria = st.radio("cat", ["PRIMERA", "SEGUNDA", "TERCERA"],
                             label_visibility="collapsed", key="cat_sel")
        st.caption({"PRIMERA":"Grados 6° y 7°","SEGUNDA":"Grados 8° y 9°","TERCERA":"Grados 10° y 11°"}.get(categoria,""))
        st.markdown("**Deporte**")
        dep_opts = list(datos["equipos_local"].get(categoria, {}).keys()) or list(DEPORTES)
        dep_raw  = st.radio("dep", [f"{ICONOS_DEP.get(d,'🏅')} {d}" for d in dep_opts],
                             label_visibility="collapsed", key="dep_sel")
        deporte = dep_raw.split(" ", 1)[1] if " " in dep_raw else dep_raw
    else:
        categoria = None
        deporte   = None

# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:{t['hero_grad']};border-left:6px solid {t['acento']};
     padding:28px 36px;margin-bottom:28px;border-radius:0 12px 12px 0;">
  <div style="font-family:'Bebas Neue',Impact,sans-serif;font-size:3.2rem;
              color:{t['acento']};letter-spacing:5px;line-height:1;">ITC DEPORTES</div>
  <div style="color:{t['text2']};margin-top:6px;font-size:0.95rem;letter-spacing:1px;">
    Sistema de gestión deportiva institucional · 2026
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  INTERCOLEGIADOS
# ═══════════════════════════════════════════════════════════════════════════════
if torneo == "🏆 Intercolegiados":
    st.markdown(f"<h2 style='color:{t['acento']};'>🏆 Intercolegiados ITC</h2>", unsafe_allow_html=True)
    tabs = st.tabs([f"{ICONOS_DEP[d]} {d}" for d in DEPORTES])

    for i, dep in enumerate(DEPORTES):
        with tabs[i]:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(seccion_titulo("Logros destacados"), unsafe_allow_html=True)
                logros_dep = [l for l in datos["logros"] if dep in l[1]]
                if logros_dep:
                    for anio, desc in logros_dep:
                        st.markdown(f"""
                        <div style="display:flex;align-items:center;gap:12px;background:{t['bg_card']};
                             border-left:3px solid {t['acento']};padding:12px 16px;
                             margin-bottom:6px;border-radius:0 8px 8px 0;">
                          <span style="background:{t['acento']};color:{t['btn_fg']};padding:4px 12px;
                                border-radius:20px;font-weight:700;font-size:0.85rem;white-space:nowrap;">{anio}</span>
                          <span style="color:{t['text']};font-size:0.95rem;">{desc}</span>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.info("Sin logros registrados.")

                if st.session_state.rol == "profesor":
                    with st.expander("➕ Añadir logro"):
                        anio_n = st.text_input("Año", key=f"logro_anio_{dep}")
                        desc_n = st.text_input("Descripción", key=f"logro_desc_{dep}")
                        if st.button("Guardar logro", key=f"logro_btn_{dep}"):
                            if anio_n and desc_n:
                                datos["logros"].append([anio_n, f"{dep} - {desc_n}"])
                                guardar_datos(datos)
                                st.success("✅ Logro añadido.")

            with c2:
                st.markdown(seccion_titulo("Partidos programados"), unsafe_allow_html=True)
                partidos_dep = datos["partidos"].get(dep, [])
                if partidos_dep:
                    for p in partidos_dep:
                        fecha, enf, estado = p[0], p[1], p[2]
                        st.markdown(partido_card(enf, fecha, estado), unsafe_allow_html=True)
                else:
                    st.info("Sin partidos programados.")

                if st.session_state.rol == "profesor":
                    with st.expander("➕ Añadir partido"):
                        fecha_p  = st.text_input("Fecha (AAAA-MM-DD)", key=f"p_fecha_{dep}")
                        enf_p    = st.text_input("Enfrentamiento", key=f"p_enf_{dep}")
                        estado_p = st.selectbox("Estado", ["Pendiente","Finalizado","Aplazado"], key=f"p_est_{dep}")
                        if st.button("Guardar partido", key=f"p_btn_{dep}"):
                            if fecha_p and enf_p:
                                datos["partidos"].setdefault(dep, []).append([fecha_p, enf_p, estado_p])
                                guardar_datos(datos)
                                st.success("✅ Partido añadido.")

# ═══════════════════════════════════════════════════════════════════════════════
#  INTERCURSOS
# ═══════════════════════════════════════════════════════════════════════════════
else:
    st.markdown(f"<h2 style='color:{t['acento']};'>🎯 Intercursos — Categoría {categoria}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{t['text3']};margin-top:-12px;'>{'Grados 6° y 7°' if categoria=='PRIMERA' else 'Grados 8° y 9°' if categoria=='SEGUNDA' else 'Grados 10° y 11°'}</p>", unsafe_allow_html=True)

    # ── Panel profesor ─────────────────────────────────────────────────────────
    if st.session_state.rol == "profesor":
        with st.expander("⚙️ Panel de Gestión — Profesor", expanded=False):
            ptabs = st.tabs(["➕ Equipo", "👤 Jugador", "✏️ Partido", "🎲 Sorteo"])

            with ptabs[0]:
                deps_ae = list(datos["equipos_local"].get(categoria, {}).keys())
                dep_ae  = st.selectbox("Deporte", deps_ae, key="ae_dep")
                cur_ae  = st.selectbox("Curso", CATEGORIAS_LOCAL.get(categoria, []), key="ae_cur")
                nom_ae  = st.text_input("Nombre del equipo", key="ae_nom")
                if st.button("Añadir equipo", key="ae_btn"):
                    nom = nom_ae.strip()
                    if nom:
                        d = datos["equipos_local"][categoria]
                        if dep_ae not in d: d[dep_ae] = {}
                        if cur_ae not in d[dep_ae]: d[dep_ae][cur_ae] = []
                        if nom not in d[dep_ae][cur_ae]:
                            d[dep_ae][cur_ae].append(nom)
                            jl = datos["jugadores_local"]
                            if categoria not in jl: jl[categoria] = {}
                            if dep_ae not in jl[categoria]: jl[categoria][dep_ae] = {}
                            if cur_ae not in jl[categoria][dep_ae]: jl[categoria][dep_ae][cur_ae] = {}
                            jl[categoria][dep_ae][cur_ae][nom] = []
                            guardar_datos(datos)
                            st.success(f"✅ Equipo '{nom}' añadido a {cur_ae}.")
                        else:
                            st.error("Ese equipo ya existe.")
                    else:
                        st.warning("Ingresa un nombre válido.")

            with ptabs[1]:
                deps_aj = list(datos["equipos_local"].get(categoria, {}).keys())
                dep_aj  = st.selectbox("Deporte", deps_aj, key="aj_dep")
                curs_aj = list(datos["equipos_local"].get(categoria, {}).get(dep_aj, {}).keys())
                if curs_aj:
                    cur_aj = st.selectbox("Curso", curs_aj, key="aj_cur")
                    eqs_aj = datos["equipos_local"][categoria][dep_aj].get(cur_aj, [])
                    if eqs_aj:
                        eq_aj  = st.selectbox("Equipo", eqs_aj, key="aj_eq")
                        nom_aj = st.text_input("Nombre del jugador", key="aj_nom")
                        if st.button("Añadir jugador", key="aj_btn"):
                            nom = nom_aj.strip()
                            if nom:
                                jl = datos["jugadores_local"].get(categoria,{}).get(dep_aj,{}).get(cur_aj,{})
                                if eq_aj not in jl: jl[eq_aj] = []
                                if not any(j["nombre"] == nom for j in jl[eq_aj]):
                                    jl[eq_aj].append({"nombre": nom, "puntos": 0})
                                    guardar_datos(datos)
                                    st.success(f"✅ Jugador '{nom}' añadido.")
                                else:
                                    st.error("Ese jugador ya existe.")
                    else:
                        st.info("No hay equipos en ese curso.")
                else:
                    st.info("No hay cursos con equipos.")

            with ptabs[2]:
                deps_ap = list(datos["partidos_local"].get(categoria, {}).keys())
                if deps_ap:
                    dep_ap = st.selectbox("Deporte", deps_ap, key="ap_dep")
                    pl_dep = datos["partidos_local"].get(categoria, {}).get(dep_ap, [])
                    if pl_dep:
                        opts_p = [f"[{i+1}] {p[0][:10]} | {p[1][:50]} | {p[2]}" for i, p in enumerate(pl_dep)]
                        sel_p  = st.selectbox("Partido", opts_p, key="ap_sel")
                        idx_p  = opts_p.index(sel_p)
                        p_sel  = pl_dep[idx_p]
                        nuevo_estado = st.selectbox("Nuevo estado", ["Pendiente","Finalizado"],
                                                     index=0 if p_sel[2]=="Pendiente" else 1, key="ap_est")
                        g1, g2 = p_sel[3], p_sel[4]
                        if nuevo_estado == "Finalizado":
                            try:
                                partes = p_sel[1].split(" vs ")
                                eq1_n  = partes[0].split("(")[0].strip()
                                eq2_n  = partes[1].split("(")[0].strip()
                            except Exception:
                                eq1_n, eq2_n = "Equipo 1", "Equipo 2"
                            col1, col2 = st.columns(2)
                            g1 = col1.number_input(f"⚽ {eq1_n[:20]}", min_value=0, value=int(g1), key="ap_g1")
                            g2 = col2.number_input(f"⚽ {eq2_n[:20]}", min_value=0, value=int(g2), key="ap_g2")
                        if st.button("Guardar cambios", key="ap_btn"):
                            datos["partidos_local"][categoria][dep_ap][idx_p] = [
                                p_sel[0], p_sel[1], nuevo_estado, int(g1), int(g2)
                            ]
                            guardar_datos(datos)
                            st.success("✅ Partido actualizado.")
                    else:
                        st.info("No hay partidos en ese deporte.")
                else:
                    st.info("No hay partidos registrados.")

            with ptabs[3]:
                st.markdown("Genera el fixture **Round-Robin de 7 jornadas**. Un equipo por curso.")
                deps_sort = list(datos["equipos_local"].get(categoria, {}).keys())
                dep_sort  = st.selectbox("Deporte a sortear", deps_sort, key="sort_dep")
                key_s     = f"{categoria}_{dep_sort}"
                ya_hecho  = key_s in datos.get("sorteo_realizado", {})
                if ya_hecho:
                    si = datos["sorteo_realizado"][key_s]
                    st.info(f"✅ Sorteo existente: {si['fecha'][:10]}  •  {si['n_equipos']} equipos")
                    confirmar = st.checkbox("Quiero re-sortear (reemplaza el fixture)", key="sort_confirm")
                else:
                    confirmar = True
                if confirmar:
                    if st.button(f"🎲 Realizar sorteo — {dep_sort}", key="sort_btn"):
                        datos_new, fixture, error = realizar_sorteo(datos, categoria, dep_sort)
                        if error:
                            st.error(error)
                        else:
                            st.session_state.datos = datos_new
                            datos = datos_new
                            guardar_datos(datos_new)
                            n = datos_new["sorteo_realizado"][key_s]["n_equipos"]
                            st.success(f"✅ ¡Sorteo realizado! {n} equipos · 7 jornadas. Ve a la pestaña Partidos.")

    st.markdown(f'<hr style="height:2px;background:linear-gradient(90deg,{t["acento"]},transparent);border:none;margin:16px 0;">', unsafe_allow_html=True)

    # ── Vistas principales ─────────────────────────────────────────────────────
    vista = st.tabs(["📊 Tabla de Posiciones", "📅 Partidos", "👥 Equipos"])

    # ── TABLA ──────────────────────────────────────────────────────────────────
    with vista[0]:
        st.markdown(f"<h3 style='color:{t['text']};'>📊 {deporte} · {categoria}</h3>", unsafe_allow_html=True)
        tabla = calcular_tabla(datos, categoria, deporte)
        if tabla:
            MEDALLAS = {1:"🥇", 2:"🥈", 3:"🥉"}
            TH = f"background:{t['acento']};color:{t['btn_fg']};padding:11px 14px;text-align:center;font-size:0.78rem;font-weight:700;letter-spacing:1px;"
            TD = f"padding:11px 14px;border-bottom:1px solid {t['bg_alt']};text-align:center;font-size:0.9rem;"
            filas = ""
            for r in tabla:
                pos    = r["#"]
                med    = MEDALLAS.get(pos, str(pos))
                dg     = f"+{r['DG']}" if r['DG']>0 else str(r['DG'])
                dg_c   = '#90FF90' if r['DG']>0 else '#FFB0B0' if r['DG']<0 else t['text3']
                row_bg = t['bg_card'] if pos%2==1 else t['bg_alt']
                pos_bg = t['acento'] if pos==1 else '#606060' if pos==2 else '#8B5C1A' if pos==3 else row_bg
                pos_fg = t['btn_fg'] if pos<=2 else '#F5F0E8' if pos==3 else t['text3']
                eq_c   = t['acento'] if pos==1 else t['text'] if pos<=3 else t['text2']
                pts_c  = t['acento'] if pos<=3 else t['text2']
                fw     = '700' if pos<=3 else '400'
                filas += f"""<tr>
                  <td style="{TD}background:{pos_bg};color:{pos_fg};font-weight:700;font-size:1rem;">{med}</td>
                  <td style="{TD}background:{row_bg};text-align:left;padding-left:16px;font-weight:{fw};color:{eq_c};font-size:0.95rem;">{r['Equipo']}</td>
                  <td style="{TD}background:{row_bg};color:{t['text3']};font-size:0.8rem;">{r['Curso']}</td>
                  <td style="{TD}background:{row_bg};">{r['PJ']}</td>
                  <td style="{TD}background:{row_bg};color:#90FF90;font-weight:600;">{r['PG']}</td>
                  <td style="{TD}background:{row_bg};color:#FFE060;">{r['PE']}</td>
                  <td style="{TD}background:{row_bg};color:#FFB0B0;">{r['PP']}</td>
                  <td style="{TD}background:{row_bg};color:{t['text2']};">{r['GF']}</td>
                  <td style="{TD}background:{row_bg};color:{t['text2']};">{r['GC']}</td>
                  <td style="{TD}background:{row_bg};color:{dg_c};font-weight:600;">{dg}</td>
                  <td style="{TD}background:{row_bg};color:{pts_c};font-weight:700;font-size:1rem;">{r['Pts']}</td>
                </tr>"""
            st.markdown(f"""
            <div style="border-radius:10px;overflow:hidden;border:1px solid {t['bg_alt']};margin-top:8px;">
            <table style="width:100%;border-collapse:collapse;">
              <thead><tr>
                <th style="{TH}width:48px;">#</th>
                <th style="{TH}text-align:left;padding-left:16px;">Equipo</th>
                <th style="{TH}">Curso</th>
                <th style="{TH}">PJ</th><th style="{TH}">PG</th><th style="{TH}">PE</th>
                <th style="{TH}">PP</th><th style="{TH}">GF</th><th style="{TH}">GC</th>
                <th style="{TH}">DG</th><th style="{TH}">Pts</th>
              </tr></thead><tbody>{filas}</tbody>
            </table></div>
            <div style="margin-top:10px;color:{t['text3']};font-size:0.8rem;">
              ⚽ Victoria = 3 pts &nbsp;&nbsp; 🤝 Empate = 1 pt &nbsp;&nbsp; ❌ Derrota = 0 pts
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Sin equipos registrados para esta categoría y deporte.")

    # ── PARTIDOS ───────────────────────────────────────────────────────────────
    with vista[1]:
        st.markdown(f"<h3 style='color:{t['text']};'>📅 {deporte} · {categoria}</h3>", unsafe_allow_html=True)
        partidos = datos["partidos_local"].get(categoria, {}).get(deporte, [])
        if partidos:
            fechas_dict = {}
            for p in partidos:
                fechas_dict.setdefault(p[0][:10], []).append(p)
            for j_idx, fch in enumerate(sorted(fechas_dict.keys())):
                st.markdown(f"""
                <div style="background:{t['bg_section']};border-left:4px solid {t['acento']};
                     padding:8px 16px;margin:16px 0 6px;border-radius:0 6px 6px 0;
                     display:flex;align-items:center;gap:12px;">
                  <span style="background:{t['acento']};color:{t['btn_fg']};padding:2px 10px;
                        border-radius:20px;font-size:0.75rem;font-weight:700;">J{j_idx+1}</span>
                  <span style="color:{t['acento']};font-weight:700;font-size:0.9rem;">JORNADA {j_idx+1}</span>
                  <span style="color:{t['text3']};font-size:0.85rem;">📅 {fch}</span>
                </div>""", unsafe_allow_html=True)
                for fecha, enf, estado, g1, g2 in fechas_dict[fch]:
                    st.markdown(partido_card(enf, fecha[11:16], estado, g1, g2), unsafe_allow_html=True)
        else:
            st.info("Sin partidos programados. Usa el Panel de Gestión → Sorteo para generar el fixture.")

    # ── EQUIPOS ────────────────────────────────────────────────────────────────
    with vista[2]:
        st.markdown(f"<h3 style='color:{t['text']};'>👥 {deporte} · {categoria}</h3>", unsafe_allow_html=True)
        equipos_dep = datos["equipos_local"].get(categoria, {}).get(deporte, {})
        if equipos_dep:
            cols = st.columns(2)
            idx_col = 0
            for cur, eqs in equipos_dep.items():
                if not eqs:
                    continue
                with cols[idx_col % 2]:
                    jugs_total = sum(
                        len(datos["jugadores_local"].get(categoria,{}).get(deporte,{}).get(cur,{}).get(eq,[]))
                        for eq in eqs
                    )
                    st.markdown(f"""
                    <div style="background:{t['bg_card']};border:1px solid {t['bg_alt']};
                         border-top:3px solid {t['acento']};border-radius:8px;
                         padding:14px 16px;margin-bottom:12px;">
                      <div style="font-size:0.7rem;font-weight:700;letter-spacing:2px;
                                  color:{t['text3']};margin-bottom:10px;">CURSO {cur}</div>
                    """, unsafe_allow_html=True)
                    for eq in eqs:
                        jugs = (datos["jugadores_local"].get(categoria,{}).get(deporte,{})
                                .get(cur,{}).get(eq,[]))
                        nombres = ', '.join(j["nombre"] for j in jugs) if jugs else ""
                        st.markdown(f"""
                      <div style="display:flex;align-items:flex-start;gap:10px;
                                  padding:8px 0;border-bottom:1px solid {t['bg_alt']};">
                        <span style="font-size:1.1rem;">⚽</span>
                        <div style="flex:1;">
                          <span style="font-weight:700;color:{t['text']};font-size:0.95rem;">{eq}</span>
                          <span style="background:{t['acento']};color:{t['btn_fg']};padding:1px 8px;
                                border-radius:20px;font-size:0.7rem;font-weight:700;margin-left:8px;">{len(jugs)} jug.</span>
                          {'<div style="color:' + t['text3'] + ';font-size:0.78rem;margin-top:3px;">' + nombres + '</div>' if nombres else ''}
                        </div>
                      </div>""", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                idx_col += 1
        else:
            st.info("Sin equipos registrados. Añade equipos desde el Panel de Gestión.")
