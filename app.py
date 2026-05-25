import streamlit as st
from data import (
    ICONOS_DEP, DEPORTES, CATEGORIAS_LOCAL, USUARIOS, USUARIOS_TIPO,
    obtener_equipos, agregar_equipo, eliminar_equipo, limpiar_equipos_corruptos,
    obtener_jugadores, agregar_jugador, eliminar_jugador,
    obtener_partidos, actualizar_partido,
    obtener_logros, agregar_logro, eliminar_logro,
    obtener_partidos_inter, agregar_partido_inter, eliminar_partido_inter,
    obtener_sorteo, realizar_sorteo, eliminar_sorteo, calcular_tabla,
    enf_limpio,
)

st.set_page_config(page_title="ITC Deportes", page_icon="⚽", layout="wide")

# ── Session state ──────────────────────────────────────────────────────────────
DEFAULTS = {
    "rol": "invitado",
    "usuario": None,
    "tema": "oscuro",
    "pagina": "inicio",       # inicio / intercolegiados / intercursos
    "categoria": "PRIMERA",
    "deporte": "Balonmano",
    "vista_ic": "tabla",      # tabla / partidos / equipos
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Temas ──────────────────────────────────────────────────────────────────────
TEMAS = {
    "oscuro": dict(
        ac="#D4A017", achi="#FFD040", bg="#0A0A0A",
        bgc="#141414", bga="#101010", bgs="#1A1200",
        tx="#F5F0E8", tx2="#9A9080", tx3="#5A5550",
        sbg="#050505", bfg="#050505",
        grad="linear-gradient(135deg,#0A0A0A,#1A1200)",
        nav="#0D0D0D", nav_border="#222",
    ),
    "verde": dict(
        ac="#4CAF28", achi="#7FD44A", bg="#0D1F0F",
        bgc="#122516", bga="#0F1E12", bgs="#0A1A08",
        tx="#E8F5E0", tx2="#8AB880", tx3="#507848",
        sbg="#071208", bfg="#071208",
        grad="linear-gradient(135deg,#071208,#0D2010)",
        nav="#071208", nav_border="#1A3A1E",
    ),
}
def T(): return TEMAS[st.session_state.tema]

# ── CSS global + mobile ────────────────────────────────────────────────────────
def css():
    t = T()
    st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow:wght@400;600;700&display=swap');

html,body,[class*="css"]{{
    font-family:'Barlow',sans-serif;
    background:{t['bg']} !important;
    color:{t['tx']} !important;
}}
[data-testid="stAppViewContainer"]{{background:{t['bg']} !important;}}
[data-testid="stSidebar"]{{display:none !important;}}
[data-testid="collapsedControl"]{{display:none !important;}}

/* Quitar padding excesivo */
.block-container{{padding:1rem 1rem 5rem 1rem !important;max-width:100% !important;}}

/* Tabs */
.stTabs [data-baseweb="tab-list"]{{
    background:{t['bgc']};border-radius:8px;
    padding:4px;gap:2px;overflow-x:auto;
    -webkit-overflow-scrolling:touch;
}}
.stTabs [data-baseweb="tab"]{{
    background:transparent;color:{t['tx2']} !important;
    border-radius:6px;padding:8px 14px;
    font-weight:600;white-space:nowrap;font-size:0.85rem;
}}
.stTabs [aria-selected="true"]{{
    background:{t['ac']} !important;color:{t['bfg']} !important;
}}

/* Expander */
.stExpander{{
    background:{t['bgc']} !important;
    border:1px solid {t['bga']} !important;
    border-radius:8px !important;
}}
.stExpander summary{{color:{t['ac']} !important;font-weight:700 !important;}}

/* Inputs */
.stSelectbox>div>div,
.stTextInput>div>div>input,
.stNumberInput>div>div>input{{
    background:{t['bga']} !important;color:{t['tx']} !important;
    border-color:{t['bgc']} !important;border-radius:8px !important;
    font-size:1rem !important;min-height:44px !important;
}}

/* Botones */
.stButton>button{{
    background:{t['ac']} !important;color:{t['bfg']} !important;
    font-weight:700 !important;border:none !important;
    border-radius:8px !important;padding:12px 20px !important;
    width:100% !important;font-size:1rem !important;
    min-height:48px !important;
}}
.stButton>button:hover{{background:{t['achi']} !important;}}

/* Texto */
div[data-testid="stMarkdownContainer"] p{{color:{t['tx']} !important;}}
h1,h2,h3{{word-break:break-word;}}

/* Tabla scroll */
.tabla-wrap{{overflow-x:auto;-webkit-overflow-scrolling:touch;border-radius:10px;}}
.tabla-wrap table{{min-width:520px;width:100%;border-collapse:collapse;}}

/* Radio */
.stRadio>div{{gap:8px !important;}}
.stRadio label{{
    background:{t['bgc']} !important;
    border:1px solid {t['bga']} !important;
    border-radius:8px !important;
    padding:10px 16px !important;
    cursor:pointer;
    transition:all 0.15s;
}}

/* Barra de navegación inferior fija */
.nav-bar{{
    position:fixed;bottom:0;left:0;right:0;
    background:{t['nav']};
    border-top:1px solid {t['nav_border']};
    display:flex;z-index:1000;
    padding:6px 0 env(safe-area-inset-bottom, 6px);
}}
.nav-item{{
    flex:1;display:flex;flex-direction:column;
    align-items:center;justify-content:center;
    padding:6px 4px;cursor:pointer;
    font-size:0.65rem;color:{t['tx3']};
    font-weight:600;letter-spacing:0.5px;
    text-transform:uppercase;gap:3px;
    border:none;background:transparent;
    text-decoration:none;
}}
.nav-item.active{{color:{t['ac']};}}
.nav-ico{{font-size:1.4rem;line-height:1;}}

/* Chips de selección */
.chip-row{{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0;}}
.chip{{
    padding:6px 14px;border-radius:20px;
    font-size:0.82rem;font-weight:700;cursor:pointer;
    border:2px solid {t['bga']};background:{t['bgc']};
    color:{t['tx2']};transition:all 0.15s;
}}
.chip.sel{{
    background:{t['ac']};color:{t['bfg']};
    border-color:{t['ac']};
}}

@media (max-width:768px){{
    .block-container{{padding:0.8rem 0.6rem 5rem !important;}}
    h2{{font-size:1.3rem !important;}}
    h3{{font-size:1.1rem !important;}}
    .stTabs [data-baseweb="tab"]{{padding:7px 10px !important;font-size:0.78rem !important;}}
}}
</style>""", unsafe_allow_html=True)
css()

# ── Helpers ────────────────────────────────────────────────────────────────────
def T(): return TEMAS[st.session_state.tema]

def badge(estado):
    if estado == "Finalizado":
        return '<span style="background:#1A6020;color:#90FF90;padding:4px 12px;border-radius:20px;font-size:0.78rem;font-weight:700;white-space:nowrap;">✓ Finalizado</span>'
    if estado == "Pendiente":
        return f'<span style="background:{T()["bgs"]};color:{T()["ac"]};padding:4px 12px;border-radius:20px;font-size:0.78rem;font-weight:700;border:1px solid {T()["ac"]};white-space:nowrap;">⏳ Pendiente</span>'
    return '<span style="background:#3A0A0A;color:#FFB0B0;padding:4px 12px;border-radius:20px;font-size:0.78rem;font-weight:700;white-space:nowrap;">✗ Aplazado</span>'

def card_partido(enf, hora, estado, g1=0, g2=0):
    m = f'<div style="background:{T()["ac"]};color:{T()["bfg"]};padding:6px 16px;border-radius:6px;font-weight:700;font-family:monospace;font-size:1.1rem;text-align:center;">{g1} — {g2}</div>' if estado=="Finalizado" else ""
    return f"""<div style="background:{T()['bgc']};border-left:4px solid {T()['ac']};
         border-radius:0 8px 8px 0;padding:14px 16px;margin-bottom:10px;">
  <div style="font-weight:700;color:{T()['tx']};font-size:0.95rem;margin-bottom:6px;line-height:1.3;">{enf}</div>
  <div style="display:flex;flex-wrap:wrap;align-items:center;gap:8px;justify-content:space-between;">
    <div style="color:{T()['tx3']};font-size:0.8rem;">🕐 {hora}</div>
    <div style="display:flex;gap:8px;align-items:center;">{m}{badge(estado)}</div>
  </div>
</div>"""

def lbl_sec(txt):
    return f'<div style="font-size:0.7rem;font-weight:700;letter-spacing:2px;color:{T()["tx3"]};text-transform:uppercase;margin:16px 0 10px;">{txt}</div>'

def dep_badge(dep):
    return f'<span style="background:{T()["ac"]};color:{T()["bfg"]};padding:4px 14px;border-radius:20px;font-weight:700;font-size:0.85rem;">{ICONOS_DEP.get(dep,"🏅")} {dep}</span>'

def seccion_header(titulo, subtitulo=""):
    sub = f'<div style="color:{T()["tx3"]};font-size:0.85rem;margin-top:2px;">{subtitulo}</div>' if subtitulo else ""
    st.markdown(f"""<div style="margin-bottom:16px;">
      <h2 style="color:{T()['ac']};margin:0;font-size:1.5rem;">{titulo}</h2>
      {sub}
    </div>""", unsafe_allow_html=True)

def render_tabla(categoria, deporte):
    tabla = calcular_tabla(categoria, deporte)
    if not tabla:
        st.info("Sin datos. Añade equipos y realiza el sorteo.")
        return
    TH = f"background:{T()['ac']};color:{T()['bfg']};padding:10px 10px;text-align:center;font-size:0.75rem;font-weight:700;white-space:nowrap;"
    TD = f"padding:9px 10px;border-bottom:1px solid {T()['bga']};text-align:center;font-size:0.85rem;white-space:nowrap;"
    MEDALLAS = {1:"🥇",2:"🥈",3:"🥉"}
    filas = ""
    for r in tabla:
        pos   = r["#"]
        med   = MEDALLAS.get(pos, str(pos))
        dg    = f"+{r['DG']}" if r['DG']>0 else str(r['DG'])
        dg_c  = '#90FF90' if r['DG']>0 else '#FFB0B0' if r['DG']<0 else T()['tx3']
        rbg   = T()['bgc'] if pos%2==1 else T()['bga']
        pbg   = T()['ac'] if pos==1 else '#606060' if pos==2 else '#8B5C1A' if pos==3 else rbg
        pfg   = T()['bfg'] if pos<=2 else '#F5F0E8' if pos==3 else T()['tx3']
        eq_c  = T()['ac'] if pos==1 else T()['tx'] if pos<=3 else T()['tx2']
        pts_c = T()['ac'] if pos<=3 else T()['tx2']
        fw    = '700' if pos<=3 else '400'
        filas += f"""<tr>
          <td style="{TD}background:{pbg};color:{pfg};font-weight:700;">{med}</td>
          <td style="{TD}background:{rbg};text-align:left;padding-left:12px;font-weight:{fw};color:{eq_c};max-width:140px;overflow:hidden;text-overflow:ellipsis;">{r['Equipo']}</td>
          <td style="{TD}background:{rbg};color:{T()['tx3']};font-size:0.75rem;">{r['Curso']}</td>
          <td style="{TD}background:{rbg};">{r['PJ']}</td>
          <td style="{TD}background:{rbg};color:#90FF90;font-weight:600;">{r['PG']}</td>
          <td style="{TD}background:{rbg};color:#FFE060;">{r['PE']}</td>
          <td style="{TD}background:{rbg};color:#FFB0B0;">{r['PP']}</td>
          <td style="{TD}background:{rbg};color:{dg_c};font-weight:600;">{dg}</td>
          <td style="{TD}background:{rbg};color:{pts_c};font-weight:700;font-size:1rem;">{r['Pts']}</td>
        </tr>"""
    st.markdown(f"""<div class="tabla-wrap">
    <table>
      <thead><tr>
        <th style="{TH}">#</th>
        <th style="{TH}text-align:left;padding-left:12px;">Equipo</th>
        <th style="{TH}">Curso</th>
        <th style="{TH}">PJ</th><th style="{TH}">PG</th><th style="{TH}">PE</th>
        <th style="{TH}">PP</th><th style="{TH}">DG</th><th style="{TH}">Pts</th>
      </tr></thead><tbody>{filas}</tbody>
    </table></div>
    <div style="margin-top:8px;color:{T()['tx3']};font-size:0.78rem;">
      ⚽ Victoria=3pts &nbsp; 🤝 Empate=1pt &nbsp; ❌ Derrota=0pts
    </div>""", unsafe_allow_html=True)

# ── Barra de navegación inferior ──────────────────────────────────────────────
def nav_bar():
    p = st.session_state.pagina
    tema_ico = "🌙" if st.session_state.tema == "oscuro" else "🟢"
    st.markdown(f"""
    <div class="nav-bar">
      <button class="nav-item {'active' if p=='inicio' else ''}"
        onclick="window.parent.postMessage({{type:'streamlit:setComponentValue',value:'inicio'}}, '*')">
        <span class="nav-ico">🏠</span>Inicio
      </button>
      <button class="nav-item {'active' if p=='intercolegiados' else ''}"
        onclick="window.parent.postMessage({{type:'streamlit:setComponentValue',value:'inter'}}, '*')">
        <span class="nav-ico">🏆</span>Copas
      </button>
      <button class="nav-item {'active' if p=='intercursos' else ''}"
        onclick="window.parent.postMessage({{type:'streamlit:setComponentValue',value:'liga'}}, '*')">
        <span class="nav-ico">🎯</span>Liga
      </button>
      <button class="nav-item"
        onclick="window.parent.postMessage({{type:'streamlit:setComponentValue',value:'tema'}}, '*')">
        <span class="nav-ico">{tema_ico}</span>Tema
      </button>
    </div>
    """, unsafe_allow_html=True)

# ── Navegación con botones reales de Streamlit ─────────────────────────────────
# Barra superior de navegación (funcional con Streamlit)
t = T()
col_logo, col_nav, col_user = st.columns([2, 5, 2])

with col_logo:
    st.markdown(f"""<div style="font-family:'Bebas Neue',Impact;font-size:1.6rem;
        color:{t['ac']};letter-spacing:3px;padding-top:4px;">⚽ ITC</div>""",
        unsafe_allow_html=True)

