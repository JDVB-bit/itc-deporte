import streamlit as st
from data import (
    ICONOS_DEP, DEPORTES, CATEGORIAS_LOCAL, USUARIOS, USUARIOS_TIPO,
    obtener_equipos, agregar_equipo, eliminar_equipo,
    obtener_jugadores, agregar_jugador, eliminar_jugador,
    obtener_partidos, actualizar_partido, insertar_partido,
    obtener_logros, agregar_logro, eliminar_logro,
    obtener_partidos_inter, agregar_partido_inter, eliminar_partido_inter,
    obtener_sorteo, realizar_sorteo, calcular_tabla,
)

st.set_page_config(page_title="ITC Deportes", page_icon="⚽", layout="wide")

# ── Session state ──────────────────────────────────────────────────────────────
for k, v in [("rol","invitado"),("usuario",None),("tema","oscuro")]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Temas ──────────────────────────────────────────────────────────────────────
TEMAS = {
    "oscuro": dict(
        acento="#D4A017", acento_hi="#FFD040", bg="#0A0A0A",
        bg_card="#141414", bg_alt="#101010", bg_sec="#1A1200",
        text="#F5F0E8", text2="#9A9080", text3="#5A5550",
        sbg="#050505", bfg="#050505",
        grad="linear-gradient(135deg,#0A0A0A,#1A1200)",
        ico="🟢", lbl="Tema Verde",
    ),
    "verde": dict(
        acento="#4CAF28", acento_hi="#7FD44A", bg="#0D1F0F",
        bg_card="#122516", bg_alt="#0F1E12", bg_sec="#0A1A08",
        text="#E8F5E0", text2="#8AB880", text3="#507848",
        sbg="#071208", bfg="#071208",
        grad="linear-gradient(135deg,#071208,#0D2010)",
        ico="🌙", lbl="Tema Oscuro",
    ),
}

def T():
    return TEMAS[st.session_state.tema]

def css():
    t = T()
    st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow:wght@400;600;700&display=swap');
html,body,[class*="css"]{{font-family:'Barlow',sans-serif;background:{t['bg']} !important;color:{t['text']} !important;}}
[data-testid="stAppViewContainer"]{{background:{t['bg']} !important;}}
[data-testid="stSidebar"]{{background:{t['sbg']} !important;border-right:1px solid {t['bg_card']};}}
[data-testid="stSidebar"] *{{color:{t['text2']} !important;}}
[data-testid="stSidebar"] h2{{color:{t['acento']} !important;font-size:1.3rem;}}
.stTabs [data-baseweb="tab-list"]{{background:{t['bg_card']};border-radius:8px;padding:4px;gap:4px;}}
.stTabs [data-baseweb="tab"]{{background:transparent;color:{t['text2']} !important;border-radius:6px;padding:8px 16px;font-weight:600;}}
.stTabs [aria-selected="true"]{{background:{t['acento']} !important;color:{t['bfg']} !important;}}
.stExpander{{background:{t['bg_card']} !important;border:1px solid {t['bg_alt']} !important;border-radius:8px !important;}}
.stExpander summary{{color:{t['acento']} !important;font-weight:700 !important;}}
.stSelectbox>div>div,.stTextInput>div>div>input,.stNumberInput>div>div>input{{
    background:{t['bg_alt']} !important;color:{t['text']} !important;
    border-color:{t['bg_card']} !important;border-radius:6px !important;}}
.stButton>button{{background:{t['acento']} !important;color:{t['bfg']} !important;
    font-weight:700 !important;border:none !important;border-radius:6px !important;padding:8px 20px !important;}}
