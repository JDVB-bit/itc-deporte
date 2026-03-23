import streamlit as st
from data import cargar_datos, guardar_datos

st.set_page_config(
    page_title="ITC Deportes",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS personalizado ─────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Fuentes y base */
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow:wght@400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Barlow', sans-serif; }

/* Header dorado */
.itc-hero {
    background: linear-gradient(135deg, #0A0A0A 0%, #1A1200 100%);
    border-left: 6px solid #D4A017;
    padding: 24px 32px;
    margin-bottom: 24px;
    border-radius: 0 8px 8px 0;
}
.itc-hero h1 {
    font-family: 'Bebas Neue', Impact, sans-serif;
    font-size: 3.5rem;
    color: #D4A017;
    margin: 0;
    letter-spacing: 4px;
}
.itc-hero p { color: #9A9080; margin: 4px 0 0; font-size: 1rem; }

/* Tarjetas de stats */
.stat-card {
    background: #141414;
    border: 1px solid #222018;
    border-top: 3px solid #D4A017;
    border-radius: 8px;
    padding: 16px 20px;
    text-align: center;
}
.stat-card .num { font-size: 2rem; font-weight: 700; color: #D4A017; }
.stat-card .lbl { font-size: 0.8rem; color: #9A9080; text-transform: uppercase; letter-spacing: 1px; }

/* Badge de estado */
.badge-fin  { background:#1A6020; color:#90FF90; padding:3px 10px; border-radius:12px; font-size:0.75rem; font-weight:600; }
.badge-pen  { background:#8A6000; color:#FFE060; padding:3px 10px; border-radius:12px; font-size:0.75rem; font-weight:600; }
.badge-apl  { background:#7A1010; color:#FFB0B0; padding:3px 10px; border-radius:12px; font-size:0.75rem; font-weight:600; }

/* Tabla de posiciones */
.pos-table { width:100%; border-collapse:collapse; }
.pos-table th { background:#D4A017; color:#050505; padding:10px 12px; text-align:center; font-size:0.8rem; letter-spacing:1px; }
.pos-table td { padding:9px 12px; border-bottom:1px solid #1A1A1A; text-align:center; font-size:0.9rem; }
.pos-table tr:nth-child(even) td { background:#101010; }
.pos-table tr:nth-child(odd)  td { background:#141414; }
.pos-gold  td:first-child { background:#D4A017; color:#050505; font-weight:700; }
.pos-silver td:first-child { background:#606060; color:#050505; font-weight:700; }
.pos-bronze td:first-child { background:#8B5C1A; color:#F5F0E8; font-weight:700; }
.pts-gold { color:#D4A017; font-weight:700; }

/* Partido row */
.partido-row {
    background:#141414;
    border-left: 3px solid #D4A017;
    border-radius: 4px;
    padding: 10px 16px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.partido-vs { font-weight:600; color:#F5F0E8; }
.partido-fecha { color:#5A5550; font-size:0.8rem; }

/* Sidebar styling */
[data-testid="stSidebar"] { background:#050505; border-right:1px solid #1A1A1A; }
[data-testid="stSidebar"] .stRadio label { color:#9A9080 !important; }

/* Divider dorado */
.gold-divider { height:2px; background:linear-gradient(90deg,#D4A017,transparent); margin:20px 0; border:none; }

/* Sorteo jornada */
.jornada-hdr {
    background:#1A1200;
    border-left:4px solid #D4A017;
    padding:8px 16px;
    margin-top:12px;
    border-radius:0 4px 4px 0;
    font-weight:600;
    color:#D4A017;
}
.match-row {
    background:#0F0F0F;
    padding:8px 16px;
    border-bottom:1px solid #1A1A1A;
    display:flex;
    align-items:center;
    gap:12px;
}

/* Botón dorado override */
.stButton > button {
    background:#D4A017 !important;
    color:#050505 !important;
    font-weight:700 !important;
    border:none !important;
    border-radius:6px !important;
}
.stButton > button:hover {
    background:#FFD040 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "datos" not in st.session_state:
    st.session_state.datos = cargar_datos()
if "rol" not in st.session_state:
    st.session_state.rol = "invitado"
if "usuario" not in st.session_state:
    st.session_state.usuario = None

datos = st.session_state.datos

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚽ ITC Deportes")
    st.markdown("---")

    if st.session_state.rol == "invitado":
        st.markdown("**👤 Modo Invitado**")
        with st.expander("🔐 Iniciar sesión como Profesor"):
            user = st.text_input("Usuario", key="sb_user")
            pwd  = st.text_input("Contraseña", type="password", key="sb_pwd")
            if st.button("Entrar"):
                if (user in datos["usuarios"]
                        and datos["usuarios"][user] == pwd
                        and datos["usuarios_tipo"].get(user) == "profesor"):
                    st.session_state.rol = "profesor"
                    st.session_state.usuario = user
                    st.success(f"¡Bienvenido, {user}!")
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas.")
    else:
        st.markdown(f"**★ {st.session_state.usuario.upper()}**")
        st.caption("Profesor")
        if st.button("Cerrar sesión"):
            st.session_state.rol = "invitado"
            st.session_state.usuario = None
            st.rerun()

    st.markdown("---")
    torneo = st.radio(
        "Selecciona torneo",
        ["🏆 Intercolegiados", "🎯 Intercursos"],
        key="torneo_sel",
    )

    if torneo == "🎯 Intercursos":
        st.markdown("**Categoría**")
        categoria = st.radio(
            "cat",
            ["PRIMERA", "SEGUNDA", "TERCERA"],
            label_visibility="collapsed",
            key="cat_sel",
        )
        cat_info = {"PRIMERA": "Grados 6° y 7°", "SEGUNDA": "Grados 8° y 9°", "TERCERA": "Grados 10° y 11°"}
        st.caption(cat_info.get(categoria, ""))

        st.markdown("**Deporte**")
        from data import ICONOS_DEP
        dep_opts = list(datos["equipos_local"].get(categoria, {}).keys()) or \
                   ["Balonmano", "Microfutbol", "Baloncesto", "Voleyball"]
        deporte = st.radio(
            "dep",
            [f"{ICONOS_DEP.get(d,'🏅')} {d}" for d in dep_opts],
            label_visibility="collapsed",
            key="dep_sel",
        )
        deporte = deporte.split(" ", 1)[1] if " " in deporte else deporte
    else:
        categoria = None
        deporte = None

# ── Main content ───────────────────────────────────────────────────────────────

st.markdown("""
<div class="itc-hero">
  <h1>ITC DEPORTES</h1>
  <p>Sistema de gestión deportiva institucional · 2026</p>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  INTERCOLEGIADOS
# ═══════════════════════════════════════════════════════════════════════════════
if torneo == "🏆 Intercolegiados":
    from data import DEPORTES, ICONOS_DEP
    st.markdown("## 🏆 Intercolegiados ITC")

    tabs = st.tabs([f"{ICONOS_DEP[d]} {d}" for d in DEPORTES])

    for i, dep in enumerate(DEPORTES):
        with tabs[i]:
            c1, c2 = st.columns([1, 1])

            with c1:
                st.markdown("### 🏅 Logros destacados")
                logros_dep = [l for l in datos["logros"] if dep in l[1]]
                if logros_dep:
                    for anio, desc in logros_dep:
                        st.markdown(f"""
                        <div style="display:flex;align-items:center;gap:12px;background:#141414;
                             border-left:3px solid #D4A017;padding:10px 16px;
                             margin-bottom:6px;border-radius:0 6px 6px 0;">
                          <span style="background:#D4A017;color:#050505;padding:4px 10px;
                                border-radius:4px;font-weight:700;font-size:0.85rem;">{anio}</span>
                          <span style="color:#F5F0E8;">{desc}</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Sin logros registrados.")

                if st.session_state.rol == "profesor":
                    st.markdown("---")
                    with st.expander("➕ Añadir logro"):
                        anio_n  = st.text_input("Año", key=f"logro_anio_{dep}")
                        desc_n  = st.text_input("Descripción", key=f"logro_desc_{dep}")
                        if st.button("Guardar logro", key=f"logro_btn_{dep}"):
                            if anio_n and desc_n:
                                datos["logros"].append([anio_n, f"{dep} - {desc_n}"])
                                guardar_datos(datos)
                                st.success("Logro añadido.")
                                st.rerun()

            with c2:
                st.markdown("### 📅 Partidos")
                partidos_dep = datos["partidos"].get(dep, [])
                if partidos_dep:
                    for fecha, enf, estado in partidos_dep:
                        if estado == "Finalizado":
                            badge = '<span class="badge-fin">Finalizado</span>'
                        elif estado == "Pendiente":
                            badge = '<span class="badge-pen">Pendiente</span>'
                        else:
                            badge = '<span class="badge-apl">Aplazado</span>'
                        st.markdown(f"""
                        <div class="partido-row">
                          <div>
                            <div class="partido-vs">{enf}</div>
                            <div class="partido-fecha">📅 {fecha}</div>
                          </div>
                          {badge}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Sin partidos programados.")

                if st.session_state.rol == "profesor":
                    st.markdown("---")
                    with st.expander("➕ Añadir partido"):
                        fecha_p  = st.text_input("Fecha (AAAA-MM-DD)", key=f"p_fecha_{dep}")
                        enf_p    = st.text_input("Enfrentamiento", key=f"p_enf_{dep}")
                        estado_p = st.selectbox("Estado", ["Pendiente","Finalizado","Aplazado"], key=f"p_est_{dep}")
                        if st.button("Guardar partido", key=f"p_btn_{dep}"):
                            if fecha_p and enf_p:
                                datos["partidos"].setdefault(dep, []).append([fecha_p, enf_p, estado_p])
                                guardar_datos(datos)
                                st.success("Partido añadido.")
                                st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
#  INTERCURSOS
# ═══════════════════════════════════════════════════════════════════════════════
else:
    from data import ICONOS_DEP, calcular_tabla, realizar_sorteo

    st.markdown(f"## 🎯 Intercursos — Categoría {categoria}")
    st.caption({"PRIMERA": "Grados 6° y 7°", "SEGUNDA": "Grados 8° y 9°", "TERCERA": "Grados 10° y 11°"}.get(categoria, ""))

    # Panel profesor
    if st.session_state.rol == "profesor":
        with st.expander("⚙️ Panel de Gestión — Profesor", expanded=False):
            ptabs = st.tabs(["➕ Añadir Equipo", "👤 Añadir Jugador", "✏️ Actualizar Partido", "🎲 Sorteo"])

            # ── Añadir equipo ──────────────────────────────────────────────────
            with ptabs[0]:
                from data import CATEGORIAS_LOCAL
                deps_panel = list(datos["equipos_local"].get(categoria, {}).keys())
                dep_ae = st.selectbox("Deporte", deps_panel, key="ae_dep")
                cur_ae = st.selectbox("Curso", CATEGORIAS_LOCAL.get(categoria, []), key="ae_cur")
                nom_ae = st.text_input("Nombre del equipo", key="ae_nom")
                if st.button("Añadir equipo", key="ae_btn"):
                    if nom_ae.strip():
                        d = datos["equipos_local"][categoria]
                        if dep_ae not in d: d[dep_ae] = {}
                        if cur_ae not in d[dep_ae]: d[dep_ae][cur_ae] = []
                        if nom_ae.strip() not in d[dep_ae][cur_ae]:
                            d[dep_ae][cur_ae].append(nom_ae.strip())
                            jl = datos["jugadores_local"]
                            if categoria not in jl: jl[categoria] = {}
                            if dep_ae not in jl[categoria]: jl[categoria][dep_ae] = {}
                            if cur_ae not in jl[categoria][dep_ae]: jl[categoria][dep_ae][cur_ae] = {}
                            jl[categoria][dep_ae][cur_ae][nom_ae.strip()] = []
                            guardar_datos(datos)
                            st.success(f"Equipo '{nom_ae.strip()}' añadido.")
                            st.rerun()
                        else:
                            st.error("Ese equipo ya existe.")
                    else:
                        st.warning("Ingresa un nombre válido.")

            # ── Añadir jugador ─────────────────────────────────────────────────
            with ptabs[1]:
                deps_panel2 = list(datos["equipos_local"].get(categoria, {}).keys())
                dep_aj = st.selectbox("Deporte", deps_panel2, key="aj_dep")
                curs_aj = list(datos["equipos_local"].get(categoria, {}).get(dep_aj, {}).keys())
                if curs_aj:
                    cur_aj = st.selectbox("Curso", curs_aj, key="aj_cur")
                    eqs_aj = datos["equipos_local"][categoria][dep_aj].get(cur_aj, [])
                    if eqs_aj:
                        eq_aj  = st.selectbox("Equipo", eqs_aj, key="aj_eq")
                        nom_aj = st.text_input("Nombre del jugador", key="aj_nom")
                        if st.button("Añadir jugador", key="aj_btn"):
                            if nom_aj.strip():
                                jl = datos["jugadores_local"][categoria][dep_aj][cur_aj]
                                if eq_aj not in jl: jl[eq_aj] = []
                                if not any(j["nombre"] == nom_aj.strip() for j in jl[eq_aj]):
                                    jl[eq_aj].append({"nombre": nom_aj.strip(), "puntos": 0})
                                    guardar_datos(datos)
                                    st.success(f"Jugador '{nom_aj.strip()}' añadido.")
                                    st.rerun()
                                else:
                                    st.error("Ese jugador ya existe.")
                    else:
                        st.info("No hay equipos en ese curso.")
                else:
                    st.info("No hay cursos con equipos.")

            # ── Actualizar partido ─────────────────────────────────────────────
            with ptabs[2]:
                deps_panel3 = list(datos["partidos_local"].get(categoria, {}).keys())
                if deps_panel3:
                    dep_ap = st.selectbox("Deporte", deps_panel3, key="ap_dep")
                    partidos_list = datos["partidos_local"].get(categoria, {}).get(dep_ap, [])
                    if partidos_list:
                        opts_p = [f"[{i+1}] {p[0][:10]} | {p[1]} | {p[2]}" for i, p in enumerate(partidos_list)]
                        sel_p  = st.selectbox("Partido", opts_p, key="ap_sel")
                        idx_p  = opts_p.index(sel_p)
                        p_sel  = partidos_list[idx_p]

                        nuevo_estado = st.selectbox("Nuevo estado", ["Pendiente", "Finalizado"], key="ap_est",
                                                     index=0 if p_sel[2]=="Pendiente" else 1)
                        g1, g2 = p_sel[3], p_sel[4]
                        if nuevo_estado == "Finalizado":
                            col1, col2 = st.columns(2)
                            partes = p_sel[1].split(" vs ")
                            eq1_name = partes[0].split("(")[0].strip() if partes else "Equipo 1"
                            eq2_name = partes[1].split("(")[0].strip() if len(partes)>1 else "Equipo 2"
                            g1 = col1.number_input(f"Goles {eq1_name[:20]}", min_value=0, value=int(g1), key="ap_g1")
                            g2 = col2.number_input(f"Goles {eq2_name[:20]}", min_value=0, value=int(g2), key="ap_g2")

                        if st.button("Guardar cambios", key="ap_btn"):
                            datos["partidos_local"][categoria][dep_ap][idx_p] = [
                                p_sel[0], p_sel[1], nuevo_estado, int(g1), int(g2)
                            ]
                            guardar_datos(datos)
                            st.success("Partido actualizado.")
                            st.rerun()
                    else:
                        st.info("No hay partidos en ese deporte.")
                else:
                    st.info("No hay partidos registrados.")

            # ── Sorteo ─────────────────────────────────────────────────────────
            with ptabs[3]:
                st.markdown("Genera el fixture Round-Robin de 7 jornadas.")
                deps_sort = list(datos["equipos_local"].get(categoria, {}).keys())
                dep_sort  = st.selectbox("Deporte a sortear", deps_sort, key="sort_dep")
                key_s     = f"{categoria}_{dep_sort}"
                ya_hecho  = key_s in datos.get("sorteo_realizado", {})

                if ya_hecho:
                    si = datos["sorteo_realizado"][key_s]
                    st.info(f"✅ Sorteo existente: {si['fecha'][:10]}  •  {si['n_equipos']} equipos")
                    if not st.checkbox("Quiero re-sortear (borra el fixture actual)", key="sort_confirm"):
                        st.stop()

                if st.button(f"🎲 Realizar sorteo — {dep_sort}", key="sort_btn"):
                    datos_new, fixture, error = realizar_sorteo(datos, categoria, dep_sort)
                    if error:
                        st.error(error)
                    else:
                        st.session_state.datos = datos_new
                        guardar_datos(datos_new)
                        st.success("¡Sorteo realizado! Revisa la pestaña de Partidos.")
                        st.session_state["ver_fixture"] = fixture
                        st.rerun()

    st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

    # ── Vistas principales ────────────────────────────────────────────────────
    vista = st.tabs(["📊 Tabla", "📅 Partidos", "👥 Equipos"])

    # ── TABLA ─────────────────────────────────────────────────────────────────
    with vista[0]:
        st.markdown(f"### 📊 Tabla de Posiciones — {deporte}")
        tabla = calcular_tabla(datos, categoria, deporte)

        if tabla:
            MEDALLAS = {1: "🥇", 2: "🥈", 3: "🥉"}
            filas_html = ""
            for r in tabla:
                pos   = r["#"]
                med   = MEDALLAS.get(pos, str(pos))
                cls   = "pos-gold" if pos==1 else "pos-silver" if pos==2 else "pos-bronze" if pos==3 else ""
                pts_c = 'class="pts-gold"' if pos<=3 else ""
                dg    = f"+{r['DG']}" if r['DG']>0 else str(r['DG'])
                filas_html += f"""
                <tr class="{cls}">
                  <td>{med}</td>
                  <td style="text-align:left;padding-left:14px;font-weight:{'700' if pos<=3 else '400'};
                      color:{'#D4A017' if pos==1 else '#F5F0E8'}">{r['Equipo']}</td>
                  <td style="color:#5A5550;">{r['Curso']}</td>
                  <td>{r['PJ']}</td><td>{r['PG']}</td><td>{r['PE']}</td><td>{r['PP']}</td>
                  <td>{r['GF']}</td><td>{r['GC']}</td>
                  <td style="color:{'#90FF90' if r['DG']>0 else '#FFB0B0' if r['DG']<0 else '#9A9080'};font-weight:600;">{dg}</td>
                  <td {pts_c} style="font-weight:700;">{r['Pts']}</td>
                </tr>"""

            st.markdown(f"""
            <table class="pos-table">
              <thead><tr>
                <th>#</th><th style="text-align:left;padding-left:14px;">Equipo</th>
                <th>Curso</th><th>PJ</th><th>PG</th><th>PE</th><th>PP</th>
                <th>GF</th><th>GC</th><th>DG</th><th>Pts</th>
              </tr></thead>
              <tbody>{filas_html}</tbody>
            </table>
            <br>
            <small style="color:#5A5550;">⚽ Victoria = 3 pts &nbsp;|&nbsp; 🤝 Empate = 1 pt &nbsp;|&nbsp; ❌ Derrota = 0 pts</small>
            """, unsafe_allow_html=True)
        else:
            st.info("Sin equipos registrados en esta categoría y deporte.")

    # ── PARTIDOS ──────────────────────────────────────────────────────────────
    with vista[1]:
        st.markdown(f"### 📅 Partidos — {deporte}")
        partidos = datos["partidos_local"].get(categoria, {}).get(deporte, [])

        if partidos:
            # Agrupar por fecha
            fechas_dict = {}
            for p in partidos:
                fch = p[0][:10]
                fechas_dict.setdefault(fch, []).append(p)

            for j_idx, fch in enumerate(sorted(fechas_dict.keys())):
                st.markdown(f'<div class="jornada-hdr">JORNADA {j_idx+1} &nbsp;·&nbsp; 📅 {fch}</div>', unsafe_allow_html=True)
                for fecha, enf, estado, g1, g2 in fechas_dict[fch]:
                    if estado == "Finalizado":
                        badge   = '<span class="badge-fin">Finalizado</span>'
                        marcador = f'<span style="background:#D4A017;color:#050505;padding:4px 12px;border-radius:4px;font-weight:700;">{g1} — {g2}</span>'
                    elif estado == "Pendiente":
                        badge    = '<span class="badge-pen">Pendiente</span>'
                        marcador = ""
                    else:
                        badge    = '<span class="badge-apl">Aplazado</span>'
                        marcador = ""

                    st.markdown(f"""
                    <div class="partido-row">
                      <div>
                        <div class="partido-vs">{enf}</div>
                        <div class="partido-fecha">{fecha[11:16]} hrs</div>
                      </div>
                      <div style="display:flex;align-items:center;gap:10px;">
                        {marcador}
                        {badge}
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Sin partidos programados. Usa el Panel de Gestión para realizar el sorteo.")

    # ── EQUIPOS ───────────────────────────────────────────────────────────────
    with vista[2]:
        st.markdown(f"### 👥 Equipos — {deporte}")
        equipos_dep = datos["equipos_local"].get(categoria, {}).get(deporte, {})

        if equipos_dep:
            for cur, eqs in equipos_dep.items():
                if not eqs:
                    continue
                with st.expander(f"📚 Curso {cur}  ({len(eqs)} equipo{'s' if len(eqs)!=1 else ''})", expanded=True):
                    for eq in eqs:
                        jugs = datos["jugadores_local"].get(categoria, {}).get(deporte, {}).get(cur, {}).get(eq, [])
                        st.markdown(f"""
                        <div style="background:#141414;border-left:3px solid #D4A017;
                             padding:10px 16px;margin-bottom:6px;border-radius:0 6px 6px 0;
                             display:flex;align-items:center;gap:12px;">
                          <span style="font-size:1.2rem;">⚽</span>
                          <div>
                            <span style="font-weight:700;color:#F5F0E8;">{eq}</span>
                            <span style="background:#D4A017;color:#050505;padding:2px 8px;
                                  border-radius:10px;font-size:0.75rem;font-weight:700;margin-left:8px;">
                              {len(jugs)} jug.
                            </span>
                            {'<br><small style="color:#5A5550;">' + ', '.join(j["nombre"] for j in jugs) + '</small>' if jugs else ''}
                          </div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("Sin equipos registrados. Añade equipos desde el Panel de Gestión.")