with col_nav:
    nav_cols = st.columns(3)
    pages = [("🏠 Inicio","inicio"), ("🏆 Intercolegiados","intercolegiados"), ("🎯 Intercursos","intercursos")]
    for i, (label, key) in enumerate(pages):
        with nav_cols[i]:
            is_active = st.session_state.pagina == key
            bg = t['ac'] if is_active else t['bgc']
            fg = t['bfg'] if is_active else t['tx2']
            if st.button(label, key=f"nav_{key}",
                         help=f"Ir a {label}"):
                st.session_state.pagina = key
                st.rerun()

with col_user:
    if st.session_state.rol == "profesor":
        st.markdown(f"""<div style="text-align:right;padding-top:4px;">
            <span style="background:{t['ac']};color:{t['bfg']};padding:4px 10px;
            border-radius:20px;font-size:0.75rem;font-weight:700;">
            ★ {st.session_state.usuario.upper()}</span></div>""",
            unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="text-align:right;padding-top:8px;color:{t["tx3"]};font-size:0.8rem;">👤 Invitado</div>',
                    unsafe_allow_html=True)

st.markdown(f'<hr style="height:2px;background:linear-gradient(90deg,{t["ac"]},transparent);border:none;margin:8px 0 16px;">', unsafe_allow_html=True)