.stButton>button:hover{{background:{t['acento_hi']} !important;}}
div[data-testid="stMarkdownContainer"] p{{color:{t['text']} !important;}}
</style>""", unsafe_allow_html=True)

css()

# ── Helpers visuales ───────────────────────────────────────────────────────────
def badge(estado):
    if estado == "Finalizado":
        return '<span style="background:#1A6020;color:#90FF90;padding:3px 12px;border-radius:20px;font-size:0.75rem;font-weight:700;white-space:nowrap;">✓ Finalizado</span>'
    if estado == "Pendiente":
        return f'<span style="background:{T()["bg_sec"]};color:{T()["acento"]};padding:3px 12px;border-radius:20px;font-size:0.75rem;font-weight:700;border:1px solid {T()["acento"]};white-space:nowrap;">⏳ Pendiente</span>'
    return '<span style="background:#3A0A0A;color:#FFB0B0;padding:3px 12px;border-radius:20px;font-size:0.75rem;font-weight:700;white-space:nowrap;">✗ Aplazado</span>'

def card_partido(enf, hora, estado, g1=0, g2=0):
    marcador = f'<span style="background:{T()["acento"]};color:{T()["bfg"]};padding:5px 14px;border-radius:6px;font-weight:700;font-family:monospace;">{g1} — {g2}</span>' if estado=="Finalizado" else ""
    return f"""<div style="background:{T()['bg_card']};border-left:4px solid {T()['acento']};
         border-radius:0 8px 8px 0;padding:12px 18px;margin-bottom:8px;
         display:flex;align-items:center;justify-content:space-between;">
  <div>
    <div style="font-weight:700;color:{T()['text']};font-size:0.95rem;margin-bottom:2px;">{enf}</div>
    <div style="color:{T()['text3']};font-size:0.8rem;">🕐 {hora}</div>
  </div>
  <div style="display:flex;align-items:center;gap:10px;">{marcador}{badge(estado)}</div>
</div>"""

def subtitulo(txt):
    return f'<div style="font-size:0.7rem;font-weight:700;letter-spacing:2px;color:{T()["text3"]};text-transform:uppercase;margin:16px 0 8px;">{txt}</div>'

def titulo_h2(txt):
    st.markdown(f'<h2 style="color:{T()["acento"]};margin-bottom:4px;">{txt}</h2>', unsafe_allow_html=True)

def titulo_h3(txt):
    st.markdown(f'<h3 style="color:{T()["text"]};margin-bottom:8px;">{txt}</h3>', unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚽ ITC Deportes")
    st.markdown("---")

    # Toggle tema — sin rerun, solo cambia estado y recarga naturalmente
    tema_nuevo = "verde" if st.session_state.tema == "oscuro" else "oscuro"
    if st.button(f"{T()['ico']} {T()['lbl']}", key="btn_tema"):
        st.session_state.tema = tema_nuevo
        st.rerun()

    st.markdown("---")

    if st.session_state.rol == "invitado":
        st.markdown("**👤 Modo Invitado**")
        with st.expander("🔐 Iniciar sesión"):
            user = st.text_input("Usuario", key="sb_user")
            pwd  = st.text_input("Contraseña", type="password", key="sb_pwd")
            if st.button("Entrar", key="btn_login"):
                if user in USUARIOS and USUARIOS[user] == pwd and USUARIOS_TIPO.get(user) == "profesor":
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
    torneo = st.radio("Torneo", ["🏆 Intercolegiados","🎯 Intercursos"], key="torneo_sel")

    if torneo == "🎯 Intercursos":
        st.markdown("**Categoría**")
        categoria = st.radio("cat", ["PRIMERA","SEGUNDA","TERCERA"],
                             label_visibility="collapsed", key="cat_sel")
        st.caption({"PRIMERA":"Grados 6° y 7°","SEGUNDA":"Grados 8° y 9°","TERCERA":"Grados 10° y 11°"}.get(categoria,""))
        st.markdown("**Deporte**")
        dep_raw = st.radio("dep", [f"{ICONOS_DEP.get(d,'🏅')} {d}" for d in DEPORTES],
                           label_visibility="collapsed", key="dep_sel")
        deporte = dep_raw.split(" ",1)[1] if " " in dep_raw else dep_raw
    else:
        categoria = None
        deporte   = None

# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown(f"""<div style="background:{T()['grad']};border-left:6px solid {T()['acento']};
     padding:26px 36px;margin-bottom:24px;border-radius:0 12px 12px 0;">
  <div style="font-family:'Bebas Neue',Impact,sans-serif;font-size:3rem;
              color:{T()['acento']};letter-spacing:5px;">ITC DEPORTES</div>
  <div style="color:{T()['text2']};font-size:0.9rem;margin-top:4px;">
    Sistema de gestión deportiva · 2026
  </div>
