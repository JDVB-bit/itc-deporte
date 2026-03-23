import streamlit as st
from data import cargar_datos, guardar_datos, ICONOS_DEP, DEPORTES, CATEGORIAS_LOCAL, calcular_tabla, realizar_sorteo

st.set_page_config(
    page_title="ITC Deportes",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Barlow', sans-serif; }
.stButton > button {
    background:#D4A017 !important; color:#050505 !important;
    font-weight:700 !important; border:none !important; border-radius:6px !important;
}
.stButton > button:hover { background:#FFD040 !important; }
[data-testid="stSidebar"] { background:#050505 !important; }
</style>
""", unsafe_allow_html=True)

TH = "background:#D4A017;color:#050505;padding:10px 12px;text-align:center;font-size:0.8rem;"
TD = "padding:9px 12px;border-bottom:1px solid #1A1A1A;text-align:center;font-size:0.9rem;"

def badge(estado):
    if estado == "Finalizado":
        return '<span style="background:#1A6020;color:#90FF90;padding:3px 10px;border-radius:12px;font-size:0.75rem;font-weight:600;">Finalizado</span>'
    elif estado == "Pendiente":
        return '<span style="background:#8A6000;color:#FFE060;padding:3px 10px;border-radius:12px;font-size:0.75rem;font-weight:600;">Pendiente</span>'
    return '<span style="background:#7A1010;color:#FFB0B0;padding:3px 10px;border-radius:12px;font-size:0.75rem;font-weight:600;">Aplazado</span>'

def partido_html(enf, hora, estado, g1=0, g2=0):
    marcador = f'<span style="background:#D4A017;color:#050505;padding:4px 12px;border-radius:4px;font-weight:700;margin-right:8px;">{g1} — {g2}</span>' if estado == "Finalizado" else ""
    return f"""<div style="background:#141414;border-left:3px solid #D4A017;border-radius:4px;
         padding:10px 16px;margin-bottom:6px;display:flex;align-items:center;justify-content:space-between;">
      <div>
        <div style="font-weight:600;color:#F5F0E8;">{enf}</div>
        <div style="color:#5A5550;font-size:0.8rem;">{hora} hrs</div>
      </div>
      <div style="display:flex;align-items:center;gap:8px;">{marcador}{badge(estado)}</div>
    </div>"""

if "datos" not in st.session_state:
    st.session_state.datos = cargar_datos()
if "rol" not in st.session_state:
    st.session_state.rol = "invitado"
if "usuario" not in st.session_state:
    st.session_state.usuario = None

datos = st.session_state.datos

with st.sidebar:
    st.markdown("## ⚽ ITC Deportes")
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
    torneo = st.radio("Selecciona torneo",
                      ["🏆 Intercolegiados", "🎯 Intercursos"], key="torneo_sel")

    if torneo == "🎯 Intercursos":
        st.markdown("**Categoría**")
        categoria = st.radio("cat", ["PRIMERA", "SEGUNDA", "TERCERA"],
                             label_visibility="collapsed", key="cat_sel")
        st.caption({"PRIMERA":"Grados 6° y 7°","SEGUNDA":"Grados 8° y 9°","TERCERA":"Grados 10° y 11°"}.get(categoria,""))
        st.markdown("**Deporte**")
        dep_opts = list(datos["equipos_local"].get(categoria, {}).keys()) or list(DEPORTES)
        deporte_raw = st.radio("dep",
                               [f"{ICONOS_DEP.get(d,'🏅')} {d}" for d in dep_opts],
                               label_visibility="collapsed", key="dep_sel")
        deporte = deporte_raw.split(" ", 1)[1] if " " in deporte_raw else deporte_raw
    else:
        categoria = None
        deporte   = None

st.markdown("""
<div style="background:linear-gradient(135deg,#0A0A0A,#1A1200);border-left:6px solid #D4A017;
     padding:24px 32px;margin-bottom:24px;border-radius:0 8px 8px 0;">
  <h1 style="font-family:'Bebas Neue',Impact,sans-serif;font-size:3rem;color:#D4A017;
             margin:0;letter-spacing:4px;">ITC DEPORTES</h1>
  <p style="color:#9A9080;margin:4px 0 0;">Sistema de gestión deportiva institucional · 2026</p>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  INTERCOLEGIADOS
# ═══════════════════════════════════════════════════════════════════════════════
if torneo == "🏆 Intercolegiados":
    st.markdown("## 🏆 Intercolegiados ITC")
    tabs = st.tabs([f"{ICONOS_DEP[d]} {d}" for d in DEPORTES])

    for i, dep in enumerate(DEPORTES):
        with tabs[i]:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### 🏅 Logros")
                logros_dep = [l for l in datos["logros"] if dep in l[1]]
                if logros_dep:
                    for anio, desc in logros_dep:
                        st.markdown(f"""<div style="display:flex;align-items:center;gap:12px;background:#141414;
                             border-left:3px solid #D4A017;padding:10px 16px;
                             margin-bottom:6px;border-radius:0 6px 6px 0;">
                          <span style="background:#D4A017;color:#050505;padding:4px 10px;
                                border-radius:4px;font-weight:700;">{anio}</span>
                          <span style="color:#F5F0E8;">{desc}</span>
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
                st.markdown("### 📅 Partidos")
                partidos_dep = datos["partidos"].get(dep, [])
                if partidos_dep:
                    for p in partidos_dep:
                        fecha, enf, estado = p[0], p[1], p[2]
                        st.markdown(partido_html(enf, fecha, estado), unsafe_allow_html=True)
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
    st.markdown(f"## 🎯 Intercursos — Categoría {categoria}")

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
                        opts_p = [f"[{i+1}] {p[0][:10]} | {p[1][:45]} | {p[2]}" for i, p in enumerate(pl_dep)]
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
                            g1 = col1.number_input(f"Goles {eq1_n[:18]}", min_value=0, value=int(g1), key="ap_g1")
                            g2 = col2.number_input(f"Goles {eq2_n[:18]}", min_value=0, value=int(g2), key="ap_g2")
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
                st.markdown("Genera el fixture Round-Robin de **7 jornadas**.")
                deps_sort = list(datos["equipos_local"].get(categoria, {}).keys())
                dep_sort  = st.selectbox("Deporte a sortear", deps_sort, key="sort_dep")
                key_s     = f"{categoria}_{dep_sort}"
                ya_hecho  = key_s in datos.get("sorteo_realizado", {})
                if ya_hecho:
                    si = datos["sorteo_realizado"][key_s]
                    st.info(f"✅ Sorteo existente: {si['fecha'][:10]}  •  {si['n_equipos']} equipos")
                    confirmar = st.checkbox("Quiero re-sortear", key="sort_confirm")
                else:
                    confirmar = True
                if confirmar:
                    if st.button(f"🎲 Sortear — {dep_sort}", key="sort_btn"):
                        datos_new, fixture, error = realizar_sorteo(datos, categoria, dep_sort)
                        if error:
                            st.error(error)
                        else:
                            st.session_state.datos = datos_new
                            datos = datos_new
                            guardar_datos(datos_new)
                            n = datos_new["sorteo_realizado"][key_s]["n_equipos"]
                            st.success(f"✅ ¡Sorteo realizado! {n} equipos · 7 jornadas. Ve a la pestaña Partidos.")

    st.markdown('<hr style="height:2px;background:linear-gradient(90deg,#D4A017,transparent);border:none;margin:16px 0;">', unsafe_allow_html=True)

    vista = st.tabs(["📊 Tabla de Posiciones", "📅 Partidos", "👥 Equipos"])

    with vista[0]:
        st.markdown(f"### 📊 Tabla — {deporte} · {categoria}")
        tabla = calcular_tabla(datos, categoria, deporte)
        if tabla:
            MEDALLAS = {1:"🥇", 2:"🥈", 3:"🥉"}
            filas = ""
            for r in tabla:
                pos    = r["#"]
                med    = MEDALLAS.get(pos, str(pos))
                dg     = f"+{r['DG']}" if r['DG']>0 else str(r['DG'])
                dg_c   = '#90FF90' if r['DG']>0 else '#FFB0B0' if r['DG']<0 else '#9A9080'
                row_bg = '#141414' if pos%2==1 else '#101010'
                pos_bg = '#D4A017' if pos==1 else '#606060' if pos==2 else '#8B5C1A' if pos==3 else row_bg
                pos_fg = '#050505' if pos<=2 else '#F5F0E8' if pos==3 else '#9A9080'
                eq_c   = '#D4A017' if pos==1 else '#F5F0E8' if pos<=3 else '#C0B8A8'
                pts_c  = '#D4A017' if pos<=3 else '#F5F0E8'
                fw     = '700' if pos<=3 else '400'
                filas += f"""<tr>
                  <td style="{TD}background:{pos_bg};color:{pos_fg};font-weight:700;">{med}</td>
                  <td style="{TD}background:{row_bg};text-align:left;padding-left:14px;font-weight:{fw};color:{eq_c};">{r['Equipo']}</td>
                  <td style="{TD}background:{row_bg};color:#5A5550;">{r['Curso']}</td>
                  <td style="{TD}background:{row_bg};">{r['PJ']}</td>
                  <td style="{TD}background:{row_bg};color:#90FF90;">{r['PG']}</td>
                  <td style="{TD}background:{row_bg};color:#FFE060;">{r['PE']}</td>
                  <td style="{TD}background:{row_bg};color:#FFB0B0;">{r['PP']}</td>
                  <td style="{TD}background:{row_bg};">{r['GF']}</td>
                  <td style="{TD}background:{row_bg};">{r['GC']}</td>
                  <td style="{TD}background:{row_bg};color:{dg_c};font-weight:600;">{dg}</td>
                  <td style="{TD}background:{row_bg};color:{pts_c};font-weight:700;">{r['Pts']}</td>
                </tr>"""
            st.markdown(f"""
            <table style="width:100%;border-collapse:collapse;margin-top:8px;">
              <thead><tr>
                <th style="{TH}">#</th>
                <th style="{TH}text-align:left;padding-left:14px;">Equipo</th>
                <th style="{TH}">Curso</th>
                <th style="{TH}">PJ</th><th style="{TH}">PG</th><th style="{TH}">PE</th>
                <th style="{TH}">PP</th><th style="{TH}">GF</th><th style="{TH}">GC</th>
                <th style="{TH}">DG</th><th style="{TH}">Pts</th>
              </tr></thead><tbody>{filas}</tbody>
            </table>
            <br><small style="color:#5A5550;">⚽ Victoria = 3 pts &nbsp;|&nbsp; 🤝 Empate = 1 pt &nbsp;|&nbsp; ❌ Derrota = 0 pts</small>
            """, unsafe_allow_html=True)
        else:
            st.info("Sin equipos registrados para esta categoría y deporte.")

    with vista[1]:
        st.markdown(f"### 📅 Partidos — {deporte} · {categoria}")
        partidos = datos["partidos_local"].get(categoria, {}).get(deporte, [])
        if partidos:
            fechas_dict = {}
            for p in partidos:
                fechas_dict.setdefault(p[0][:10], []).append(p)
            for j_idx, fch in enumerate(sorted(fechas_dict.keys())):
                st.markdown(
                    f'<div style="background:#1A1200;border-left:4px solid #D4A017;padding:8px 16px;'
                    f'margin-top:12px;border-radius:0 4px 4px 0;font-weight:600;color:#D4A017;">'
                    f'JORNADA {j_idx+1} &nbsp;·&nbsp; 📅 {fch}</div>',
                    unsafe_allow_html=True)
                for fecha, enf, estado, g1, g2 in fechas_dict[fch]:
                    st.markdown(partido_html(enf, fecha[11:16], estado, g1, g2), unsafe_allow_html=True)
        else:
            st.info("Sin partidos programados. Usa el Panel de Gestión → Sorteo para generar el fixture.")

    with vista[2]:
        st.markdown(f"### 👥 Equipos — {deporte} · {categoria}")
        equipos_dep = datos["equipos_local"].get(categoria, {}).get(deporte, {})
        if equipos_dep:
            for cur, eqs in equipos_dep.items():
                if not eqs:
                    continue
                with st.expander(f"📚 Curso {cur}  —  {len(eqs)} equipo{'s' if len(eqs)!=1 else ''}", expanded=True):
                    for eq in eqs:
                        jugs = (datos["jugadores_local"]
                                .get(categoria, {}).get(deporte, {})
                                .get(cur, {}).get(eq, []))
                        nombres = ', '.join(j["nombre"] for j in jugs) if jugs else ""
                        st.markdown(f"""<div style="background:#141414;border-left:3px solid #D4A017;
                             padding:10px 16px;margin-bottom:6px;border-radius:0 6px 6px 0;">
                          <span style="font-weight:700;color:#F5F0E8;">⚽ {eq}</span>
                          <span style="background:#D4A017;color:#050505;padding:2px 8px;
                                border-radius:10px;font-size:0.75rem;font-weight:700;margin-left:10px;">{len(jugs)} jug.</span>
                          {'<br><small style="color:#5A5550;margin-top:4px;display:block;">' + nombres + '</small>' if nombres else ''}
                        </div>""", unsafe_allow_html=True)
        else:
            st.info("Sin equipos registrados. Añade equipos desde el Panel de Gestión.")