pagina = st.session_state.pagina

# ═══════════════════════════════════════════════════════════════════════════════
#  PÁGINA: INICIO
# ═══════════════════════════════════════════════════════════════════════════════
if pagina == "inicio":
    # Hero
    st.markdown(f"""<div style="background:{t['grad']};border-left:6px solid {t['ac']};
         padding:20px 20px;margin-bottom:20px;border-radius:0 12px 12px 0;">
      <div style="font-family:'Bebas Neue',Impact;font-size:2.4rem;
                  color:{t['ac']};letter-spacing:4px;line-height:1.1;">ITC DEPORTES</div>
      <div style="color:{t['tx2']};font-size:0.85rem;margin-top:4px;">
        Sistema de gestión deportiva · 2026
      </div>
    </div>""", unsafe_allow_html=True)

    # Login / Logout
    if st.session_state.rol == "invitado":
        with st.expander("🔐 Iniciar sesión como Profesor"):
            user = st.text_input("Usuario", key="login_user")
            pwd  = st.text_input("Contraseña", type="password", key="login_pwd")
            if st.button("Entrar", key="login_btn"):
                if user in USUARIOS and USUARIOS[user] == pwd and USUARIOS_TIPO.get(user) == "profesor":
                    st.session_state.rol = "profesor"
                    st.session_state.usuario = user
                    st.success(f"¡Bienvenido {user}!")
                else:
                    st.error("Usuario o contraseña incorrectos.")
    else:
        col1, col2 = st.columns([3,1])
        with col1:
            st.markdown(f"""<div style="background:{t['bgc']};border-left:4px solid {t['ac']};
                 padding:12px 16px;border-radius:0 8px 8px 0;">
              <div style="font-weight:700;color:{t['ac']};">★ Sesión activa: {st.session_state.usuario.upper()}</div>
              <div style="color:{t['tx3']};font-size:0.82rem;">Modo Profesor</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            if st.button("Salir", key="logout_btn"):
                st.session_state.rol = "invitado"
                st.session_state.usuario = None
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Cards de acceso rápido
    st.markdown(f"<div style='font-size:0.7rem;font-weight:700;letter-spacing:2px;color:{t['tx3']};text-transform:uppercase;margin-bottom:12px;'>Acceso rápido</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""<div style="background:{t['bgc']};border-top:3px solid {t['ac']};
             border-radius:8px;padding:16px;text-align:center;margin-bottom:10px;">
          <div style="font-size:2rem;">🏆</div>
          <div style="font-weight:700;color:{t['tx']};margin-top:6px;">Intercolegiados</div>
          <div style="color:{t['tx3']};font-size:0.8rem;">Logros y partidos</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Ver Intercolegiados", key="quick_inter"):
            st.session_state.pagina = "intercolegiados"
            st.rerun()
    with c2:
        st.markdown(f"""<div style="background:{t['bgc']};border-top:3px solid {t['ac']};
             border-radius:8px;padding:16px;text-align:center;margin-bottom:10px;">
          <div style="font-size:2rem;">🎯</div>
          <div style="font-weight:700;color:{t['tx']};margin-top:6px;">Intercursos</div>
          <div style="color:{t['tx3']};font-size:0.8rem;">Tabla y resultados</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Ver Intercursos", key="quick_liga"):
            st.session_state.pagina = "intercursos"
            st.rerun()

    # Tema
    st.markdown("<br>", unsafe_allow_html=True)
    tema_lbl = "🌙 Cambiar a Tema Verde" if st.session_state.tema == "oscuro" else "🌟 Cambiar a Tema Oscuro"
    if st.button(tema_lbl, key="tema_inicio"):
        st.session_state.tema = "verde" if st.session_state.tema == "oscuro" else "oscuro"
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
#  PÁGINA: INTERCOLEGIADOS
# ═══════════════════════════════════════════════════════════════════════════════
elif pagina == "intercolegiados":
    seccion_header("🏆 Intercolegiados ITC", "Partidos y logros del colegio")

    tabs = st.tabs([f"{ICONOS_DEP[d]} {d}" for d in DEPORTES])
    for i, dep in enumerate(DEPORTES):
        with tabs[i]:
            # Logros
            st.markdown(lbl_sec("🏅 Logros"), unsafe_allow_html=True)
            logros = [[lid,a,d] for lid,a,d in obtener_logros() if dep in d]
            if logros:
                for lid, anio, desc in logros:
                    col_l, col_x = st.columns([10, 1])
                    with col_l:
                        st.markdown(f"""<div style="display:flex;align-items:center;gap:10px;
                             background:{t['bgc']};border-left:3px solid {t['ac']};
                             padding:10px 14px;margin-bottom:6px;border-radius:0 8px 8px 0;">
                          <span style="background:{t['ac']};color:{t['bfg']};padding:3px 10px;
                                border-radius:20px;font-weight:700;font-size:0.82rem;white-space:nowrap;">{anio}</span>
                          <span style="color:{t['tx']};font-size:0.88rem;">{desc}</span>
                        </div>""", unsafe_allow_html=True)
                    with col_x:
                        if st.session_state.rol == "profesor":
                            if st.button("✕", key=f"xl_{lid}"):
                                eliminar_logro(lid); st.rerun()
            else:
                st.info("Sin logros registrados.")

            if st.session_state.rol == "profesor":
                with st.expander("➕ Añadir logro"):
                    a_n = st.text_input("Año", key=f"la_{dep}")
                    d_n = st.text_input("Descripción", key=f"ld_{dep}")
                    if st.button("Guardar logro", key=f"lb_{dep}"):
                        if a_n and d_n:
                            agregar_logro(a_n, f"{dep} - {d_n}")
                            st.success("✅ Logro añadido."); st.rerun()

            st.markdown(f'<hr style="border:none;border-top:1px solid {t["bga"]};margin:16px 0;">', unsafe_allow_html=True)

            # Partidos
            st.markdown(lbl_sec("📅 Partidos"), unsafe_allow_html=True)
            partidos_i = obtener_partidos_inter(dep)
            if partidos_i:
                for pid, fecha, enf, estado in partidos_i:
                    col_p, col_x = st.columns([10, 1])
                    with col_p:
                        st.markdown(card_partido(enf, fecha, estado), unsafe_allow_html=True)
                    with col_x:
                        if st.session_state.rol == "profesor":
                            if st.button("✕", key=f"xpi_{pid}"):
                                eliminar_partido_inter(pid); st.rerun()
            else:
                st.info("Sin partidos programados.")

            if st.session_state.rol == "profesor":
                with st.expander("➕ Añadir partido"):
                    f_p = st.text_input("Fecha (AAAA-MM-DD)", key=f"pf_{dep}")
                    e_p = st.text_input("Enfrentamiento", key=f"pe_{dep}")
                    s_p = st.selectbox("Estado", ["Pendiente","Finalizado","Aplazado"], key=f"ps_{dep}")
                    if st.button("Guardar partido", key=f"pb_{dep}"):
                        if f_p and e_p:
                            agregar_partido_inter(dep, f_p, e_p, s_p)
                            st.success("✅ Partido añadido."); st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
#  PÁGINA: INTERCURSOS
# ═══════════════════════════════════════════════════════════════════════════════
elif pagina == "intercursos":
    # ── Selector de categoría y deporte ───────────────────────────────────────
    cat_actual = st.session_state.categoria
    dep_actual = st.session_state.deporte

    with st.expander(f"📂 {cat_actual} · {ICONOS_DEP.get(dep_actual,'')} {dep_actual}  —  Cambiar", expanded=False):
        st.markdown("**Categoría**")
        cat_cols = st.columns(3)
        cats = {"PRIMERA":"6° y 7°","SEGUNDA":"8° y 9°","TERCERA":"10° y 11°"}
        for i, (cat, grados) in enumerate(cats.items()):
            with cat_cols[i]:
                sel = cat_actual == cat
                bg  = t['ac'] if sel else t['bgc']
                fg  = t['bfg'] if sel else t['tx2']
                st.markdown(f"""<div style="background:{bg};color:{fg};padding:10px;
                     border-radius:8px;text-align:center;font-weight:700;
                     font-size:0.85rem;margin-bottom:4px;">{cat}<br>
                     <span style="font-size:0.72rem;font-weight:400;">{grados}</span></div>""",
                    unsafe_allow_html=True)
                if st.button(f"{'✓ ' if sel else ''}{cat}", key=f"sel_cat_{cat}"):
                    st.session_state.categoria = cat
                    st.rerun()

        st.markdown("**Deporte**")
        dep_cols = st.columns(2)
        for i, dep in enumerate(DEPORTES):
            with dep_cols[i % 2]:
                sel = dep_actual == dep
                bg  = t['ac'] if sel else t['bgc']
                fg  = t['bfg'] if sel else t['tx2']
                ico = ICONOS_DEP.get(dep,'🏅')
                if st.button(f"{ico} {dep}", key=f"sel_dep_{dep}"):
                    st.session_state.deporte = dep
                    st.rerun()

    categoria = st.session_state.categoria
    deporte   = st.session_state.deporte

    seccion_header(
        f"🎯 {ICONOS_DEP.get(deporte,'')} {deporte}",
        f"Categoría {categoria} · {'Grados 6° y 7°' if categoria=='PRIMERA' else 'Grados 8° y 9°' if categoria=='SEGUNDA' else 'Grados 10° y 11°'}"
    )

    # ── Panel profesor ─────────────────────────────────────────────────────────
    if st.session_state.rol == "profesor":
        with st.expander("⚙️ Panel de Gestión — Profesor", expanded=False):
            ptabs = st.tabs(["➕ Equipo","👤 Jugador","✏️ Partido","🎲 Sorteo"])

            with ptabs[0]:
                st.markdown(f"Deporte: {dep_badge(deporte)}", unsafe_allow_html=True)
                st.markdown("---")
                st.markdown("**Añadir equipo**")
                cur_ae = st.selectbox("Curso", CATEGORIAS_LOCAL.get(categoria,[]), key="ae_cur")
                nom_ae = st.text_input("Nombre del equipo", key="ae_nom")
                if st.button("Añadir equipo", key="ae_btn"):
                    nom = nom_ae.strip()
                    if nom:
                        err = agregar_equipo(categoria, deporte, cur_ae, nom)
                        if err: st.error(err)
                        else:   st.success(f"✅ '{nom}' añadido al curso {cur_ae}."); st.rerun()
                    else: st.warning("Ingresa un nombre.")
                st.markdown("---")
                st.markdown("**Eliminar equipo**")
                eqs_de = obtener_equipos(categoria, deporte)
                curs_de = list(eqs_de.keys())
                if curs_de:
                    cur_de = st.selectbox("Curso", curs_de, key="de_cur")
                    lista_de = eqs_de.get(cur_de, [])
                    if lista_de:
                        eq_de = st.selectbox("Equipo", lista_de, key="de_eq")
                        st.warning(f"⚠️ Eliminará '{eq_de}' y sus jugadores.")
                        if st.button("🗑️ Eliminar equipo", key="de_btn"):
                            eliminar_equipo(categoria, deporte, cur_de, eq_de)
                            st.success(f"✅ '{eq_de}' eliminado."); st.rerun()
                else: st.info("No hay equipos registrados.")

            with ptabs[1]:
                st.markdown(f"Deporte: {dep_badge(deporte)}", unsafe_allow_html=True)
                st.markdown("---")
                st.markdown("**Añadir jugador**")
                eqs_aj = obtener_equipos(categoria, deporte)
                curs_aj = list(eqs_aj.keys())
                if curs_aj:
                    cur_aj = st.selectbox("Curso", curs_aj, key="aj_cur")
                    lista_aj = eqs_aj.get(cur_aj, [])
                    if lista_aj:
                        eq_aj  = st.selectbox("Equipo", lista_aj, key="aj_eq")
                        nom_aj = st.text_input("Nombre del jugador", key="aj_nom")
                        if st.button("Añadir jugador", key="aj_btn"):
                            nom = nom_aj.strip()
                            if nom:
                                err = agregar_jugador(categoria, deporte, cur_aj, eq_aj, nom)
                                if err: st.error(err)
                                else:   st.success(f"✅ '{nom}' añadido."); st.rerun()
                    else: st.info("No hay equipos en ese curso.")
                else: st.info("No hay equipos registrados.")
                st.markdown("---")
                st.markdown("**Eliminar jugador**")
                eqs_dj = obtener_equipos(categoria, deporte)
                curs_dj = list(eqs_dj.keys())
                if curs_dj:
                    cur_dj = st.selectbox("Curso", curs_dj, key="dj_cur")
                    lista_dj = eqs_dj.get(cur_dj, [])
                    if lista_dj:
                        eq_dj   = st.selectbox("Equipo", lista_dj, key="dj_eq")
                        jugs_dj = obtener_jugadores(categoria, deporte, cur_dj, eq_dj)
                        if jugs_dj:
                            noms_dj = [j["nombre"] for j in jugs_dj]
                            ids_dj  = [j["id"] for j in jugs_dj]
                            nom_sel = st.selectbox("Jugador", noms_dj, key="dj_nom")
                            jid     = ids_dj[noms_dj.index(nom_sel)]
                            if st.button("🗑️ Eliminar jugador", key="dj_btn"):
                                eliminar_jugador(jid)
                                st.success(f"✅ '{nom_sel}' eliminado."); st.rerun()
                        else: st.info("No hay jugadores.")
                else: st.info("No hay equipos registrados.")

            with ptabs[2]:
                st.markdown(f"Deporte: {dep_badge(deporte)}", unsafe_allow_html=True)
                st.markdown("---")
                pl_dep = obtener_partidos(categoria, deporte)
                if pl_dep:
                    def opt_p(i, p):
                        ico = "✓" if p[3]=="Finalizado" else "⏳"
                        return f"{ico} J{i+1} · {p[1][:10]} | {enf_limpio(p[2])}"
                    opts_p = [opt_p(i, p) for i, p in enumerate(pl_dep)]
                    sel_p  = st.selectbox("Selecciona partido", opts_p, key="ap_sel")
                    idx_p  = opts_p.index(sel_p)
                    p_sel  = pl_dep[idx_p]
                    pid, fecha_p, enf_p, estado_p, g1_p, g2_p = p_sel
                    enf_show = enf_limpio(enf_p)

                    st.markdown(f"""<div style="background:{t['bgs']};border-left:4px solid {t['ac']};
                         padding:14px 16px;border-radius:0 8px 8px 0;margin:10px 0;">
                      <div style="font-weight:700;color:{t['tx']};font-size:0.95rem;">{enf_show}</div>
                      <div style="color:{t['tx3']};font-size:0.8rem;margin-top:4px;">
                        📅 {fecha_p[:10]} · Estado: <b style="color:{t['ac']}">{estado_p}</b>
                      </div>
                    </div>""", unsafe_allow_html=True)

                    nuevo_est = st.selectbox("Nuevo estado", ["Pendiente","Finalizado"],
                                              index=0 if estado_p=="Pendiente" else 1, key="ap_est")
                    g1, g2 = 0, 0
                    if nuevo_est == "Finalizado":
                        try:
                            partes = enf_show.split(" vs ")
                            eq1_n  = partes[0].split("(")[0].strip()
                            eq2_n  = partes[1].split("(")[0].strip()
                        except Exception:
                            eq1_n, eq2_n = "Equipo 1", "Equipo 2"
                        col1, col_vs, col2 = st.columns([5,1,5])
                        with col1:
                            st.markdown(f"<div style='background:{t['bgc']};padding:8px;border-radius:6px 6px 0 0;font-weight:700;color:{t['ac']};text-align:center;font-size:0.85rem;'>{eq1_n[:20]}</div>", unsafe_allow_html=True)
                            g1 = st.number_input("g1", min_value=0, value=0, key="ap_g1", label_visibility="collapsed")
                        with col_vs:
                            st.markdown(f"<div style='text-align:center;padding-top:32px;color:{t['tx3']};font-weight:700;'>—</div>", unsafe_allow_html=True)
                        with col2:
                            st.markdown(f"<div style='background:{t['bgc']};padding:8px;border-radius:6px 6px 0 0;font-weight:700;color:{t['ac']};text-align:center;font-size:0.85rem;'>{eq2_n[:20]}</div>", unsafe_allow_html=True)
                            g2 = st.number_input("g2", min_value=0, value=0, key="ap_g2", label_visibility="collapsed")

                    if st.button("💾 Guardar resultado", key="ap_btn"):
                        actualizar_partido(pid, nuevo_est, int(g1), int(g2))
                        res = f" ({int(g1)}–{int(g2)})" if nuevo_est=="Finalizado" else ""
                        st.success(f"✅ {enf_show} → {nuevo_est}{res}")
                        st.rerun()
                else:
                    st.info("No hay partidos. Realiza el sorteo primero.")

            with ptabs[3]:
                st.markdown(f"Deporte: {dep_badge(deporte)}", unsafe_allow_html=True)
                st.markdown("---")
                key_s  = f"{categoria}_{deporte}"
                sorteo = obtener_sorteo(key_s)
                if sorteo:
                    st.info(f"✅ Sorteo activo: {sorteo['fecha'][:10]} · {sorteo['n_equipos']} equipos")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("🔄 Re-sortear", key="sort_btn"):
                            with st.spinner("Generando..."):
                                ok, err = realizar_sorteo(categoria, deporte)
                            if err: st.error(err)
                            else:   st.success("✅ Nuevo fixture generado."); st.rerun()
                    with c2:
                        if st.button("🗑️ Eliminar sorteo", key="del_sort"):
                            eliminar_sorteo(categoria, deporte)
                            st.success("✅ Sorteo eliminado."); st.rerun()
                else:
                    n_eqs = sum(len(v) for v in obtener_equipos(categoria, deporte).values())
                    if n_eqs < 2:
                        st.warning(f"Solo hay {n_eqs} equipo(s). Añade al menos 2 en la pestaña Equipo.")
                    else:
                        st.success(f"✅ {n_eqs} equipos listos para sortear.")
                    if st.button("🎲 Realizar sorteo", key="sort_btn"):
                        with st.spinner("Generando fixture..."):
                            ok, err = realizar_sorteo(categoria, deporte)
                        if err: st.error(err)
                        else:
                            s2 = obtener_sorteo(key_s)
                            st.success(f"✅ Sorteo listo. {s2['n_equipos']} equipos · 7 jornadas."); st.rerun()

    st.markdown(f'<hr style="height:2px;background:linear-gradient(90deg,{t["ac"]},transparent);border:none;margin:12px 0 16px;">', unsafe_allow_html=True)

    # ── Vistas ────────────────────────────────────────────────────────────────
    vista = st.tabs(["📊 Tabla", "📅 Partidos", "👥 Equipos"])

    with vista[0]:
        render_tabla(categoria, deporte)

    with vista[1]:
        partidos = obtener_partidos(categoria, deporte)
        if partidos:
            fechas_dict = {}
            for p in partidos:
                fechas_dict.setdefault(p[1][:10], []).append(p)
            for j_idx, fch in enumerate(sorted(fechas_dict.keys())):
                st.markdown(f"""<div style="background:{t['bgs']};border-left:4px solid {t['ac']};
                     padding:8px 14px;margin:14px 0 6px;border-radius:0 6px 6px 0;
                     display:flex;align-items:center;gap:10px;">
                  <span style="background:{t['ac']};color:{t['bfg']};padding:2px 10px;
                        border-radius:20px;font-size:0.75rem;font-weight:700;">J{j_idx+1}</span>
                  <span style="color:{t['ac']};font-weight:700;font-size:0.9rem;">JORNADA {j_idx+1}</span>
                  <span style="color:{t['tx3']};font-size:0.82rem;">📅 {fch}</span>
                </div>""", unsafe_allow_html=True)
                for pid, fecha, enf, estado, g1, g2 in fechas_dict[fch]:
                    st.markdown(card_partido(enf_limpio(enf), fecha[11:16] or "15:00", estado, g1, g2), unsafe_allow_html=True)
        else:
            st.info("Sin partidos. Usa el Panel de Gestión → Sorteo para generar el fixture.")

    with vista[2]:
        equipos_dep = obtener_equipos(categoria, deporte)
        if equipos_dep:
            cols = st.columns(2)
            for idx_col, (cur, eqs) in enumerate(sorted(equipos_dep.items())):
                if not eqs: continue
                with cols[idx_col % 2]:
                    st.markdown(f"""<div style="background:{t['bgc']};border-top:3px solid {t['ac']};
                         border-radius:8px 8px 0 0;padding:8px 14px;">
                      <span style="font-size:0.68rem;font-weight:700;letter-spacing:2px;color:{t['tx3']};">CURSO {cur}</span>
                    </div>""", unsafe_allow_html=True)
                    for eq in eqs:
                        jugs = obtener_jugadores(categoria, deporte, cur, eq)
                        nombres = ", ".join(j["nombre"] for j in jugs) if jugs else ""
                        st.markdown(f"""<div style="background:{t['bgc']};border:1px solid {t['bga']};
                             border-top:none;padding:10px 14px;">
                          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                            <span>⚽</span>
                            <span style="font-weight:700;color:{t['tx']};font-size:0.9rem;">{eq}</span>
                            <span style="background:{t['ac']};color:{t['bfg']};padding:1px 8px;
                                  border-radius:20px;font-size:0.7rem;font-weight:700;">{len(jugs)} jug.</span>
                          </div>
                          {f'<div style="color:{t["tx3"]};font-size:0.75rem;margin-top:4px;padding-left:24px;">{nombres}</div>' if nombres else ''}
                        </div>""", unsafe_allow_html=True)
                    st.markdown(f'<div style="background:{t["bgc"]};border-radius:0 0 8px 8px;height:6px;border:1px solid {t["bga"]};border-top:none;margin-bottom:10px;"></div>', unsafe_allow_html=True)
        else:
            st.info("Sin equipos registrados para este deporte.")