</div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  INTERCOLEGIADOS
# ═══════════════════════════════════════════════════════════════════════════════
if torneo == "🏆 Intercolegiados":
    titulo_h2("🏆 Intercolegiados ITC")
    tabs = st.tabs([f"{ICONOS_DEP[d]} {d}" for d in DEPORTES])

    for i, dep in enumerate(DEPORTES):
        with tabs[i]:
            c1, c2 = st.columns(2)

            # ── Logros ────────────────────────────────────────────────────────
            with c1:
                st.markdown(subtitulo("Logros destacados"), unsafe_allow_html=True)
                logros = [[lid,a,d] for lid,a,d in obtener_logros() if dep in d]
                if logros:
                    for lid, anio, desc in logros:
                        col_l, col_x = st.columns([10,1])
                        with col_l:
                            st.markdown(f"""<div style="display:flex;align-items:center;gap:12px;
                                 background:{T()['bg_card']};border-left:3px solid {T()['acento']};
                                 padding:10px 16px;margin-bottom:4px;border-radius:0 8px 8px 0;">
                              <span style="background:{T()['acento']};color:{T()['bfg']};padding:3px 10px;
                                    border-radius:20px;font-weight:700;font-size:0.85rem;">{anio}</span>
                              <span style="color:{T()['text']};font-size:0.9rem;">{desc}</span>
                            </div>""", unsafe_allow_html=True)
                        with col_x:
                            if st.session_state.rol == "profesor":
                                if st.button("✕", key=f"del_logro_{lid}", help="Eliminar logro"):
                                    eliminar_logro(lid)
                                    st.rerun()
                else:
                    st.info("Sin logros registrados.")

                if st.session_state.rol == "profesor":
                    with st.expander("➕ Añadir logro"):
                        anio_n = st.text_input("Año", key=f"logro_anio_{dep}")
                        desc_n = st.text_input("Descripción", key=f"logro_desc_{dep}")
                        if st.button("Guardar logro", key=f"logro_btn_{dep}"):
                            if anio_n and desc_n:
                                agregar_logro(anio_n, f"{dep} - {desc_n}")
                                st.success("✅ Logro añadido.")
                                st.rerun()

            # ── Partidos inter ────────────────────────────────────────────────
            with c2:
                st.markdown(subtitulo("Partidos programados"), unsafe_allow_html=True)
                partidos_i = obtener_partidos_inter(dep)
                if partidos_i:
                    for pid, fecha, enf, estado in partidos_i:
                        col_p, col_x = st.columns([10,1])
                        with col_p:
                            st.markdown(card_partido(enf, fecha, estado), unsafe_allow_html=True)
                        with col_x:
                            if st.session_state.rol == "profesor":
                                if st.button("✕", key=f"del_pi_{pid}", help="Eliminar partido"):
                                    eliminar_partido_inter(pid)
                                    st.rerun()
                else:
                    st.info("Sin partidos programados.")

                if st.session_state.rol == "profesor":
                    with st.expander("➕ Añadir partido"):
                        fecha_p  = st.text_input("Fecha (AAAA-MM-DD)", key=f"p_fecha_{dep}")
                        enf_p    = st.text_input("Enfrentamiento (ej: ITC vs Colegio X)", key=f"p_enf_{dep}")
                        estado_p = st.selectbox("Estado", ["Pendiente","Finalizado","Aplazado"], key=f"p_est_{dep}")
                        if st.button("Guardar partido", key=f"p_btn_{dep}"):
                            if fecha_p and enf_p:
                                agregar_partido_inter(dep, fecha_p, enf_p, estado_p)
                                st.success("✅ Partido añadido.")
                                st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
#  INTERCURSOS
# ═══════════════════════════════════════════════════════════════════════════════
else:
    titulo_h2(f"🎯 Intercursos — Categoría {categoria}")
    st.markdown(f'<p style="color:{T()["text3"]};margin-top:-12px;">{"Grados 6° y 7°" if categoria=="PRIMERA" else "Grados 8° y 9°" if categoria=="SEGUNDA" else "Grados 10° y 11°"}</p>', unsafe_allow_html=True)

    # ── Panel profesor ─────────────────────────────────────────────────────────
    if st.session_state.rol == "profesor":
        with st.expander("⚙️ Panel de Gestión — Profesor", expanded=False):
            ptabs = st.tabs(["➕ Equipo","👤 Jugador","✏️ Partido","🗑️ Eliminar","🎲 Sorteo"])

            # ── Añadir equipo ──────────────────────────────────────────────────
            with ptabs[0]:
                dep_ae = st.selectbox("Deporte", DEPORTES, key="ae_dep")
                cur_ae = st.selectbox("Curso", CATEGORIAS_LOCAL.get(categoria,[]), key="ae_cur")
                nom_ae = st.text_input("Nombre del equipo", key="ae_nom")
                if st.button("Añadir equipo", key="ae_btn"):
                    nom = nom_ae.strip()
                    if nom:
                        err = agregar_equipo(categoria, dep_ae, cur_ae, nom)
                        if err: st.error(err)
                        else:   st.success(f"✅ Equipo '{nom}' añadido.")
                    else: st.warning("Ingresa un nombre.")

            # ── Añadir jugador ─────────────────────────────────────────────────
            with ptabs[1]:
                dep_aj = st.selectbox("Deporte", DEPORTES, key="aj_dep")
                eqs_map = obtener_equipos(categoria, dep_aj)
                curs_aj = list(eqs_map.keys())
                if curs_aj:
                    cur_aj = st.selectbox("Curso", curs_aj, key="aj_cur")
                    eqs_aj = eqs_map.get(cur_aj, [])
                    if eqs_aj:
                        eq_aj  = st.selectbox("Equipo", eqs_aj, key="aj_eq")
                        nom_aj = st.text_input("Nombre del jugador", key="aj_nom")
                        if st.button("Añadir jugador", key="aj_btn"):
                            nom = nom_aj.strip()
                            if nom:
                                err = agregar_jugador(categoria, dep_aj, cur_aj, eq_aj, nom)
                                if err: st.error(err)
                                else:   st.success(f"✅ Jugador '{nom}' añadido.")
                            else: st.warning("Ingresa un nombre.")
                    else: st.info("No hay equipos en ese curso.")
                else: st.info("No hay equipos registrados.")

            # ── Actualizar partido ─────────────────────────────────────────────
            with ptabs[2]:
                dep_ap = st.selectbox("Deporte", DEPORTES, key="ap_dep")
                pl_dep = obtener_partidos(categoria, dep_ap)
                if pl_dep:
                    opts_p = [f"[{i+1}] {p[1][:10]} | {p[2][:45]} | {p[3]}" for i,p in enumerate(pl_dep)]
                    sel_p  = st.selectbox("Partido", opts_p, key="ap_sel")
                    idx_p  = opts_p.index(sel_p)
                    p_sel  = pl_dep[idx_p]
                    pid, fecha_p, enf_p, estado_p, g1_p, g2_p = p_sel
                    nuevo_est = st.selectbox("Estado", ["Pendiente","Finalizado"],
                                              index=0 if estado_p=="Pendiente" else 1, key="ap_est")
                    g1, g2 = int(g1_p), int(g2_p)
                    if nuevo_est == "Finalizado":
                        try:
                            partes = enf_p.split(" vs ")
                            eq1_n = partes[0].split("(")[0].strip()
                            eq2_n = partes[1].split("(")[0].strip()
                        except Exception:
                            eq1_n, eq2_n = "Equipo 1", "Equipo 2"
                        col1, col2 = st.columns(2)
                        g1 = col1.number_input(f"Goles {eq1_n[:20]}", min_value=0, value=g1, key="ap_g1")
                        g2 = col2.number_input(f"Goles {eq2_n[:20]}", min_value=0, value=g2, key="ap_g2")
                    if st.button("Guardar cambios", key="ap_btn"):
                        actualizar_partido(pid, nuevo_est, int(g1), int(g2))
                        st.success("✅ Partido actualizado.")
                        st.rerun()
                else:
                    st.info("No hay partidos. Realiza el sorteo primero.")

            # ── Eliminar equipo / jugador ──────────────────────────────────────
            with ptabs[3]:
                st.markdown("**Eliminar equipo**")
                dep_de = st.selectbox("Deporte", DEPORTES, key="de_dep")
                eqs_del_map = obtener_equipos(categoria, dep_de)
                curs_de = list(eqs_del_map.keys())
                if curs_de:
                    cur_de = st.selectbox("Curso", curs_de, key="de_cur")
                    eqs_de = eqs_del_map.get(cur_de, [])
                    if eqs_de:
                        eq_de = st.selectbox("Equipo a eliminar", eqs_de, key="de_eq")
                        st.warning(f"Esto eliminará '{eq_de}' y todos sus jugadores.")
                        if st.button("🗑️ Eliminar equipo", key="de_btn"):
                            eliminar_equipo(categoria, dep_de, cur_de, eq_de)
                            st.success(f"✅ Equipo '{eq_de}' eliminado.")
                            st.rerun()
                    else: st.info("No hay equipos en ese curso.")
                else: st.info("No hay equipos registrados.")

                st.markdown("---")
                st.markdown("**Eliminar jugador**")
                dep_dj = st.selectbox("Deporte", DEPORTES, key="dj_dep")
                eqs_dj_map = obtener_equipos(categoria, dep_dj)
                curs_dj = list(eqs_dj_map.keys())
                if curs_dj:
                    cur_dj = st.selectbox("Curso", curs_dj, key="dj_cur")
                    eqs_dj = eqs_dj_map.get(cur_dj, [])
                    if eqs_dj:
                        eq_dj  = st.selectbox("Equipo", eqs_dj, key="dj_eq")
                        jugs_dj = obtener_jugadores(categoria, dep_dj, cur_dj, eq_dj)
                        if jugs_dj:
                            nombres_dj = [j["nombre"] for j in jugs_dj]
                            ids_dj     = [j["id"] for j in jugs_dj]
                            nom_sel    = st.selectbox("Jugador a eliminar", nombres_dj, key="dj_nom")
                            jid = ids_dj[nombres_dj.index(nom_sel)]
                            if st.button("🗑️ Eliminar jugador", key="dj_btn"):
                                eliminar_jugador(jid)
                                st.success(f"✅ Jugador '{nom_sel}' eliminado.")
                                st.rerun()
                        else: st.info("No hay jugadores en ese equipo.")
                    else: st.info("No hay equipos en ese curso.")
                else: st.info("No hay equipos registrados.")

            # ── Sorteo ─────────────────────────────────────────────────────────
            with ptabs[4]:
                st.markdown("Genera el fixture **Round-Robin de 7 jornadas**.")
                dep_sort = st.selectbox("Deporte", DEPORTES, key="sort_dep")
                key_s    = f"{categoria}_{dep_sort}"
                sorteo   = obtener_sorteo(key_s)
                if sorteo:
                    st.info(f"✅ Sorteo existente: {sorteo['fecha'][:10]} · {sorteo['n_equipos']} equipos")
                    confirmar = st.checkbox("Quiero re-sortear (borra partidos pendientes)", key="sort_confirm")
                else:
                    confirmar = True
                if confirmar:
                    if st.button(f"🎲 Sortear — {dep_sort}", key="sort_btn"):
                        with st.spinner("Generando fixture..."):
                            ok, error = realizar_sorteo(categoria, dep_sort)
                        if error: st.error(error)
                        else:
                            s2 = obtener_sorteo(key_s)
                            n  = s2["n_equipos"] if s2 else "?"
                            st.success(f"✅ Sorteo listo. {n} equipos · 7 jornadas.")
                            st.rerun()

    st.markdown(f'<hr style="height:2px;background:linear-gradient(90deg,{T()["acento"]},transparent);border:none;margin:16px 0;">', unsafe_allow_html=True)

    # ── Vistas ─────────────────────────────────────────────────────────────────
    vista = st.tabs(["📊 Tabla","📅 Partidos","👥 Equipos"])

    # ── TABLA ──────────────────────────────────────────────────────────────────
    with vista[0]:
        titulo_h3(f"📊 {deporte} · {categoria}")
        tabla = calcular_tabla(categoria, deporte)
        if tabla:
            TH = f"background:{T()['acento']};color:{T()['bfg']};padding:10px 12px;text-align:center;font-size:0.78rem;font-weight:700;letter-spacing:1px;"
            TD = f"padding:10px 12px;border-bottom:1px solid {T()['bg_alt']};text-align:center;font-size:0.88rem;"
            MEDALLAS = {1:"🥇",2:"🥈",3:"🥉"}
            filas = ""
            for r in tabla:
                pos  = r["#"]
                med  = MEDALLAS.get(pos, str(pos))
                dg   = f"+{r['DG']}" if r['DG']>0 else str(r['DG'])
                dg_c = '#90FF90' if r['DG']>0 else '#FFB0B0' if r['DG']<0 else T()['text3']
                rbg  = T()['bg_card'] if pos%2==1 else T()['bg_alt']
                pbg  = T()['acento'] if pos==1 else '#606060' if pos==2 else '#8B5C1A' if pos==3 else rbg
                pfg  = T()['bfg'] if pos<=2 else '#F5F0E8' if pos==3 else T()['text3']
                eq_c = T()['acento'] if pos==1 else T()['text'] if pos<=3 else T()['text2']
                pts_c= T()['acento'] if pos<=3 else T()['text2']
                fw   = '700' if pos<=3 else '400'
                # Curso limpio — sin comillas
                curso_limpio = str(r['Curso']).strip().strip("'\"")
                filas += f"""<tr>
                  <td style="{TD}background:{pbg};color:{pfg};font-weight:700;font-size:1rem;">{med}</td>
                  <td style="{TD}background:{rbg};text-align:left;padding-left:14px;font-weight:{fw};color:{eq_c};">{r['Equipo']}</td>
                  <td style="{TD}background:{rbg};color:{T()['text3']};font-size:0.8rem;">{curso_limpio}</td>
                  <td style="{TD}background:{rbg};">{r['PJ']}</td>
                  <td style="{TD}background:{rbg};color:#90FF90;font-weight:600;">{r['PG']}</td>
                  <td style="{TD}background:{rbg};color:#FFE060;">{r['PE']}</td>
                  <td style="{TD}background:{rbg};color:#FFB0B0;">{r['PP']}</td>
                  <td style="{TD}background:{rbg};color:{T()['text2']};">{r['GF']}</td>
                  <td style="{TD}background:{rbg};color:{T()['text2']};">{r['GC']}</td>
                  <td style="{TD}background:{rbg};color:{dg_c};font-weight:600;">{dg}</td>
                  <td style="{TD}background:{rbg};color:{pts_c};font-weight:700;">{r['Pts']}</td>
                </tr>"""
            st.markdown(f"""<div style="border-radius:10px;overflow:hidden;border:1px solid {T()['bg_alt']};margin-top:8px;">
            <table style="width:100%;border-collapse:collapse;">
              <thead><tr>
                <th style="{TH}">#</th>
                <th style="{TH}text-align:left;padding-left:14px;">Equipo</th>
                <th style="{TH}">Curso</th><th style="{TH}">PJ</th><th style="{TH}">PG</th>
                <th style="{TH}">PE</th><th style="{TH}">PP</th><th style="{TH}">GF</th>
                <th style="{TH}">GC</th><th style="{TH}">DG</th><th style="{TH}">Pts</th>
              </tr></thead><tbody>{filas}</tbody>
            </table></div>
            <div style="margin-top:8px;color:{T()['text3']};font-size:0.8rem;">
              ⚽ Victoria = 3 pts &nbsp;&nbsp; 🤝 Empate = 1 pt &nbsp;&nbsp; ❌ Derrota = 0 pts
            </div>""", unsafe_allow_html=True)
        else:
            st.info("Sin datos. Realiza el sorteo para registrar los equipos automáticamente.")

    # ── PARTIDOS ───────────────────────────────────────────────────────────────
    with vista[1]:
        titulo_h3(f"📅 {deporte} · {categoria}")
        partidos = obtener_partidos(categoria, deporte)
        if partidos:
            fechas_dict = {}
            for p in partidos:
                fechas_dict.setdefault(p[1][:10], []).append(p)
            for j_idx, fch in enumerate(sorted(fechas_dict.keys())):
                st.markdown(f"""<div style="background:{T()['bg_sec']};border-left:4px solid {T()['acento']};
                     padding:8px 16px;margin:14px 0 6px;border-radius:0 6px 6px 0;
                     display:flex;align-items:center;gap:12px;">
                  <span style="background:{T()['acento']};color:{T()['bfg']};padding:2px 10px;
                        border-radius:20px;font-size:0.75rem;font-weight:700;">J{j_idx+1}</span>
                  <span style="color:{T()['acento']};font-weight:700;">JORNADA {j_idx+1}</span>
                  <span style="color:{T()['text3']};font-size:0.85rem;">📅 {fch}</span>
                </div>""", unsafe_allow_html=True)
                for pid, fecha, enf, estado, g1, g2 in fechas_dict[fch]:
                    st.markdown(card_partido(enf, fecha[11:16] or "15:00", estado, g1, g2), unsafe_allow_html=True)
        else:
            st.info("Sin partidos. Usa el Panel de Gestión → Sorteo para generar el fixture.")

    # ── EQUIPOS ────────────────────────────────────────────────────────────────
    with vista[2]:
        titulo_h3(f"👥 {deporte} · {categoria}")
        equipos_dep = obtener_equipos(categoria, deporte)
        if equipos_dep:
            cols = st.columns(2)
            for idx_col, (cur, eqs) in enumerate(sorted(equipos_dep.items())):
                if not eqs: continue
                with cols[idx_col % 2]:
                    # Encabezado del curso
                    st.markdown(f"""<div style="background:{T()['bg_card']};border-top:3px solid {T()['acento']};
                         border-radius:8px 8px 0 0;padding:10px 16px;">
                      <span style="font-size:0.7rem;font-weight:700;letter-spacing:2px;color:{T()['text3']};">CURSO {cur}</span>
                    </div>""", unsafe_allow_html=True)
                    for eq in eqs:
                        jugs = obtener_jugadores(categoria, deporte, cur, eq)
                        # Nombres limpios — sin HTML, solo texto plano
                        nombres_txt = ", ".join(j["nombre"] for j in jugs) if jugs else ""
                        st.markdown(f"""<div style="background:{T()['bg_card']};
                             border-left:1px solid {T()['bg_alt']};border-right:1px solid {T()['bg_alt']};
                             border-bottom:1px solid {T()['bg_alt']};padding:10px 16px;">
                          <div style="display:flex;align-items:center;gap:8px;">
                            <span style="font-size:1rem;">⚽</span>
                            <span style="font-weight:700;color:{T()['text']};font-size:0.95rem;">{eq}</span>
                            <span style="background:{T()['acento']};color:{T()['bfg']};padding:1px 8px;
                                  border-radius:20px;font-size:0.7rem;font-weight:700;">{len(jugs)} jug.</span>
                          </div>
                          {f'<div style="color:{T()["text3"]};font-size:0.78rem;margin-top:4px;padding-left:24px;">{nombres_txt}</div>' if nombres_txt else ''}
                        </div>""", unsafe_allow_html=True)
                    st.markdown(f'<div style="background:{T()["bg_card"]};border-radius:0 0 8px 8px;height:8px;border:1px solid {T()["bg_alt"]};border-top:none;margin-bottom:12px;"></div>', unsafe_allow_html=True)
        else:
            st.info("Sin equipos. Añade desde el Panel de Gestión o realiza el sorteo.")
