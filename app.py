import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import qrcode
import json
import os
from io import BytesIO
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(page_title="BANCO KPI PRO", layout="wide")

# ---------------- LOGIN ----------------
USERS = {"ADMIN": "1234"}

if "auth" not in st.session_state:
    st.session_state.auth = False

st.sidebar.title("🔐 LOGIN")
user = st.sidebar.text_input("USUARIO").upper()
password = st.sidebar.text_input("CONTRASEÑA", type="password")

if st.sidebar.button("INGRESAR"):
    if USERS.get(user) == password:
        st.session_state.auth = True
    else:
        st.sidebar.error("ACCESO INCORRECTO")

if not st.session_state.auth:
    st.stop()

# ---------------- DB ----------------
conn = sqlite3.connect("bank.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS empleados(
    id TEXT PRIMARY KEY,
    nombre TEXT,
    edad INTEGER,
    estado TEXT,
    profesion TEXT,
    cargo TEXT,
    foto BLOB
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS kpis(
    id TEXT,
    indicador TEXT,
    meta REAL,
    real REAL,
    proyectado REAL
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS cargos(
    nombre TEXT,
    indicador TEXT
)
""")

conn.commit()

# ---------------- INIT CARGOS ----------------
if pd.read_sql("SELECT * FROM cargos", conn).empty:
    base = {
        "GERENTE FINANCIERO": ["RENTABILIDAD","ROA","ROE","LIQUIDEZ"],
        "RECURSOS HUMANOS": ["AUSENTISMO","CLIMA","ROTACION"],
        "ANALISTA DE DATOS": ["PRECISION","TIEMPO","SISTEMAS"]
    }
    for cargo, inds in base.items():
        for i in inds:
            c.execute("INSERT INTO cargos VALUES (?,?)",(cargo,i))
    conn.commit()

# ---------------- FUNCIONES ----------------
def regenerar_kpis(emp_id, cargo):
    c.execute("DELETE FROM kpis WHERE id=?", (emp_id,))
    indicadores = pd.read_sql(
        "SELECT indicador FROM cargos WHERE nombre=?",
        conn, params=(cargo,)
    )
    for ind in indicadores["indicador"]:
        c.execute("INSERT INTO kpis VALUES (?,?,?,?,?)",
                  (emp_id, ind, 0, 0, 0))
    conn.commit()

def generar_qr(data, kpis_df):
    contenido = {
        "id": data["id"],
        "nombre": data["nombre"],
        "cargo": data["cargo"],
        "kpis": kpis_df.to_dict(orient="records")
    }
    img = qrcode.make(json.dumps(contenido))
    buf = BytesIO()
    img.save(buf)
    return buf.getvalue()

def mayus(df):
    df = df.copy()
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: x.upper() if isinstance(x, str) else x
        )
    df.columns = [c.upper() for c in df.columns]
    return df

# ---------------- MENU ----------------
menu = st.sidebar.radio("MENÚ", [
    "DASHBOARD",
    "REGISTRAR",
    "EDITAR",
    "KPIS",
    "ESCÁNER",
    "CARGOS"
])

# =========================================================
# DASHBOARD EJECUTIVO PERFECCIONADO (VERSION CLON REAL V14)
# =========================================================
if menu == "DASHBOARD":

    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background-color: #060b13 !important;
    }
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        max-width: 96% !important;
    }
    
    div[data-testid="stVerticalBlock"] > div:has(div.kpi-contenedor-tarjeta) {
        background: #09101a !important;
        border: 1px solid #142334 !important;
        border-radius: 14px !important;
        padding: 22px !important;
        margin-bottom: 12px !important;
    }

    .hdr-clon-box {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        margin-bottom: 15px;
    }
    .hdr-logo-box {
        background: #09101a;
        border: 1px solid #00E676;
        box-shadow: 0px 0px 12px rgba(0, 230, 118, 0.3);
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 24px;
    }
    .hdr-title-center { text-align: center; flex-grow: 1; }
    .hdr-title-main { font-size: 30px; font-weight: 800; color: white; margin: 0; letter-spacing: 0.5px; }
    .hdr-title-sub { color: #00E676; font-size: 13px; font-weight: 700; letter-spacing: 1.5px; margin-top: 2px; }
    .hdr-date-badge { background-color: #0b131c; border: 1px solid #142334; border-radius: 8px; padding: 8px 16px; text-align: right; }

    .top-metric-frame {
        background: #0b131c;
        border-radius: 10px;
        padding: 12px;
        border: 1px solid #142334;
        display: flex;
        align-items: center;
        gap: 12px;
        height: 68px;
    }
    .top-icon-circle {
        font-size: 18px;
        background: rgba(0, 230, 118, 0.06);
        padding: 8px;
        border-radius: 6px;
        border: 1px solid rgba(0, 230, 118, 0.2);
        display: flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
    }
    .top-lbl { color: #7a8b9e; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    .top-val { color: white; font-size: 20px; font-weight: 700; line-height: 1.1; }
    .top-dsc { color: #4f6174; font-size: 10px; }

    .kpi-card-header-row { display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 12px; }
    .kpi-card-header-left { display: flex; align-items: center; }
    .badge-sym-frame { background: rgba(0, 230, 118, 0.12); color: #00E676; padding: 3px 9px; border-radius: 6px; font-weight: 800; font-size: 14px; margin-right: 12px; border: 1px solid rgba(0, 230, 118, 0.25); }
    .kpi-title-text { color: white; font-size: 16px; font-weight: 700; }

    .row-data-align { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-size: 13px; width: 100%; }
    .bullet-circle { height: 8px; width: 8px; border-radius: 50%; display: inline-block; margin-right: 8px; }
    .b-meta { background-color: #2196F3; }
    .b-proy { background-color: #FFC107; }
    .b-real { background-color: #00E676; }
    .lbl-style { color: #7a8b9e; font-weight: 600; text-transform: uppercase; }
    .val-style { color: white; font-weight: 700; font-family: monospace; font-size: 13.5px; }

    .box-comp-clon { background: #0e1926; border: 1px solid #1a2d42; border-radius: 10px; padding: 12px; text-align: center; margin-top: 15px; width: 100%; }
    .box-comp-lbl { color: #7a8b9e; font-size: 11px; font-weight: 500; }
    .box-comp-val { color: #00E676; font-size: 22px; font-weight: 700; margin: 2px 0; }
    .box-comp-status { color: #00E676; font-size: 11px; font-weight: 600; }

    .card-footer-note { text-align: center; color: #00E676; font-size: 11px; opacity: 0.6; margin-top: 15px; font-weight: 500; width: 100%; }
    .footer-bar-clon { display: flex; justify-content: space-between; padding-top: 12px; border-top: 1px solid #142334; color: #4f6174; font-size: 11px; margin-top: 30px; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

    empleados = pd.read_sql("SELECT * FROM empleados", conn)
    kpis = pd.read_sql("SELECT * FROM kpis", conn)

    total_emp = len(empleados)
    total_kp = len(kpis)
    prom_cump = round((kpis["real"].sum() / (kpis["meta"].sum() + 1)) * 100, 2) if not kpis.empty else 0
    kpis_riesgo = len(kpis[kpis["real"] < kpis["meta"]]) if not kpis.empty else 0
    kpis_ok = max(total_kp - kpis_riesgo, 0)
    fecha_badge = datetime.now().strftime("%d/%m/%Y")

    st.markdown(f"""
    <div class='hdr-clon-box'>
        <div class='hdr-logo-box'>🏦</div>
        <div class='hdr-title-center'>
            <h1 class='hdr-title-main'>DASHBOARD EJECUTIVO</h1>
            <div class='hdr-title-sub'>GERENCIA DE BANCO KPI</div>
        </div>
        <div class='hdr-date-badge'>
            <span style='color:#7a8b9e; font-size:9px; display:block; font-weight:600;'>FECHA ACTUAL</span>
            <span style='color:white; font-size:12px; font-weight:700;'>📅 {fecha_badge}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    t1, t2, t3, t4, t5 = st.columns(5)
    with t1:
        st.markdown(f"<div class='top-metric-frame'><div class='top-icon-circle' style='color:#00E676;'>👥</div><div><div class='top-lbl'>Colaboradores</div><div class='top-val'>{total_emp}</div><div class='top-dsc'>Total Personal</div></div></div>", unsafe_allow_html=True)
    with t2:
        st.markdown(f"<div class='top-metric-frame'><div class='top-icon-circle' style='color:#2196F3;'>📈</div><div><div class='top-lbl'>KPIs Activos</div><div class='top-val'>{total_kp}</div><div class='top-dsc'>Indicadores</div></div></div>", unsafe_allow_html=True)
    with t3:
        st.markdown(f"<div class='top-metric-frame'><div class='top-icon-circle' style='color:#00E676;'>🎯</div><div><div class='top-lbl'>Cumplimiento</div><div class='top-val'>{prom_cump}%</div><div class='top-dsc'>Promedio General</div></div></div>", unsafe_allow_html=True)
    with t4:
        st.markdown(f"<div class='top-metric-frame'><div class='top-icon-circle' style='color:#00E676;'>✅</div><div><div class='top-lbl'>En Objetivo</div><div class='top-val'>{kpis_ok}</div><div class='top-dsc'>Sin Riesgo</div></div></div>", unsafe_allow_html=True)
    with t5:
        c_alert = "#FFC107" if kpis_riesgo > 0 else "#7a8b9e"
        st.markdown(f"<div class='top-metric-frame'><div class='top-icon-circle' style='color:{c_alert};'>⚠️</div><div><div class='top-lbl'>En Riesgo</div><div class='top-val' style='color:{c_alert};'>{kpis_riesgo}</div><div class='top-dsc'>Atención</div></div></div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

    for index in range(0, len(kpis), 2):
        par_kpis = kpis.iloc[index:index+2]
        bloque_columnas = st.columns(2)

        for col_pos, (idx, row) in enumerate(par_kpis.iterrows()):
            m_val = max(row["meta"], 1)
            r_val = row["real"]
            p_val = row["proyectado"]
            pct_cump = round((r_val / m_val) * 100, 2)

            badge_txt = "$"
            ind_title = f"{row['indicador']}"
            txt_footer = "Valores expresados en CÓRDOBAS (C$)"

            if row["indicador"] == "RENTABILIDAD":
                ind_title = "RENTABILIDAD (Utilidad Generada)"
            elif row["indicador"] == "ROA":
                badge_txt = "%"
                ind_title = "ROA (Rendimiento sobre Activos)"
                txt_footer = "Valores expresados en PORCENTAJE (%)"
            elif row["indicador"] == "ROE":
                badge_txt = "%"
                ind_title = "ROE (Rendimiento sobre Patrimonio)"
                txt_footer = "Valores expresados en PORCENTAJE (%)"
            elif row["indicador"] == "LIQUIDEZ":
                ind_title = "LIQUIDEZ (Disponibilidad de Efectivo)"

            with bloque_columnas[col_pos]:
                with st.container():
                    st.markdown(f"<div class='kpi-contenedor-tarjeta'></div>", unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div class='kpi-card-header-row'>
                        <div class='kpi-card-header-left'>
                            <span class='badge-sym-frame'>{badge_txt}</span>
                            <span class='kpi-title-text'>{ind_title}</span>
                        </div>
                        <div style='color:#4f6174; font-weight:bold; font-size:14px;'>•••</div>
                    </div>
                    """, unsafe_allow_html=True)

                    c_grafico, c_datos = st.columns([1.1, 1.2])

                    with c_grafico:
                        val_graf_cump = r_val if r_val <= m_val else m_val
                        val_graf_rest = max(m_val - r_val, 0)
                        
                        fig_donut = go.Figure()
                        fig_donut.add_trace(go.Pie(
                            values=[val_graf_cump, val_graf_rest],
                            hole=0.52,
                            textinfo="none",
                            hoverinfo="none",
                            marker=dict(colors=["#00E676", "#142c1b"]),
                            direction="clockwise",
                            sort=False
                        ))

                        fig_donut.update_layout(
                            height=180,
                            margin=dict(t=0, b=0, l=0, r=0),
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            showlegend=False,
                            annotations=[dict(
                                text=f"<b style='font-size:22px;color:white;'>{pct_cump}%</b><br><span style='font-size:10px;color:#7a8b9e;font-weight:600;'>Cumplimiento</span>",
                                showarrow=False,
                                font=dict(color="white")
                            )]
                        )
                        st.plotly_chart(fig_donut, use_container_width=True, key=f"donut_{idx}", config={'displayModeBar': False})

                    with c_datos:
                        f_str = ",.2f"
                        s_str = "%" if badge_txt == "%" else ""
                        p_str = "C$ " if badge_txt == "$" else ""

                        bloque_datos_html = (
                            f"<div style='padding-top:5px; width:100%;'>"
                            f"  <div class='row-data-align'>"
                            f"      <div><span class='bullet-circle b-meta'></span><span class='lbl-style'>META</span></div>"
                            f"      <div class='val-style'>{p_str}{m_val:{f_str}}{s_str}</div>"
                            f"  </div>"
                            f"  <div class='row-data-align'>"
                            f"      <div><span class='bullet-circle b-proy'></span><span class='lbl-style'>PROYECTADO</span></div>"
                            f"      <div class='val-style'>{p_str}{p_val:{f_str}}{s_str}</div>"
                            f"  </div>"
                            f"  <div class='row-data-align'>"
                            f"      <div><span class='bullet-circle b-real'></span><span class='lbl-style'>REAL</span></div>"
                            f"      <div class='val-style'>{p_str}{r_val:{f_str}}{s_str}</div>"
                            f"  </div>"
                            f"  <div class='box-comp-clon'>"
                            f"      <div class='box-comp-lbl'>Cumplimiento</div>"
                            f"      <div class='box-comp-val'>{pct_cump}%</div>"
                            f"      <div class='box-comp-status'>▲ Por encima de la meta</div>"
                            f"  </div>"
                            f"</div>"
                        )
                        st.markdown(bloque_datos_html, unsafe_allow_html=True)

                    st.markdown(f"<div class='card-footer-note'>{txt_footer}</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class='footer-bar-clon'>
        <div>⚙️ Sistema de Gestión KPI - Banco &nbsp;|&nbsp; Información actualizada en tiempo real</div>
        <div style='color:#00E676;'>Datos confiables para decisiones inteligentes 📈</div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# REGISTRAR
# =========================================================
elif menu == "REGISTRAR":
    st.title("➕ REGISTRO DE EMPLEADO")
    cargos = pd.read_sql("SELECT DISTINCT nombre FROM cargos", conn)

    with st.form("form_reg"):
        col1, col2, col3 = st.columns(3)
        with col1:
            id = st.text_input("ID").upper()
            nombre = st.text_input("NOMBRE").upper()
        with col2:
            edad = st.number_input("EDAD", 18, 70)
            estado = st.selectbox("ESTADO", ["SOLTERO","CASADO"])
        with col3:
            profesion = st.text_input("PROFESIÓN").upper()
            cargo = st.selectbox("CARGO", cargos["nombre"])

        foto = st.file_uploader("FOTO", type=["jpg","png"])

        if st.form_submit_button("GUARDAR"):
            img = foto.read() if foto else None
            c.execute("""
            INSERT OR REPLACE INTO empleados
            VALUES (?,?,?,?,?,?,?)
            """, (id,nombre,edad,estado,profesion,cargo,img))
            
            regenerar_kpis(id, cargo)
            st.success("EMPLEADO REGISTRADO")

# =========================================================
# EDITAR
# =========================================================
elif menu == "EDITAR":
    st.title("✏️ EDITAR EMPLEADO")
    df = pd.read_sql("SELECT * FROM empleados", conn)

    if df.empty:
        st.warning("NO HAY EMPLEADOS")
    else:
        emp_id = st.selectbox("EMPLEADO", df["id"])
        data = df[df["id"] == emp_id].iloc[0]

        nombre = st.text_input("NOMBRE", value=data["nombre"]).upper()
        edad = st.number_input("EDAD", value=int(data["edad"]))
        estado = st.selectbox("ESTADO", ["SOLTERO","CASADO"])

        cargos = pd.read_sql("SELECT DISTINCT nombre FROM cargos", conn)
        cargo = st.selectbox("CARGO", cargos["nombre"])
        foto = st.file_uploader("ACTUALIZAR FOTO", type=["jpg","png"])

        if st.button("ACTUALIZAR"):
            img = foto.read() if foto else data["foto"]
            c.execute("""
            UPDATE empleados
            SET nombre=?, edad=?, estado=?, cargo=?, foto=?
            WHERE id=?
            """, (nombre,edad,estado,cargo,img,emp_id))
            
            regenerar_kpis(emp_id, cargo)
            st.success("ACTUALIZADO")

# =========================================================
# KPIS
# =========================================================
elif menu == "KPIS":
    st.title("📊 KPIs")
    df = pd.read_sql("SELECT * FROM empleados", conn)

    if not df.empty:
        emp_id = st.selectbox("EMPLEADO", df["id"])
        kpis_df = pd.read_sql("SELECT * FROM kpis WHERE id=?", conn, params=(emp_id,))

        for i, row in kpis_df.iterrows():
            st.subheader(row["indicador"])
            col1, col2, col3 = st.columns(3)
            with col1:
                m = st.number_input("META", value=row["meta"], key=f"m{i}")
            with col2:
                p = st.number_input("PROYECTADO", value=row["proyectado"], key=f"p{i}")
            with col3:
                r = st.number_input("REAL", value=row["real"], key=f"r{i}")

            if st.button(f"GUARDAR {row['indicador']}", key=f"btn_{i}"):
                c.execute("""
                UPDATE kpis SET meta=?, real=?, proyectado=?
                WHERE id=? AND indicador=?
                """, (m,r,p,emp_id,row["indicador"]))
                conn.commit()
                st.success(f"{row['indicador']} ACTUALIZADO")

# =========================================================
# ESCÁNER VISTA EJECUTIVA
# =========================================================
elif menu == "ESCÁNER":

    st.markdown("""
    <style>
    .stApp { background-color: #050814 !important; }
    .card {
        background: #090e1d;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid #141b2d;
    }
    .tt { font-size: 38px; font-weight: 700; color: white; letter-spacing: 0.5px; }
    .sub { font-size: 16px; color: #7b52ff; font-weight: 600; margin-top: 6px; }
    .section-title { color: white; font-size: 22px; font-weight: 700; margin-bottom: 20px; display: flex; align-items: center; gap: 8px; }
    .box {
        background: #0b1326;
        padding: 16px;
        border-radius: 10px;
        margin-bottom: 14px;
        border: 1px solid #172033;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .lbl { font-size: 14px; color: #637393; font-weight: 700; text-transform: uppercase; }
    .val { font-size: 22px; font-weight: 700; color: white; }
    .profile-container { display: flex; gap: 30px; align-items: center; background: #0b1326; padding: 20px; border-radius: 10px; border: 1px solid #172033; }
    .profile-item { display: flex; align-items: center; gap: 15px; flex: 1; }
    .profile-icon { background: rgba(123, 82, 255, 0.15); color: #7b52ff; padding: 12px; border-radius: 50px; font-size: 26px; display: flex; align-items: center; justify-content: center; width: 55px; height: 55px; }
    .lbl-profile { font-size: 18px; color: #7b52ff; font-weight: 700; }
    .val-profile { font-size: 24px; font-weight: 700; color: white; }
    
    .stDataFrame td, .stDataFrame div[data-testid="stTableDataCell"] p {
        font-size: 24px !important; font-weight: 700 !important; color: white !important;
    }
    .stDataFrame th, .stDataFrame div[data-testid="stHeaderCell"] p {
        font-size: 26px !important; font-weight: 900 !important; color: #8e6eff !important; text-transform: uppercase !important;
    }
    </style>
    """, unsafe_allow_html=True)

    empleados = pd.read_sql("SELECT * FROM empleados", conn)

    if empleados.empty:
        st.warning("SIN EMPLEADOS REGISTRADOS")
        st.stop()

    empleados["vista"] = empleados["id"].astype(str) + " - " + empleados["nombre"]

    parametros_url = st.query_params
    indice_por_defecto = 0
    
    if "emp_id" in parametros_url:
        id_buscado = str(parametros_url["emp_id"])
        coincidencias = empleados[empleados["id"].astype(str) == id_buscado].index
        if not coincidencias.empty:
            indice_por_defecto = int(coincidencias[0])

    c1, c2 = st.columns([3.8, 2.2])
    with c1:
        st.markdown("""
        <div class='card' style='margin-bottom: 15px;'>
            <div style='display: flex; align-items: center; gap: 15px;'>
                <span style='font-size: 32px;'>📄</span>
                <div>
                    <div class='tt'>ESCÁNER EMPLEADO</div>
                    <div class='sub'>Perfil • Cargo • KPIs</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("<p style='color:#637393; font-size:16px; font-weight:700; margin-bottom:4px; margin-top:5px;'>Empleado</p>", unsafe_allow_html=True)
        emp = st.selectbox("Empleado", empleados["vista"], index=indice_por_defecto, label_visibility="collapsed")

    id_emp = emp.split(" - ")[0]
    empleado = empleados[empleados["id"].astype(str) == id_emp].iloc[0]

    izq, der = st.columns([1.3, 3])

    with izq:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>📷 FOTO</div>", unsafe_allow_html=True)

        os.makedirs("fotos", exist_ok=True)
        ruta = f"fotos/{id_emp}.png"
        foto = st.file_uploader("", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

        if foto:
            with open(ruta, "wb") as f:
                f.write(foto.read())
            st.rerun()

        if os.path.exists(ruta):
            st.image(ruta, use_container_width=True)
        else:
            st.markdown("""
            <div style='border: 2px dashed #242f4d; border-radius: 10px; padding: 30px; text-align: center; background: #070c18;'>
                <div style='font-size: 30px; color: #7b52ff; margin-bottom: 8px;'>📥</div>
                <div style='color: white; font-weight: 700; font-size: 14px;'>SUBIR FOTO</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        for x in ["nombre", "edad", "estado", "profesion"]:
            st.markdown(f"""
            <div class='box'>
                <div class='lbl'>{x}</div>
                <div class='val'>{empleado[x]}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with der:
        st.markdown(f"""
        <div class='card'>
            <div class='section-title'>👤 PERFIL</div>
            <div class='profile-container'>
                <div class='profile-item'>
                    <div class='profile-icon'>🏢</div>
                    <div>
                        <div class='lbl-profile'>ÁREA</div>
                        <div class='val-profile'>FINANZAS</div>
                    </div>
                </div>
                <div style='width: 1px; height: 45px; background: #1c263c;'></div>
                <div class='profile-item'>
                    <div class='profile-icon'>💼</div>
                    <div>
                        <div class='lbl-profile'>CARGO</div>
                        <div class='val-profile'>{empleado['cargo'].upper()}</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>📈 KPI DEL PUESTO</div>", unsafe_allow_html=True)

        datos_kpi = pd.read_sql("SELECT * FROM kpis WHERE id=?", conn, params=(id_emp,))

        if not datos_kpi.empty:
            k1, k2 = st.columns([1.8, 1.2])
            with k1:
                tabla = datos_kpi[["indicador", "meta", "proyectado", "real"]]
                st.dataframe(tabla, use_container_width=True, hide_index=True)

            with k2:
                meta = max(datos_kpi["meta"].sum(), 1)
                real = datos_kpi["real"].sum()
                pct = round((real / meta) * 100, 2)

                # Control para que el gráfico no rompa si supera el 100%
                val_cump = min(pct, 100)
                val_rest = max(100 - pct, 0)

                fig = go.Figure()
                fig.add_trace(go.Pie(
                    values=[val_cump, val_rest], 
                    hole=0.72,
                    marker=dict(colors=["#1aff74", "#172033"]),
                    textinfo="none",
                    hoverinfo="skip",
                    sort=False
                ))

                fig.update_layout(
                    height=200,
                    margin=dict(t=0, b=0, l=0, r=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False,
                    annotations=[dict(
                        text=f"<span style='font-size:28px; font-weight:800; color:#1aff74;'>{pct}%</span><br><span style='font-size:11px; font-weight:700; color:white;'>CUMPLIMIENTO</span>",
                        showarrow=False
                    )]
                )
                st.plotly_chart(fig, use_container_width=True, key=f"esc_donut_{id_emp}", config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

        # --- SECCIÓN GENERADOR QR INTEGRADA ---
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>🔑 CÓDIGO QR CREDENCIAL</div>", unsafe_allow_html=True)
        
        qr_bytes = generar_qr(empleado, datos_kpi)
        
        qc1, qc2 = st.columns([1, 2])
        with qc1:
            st.image(qr_bytes, width=180)
        with qc2:
            st.write("Esta credencial QR contiene la información del perfil del colaborador y sus métricas actuales consolidadas.")
            st.download_button(
                label="📥 Descargar Código QR",
                data=qr_bytes,
                file_name=f"QR_{id_emp}.png",
                mime="image/png"
            )
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# CARGOS
# =========================================================
import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import qrcode
import json
import os
from io import BytesIO
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(page_title="BANCO KPI PRO", layout="wide")

# ---------------- LOGIN ----------------
USERS = {"ADMIN": "1234"}

if "auth" not in st.session_state:
    st.session_state.auth = False

st.sidebar.title("🔐 LOGIN")
user = st.sidebar.text_input("USUARIO").upper()
password = st.sidebar.text_input("CONTRASEÑA", type="password")

if st.sidebar.button("INGRESAR"):
    if USERS.get(user) == password:
        st.session_state.auth = True
    else:
        st.sidebar.error("ACCESO INCORRECTO")

if not st.session_state.auth:
    st.stop()

# ---------------- DB ----------------
conn = sqlite3.connect("bank.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS empleados(
    id TEXT PRIMARY KEY,
    nombre TEXT,
    edad INTEGER,
    estado TEXT,
    profesion TEXT,
    cargo TEXT,
    foto BLOB
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS kpis(
    id TEXT,
    indicador TEXT,
    meta REAL,
    real REAL,
    proyectado REAL
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS cargos(
    nombre TEXT,
    indicador TEXT
)
""")

conn.commit()

# ---------------- INIT CARGOS ----------------
if pd.read_sql("SELECT * FROM cargos", conn).empty:
    base = {
        "GERENTE FINANCIERO": ["RENTABILIDAD","ROA","ROE","LIQUIDEZ"],
        "RECURSOS HUMANOS": ["AUSENTISMO","CLIMA","ROTACION"],
        "ANALISTA DE DATOS": ["PRECISION","TIEMPO","SISTEMAS"]
    }
    for cargo, inds in base.items():
        for i in inds:
            c.execute("INSERT INTO cargos VALUES (?,?)",(cargo,i))
    conn.commit()

# ---------------- FUNCIONES ----------------
def regenerar_kpis(emp_id, cargo):
    c.execute("DELETE FROM kpis WHERE id=?", (emp_id,))
    indicadores = pd.read_sql(
        "SELECT indicador FROM cargos WHERE nombre=?",
        conn, params=(cargo,)
    )
    for ind in indicadores["indicador"]:
        c.execute("INSERT INTO kpis VALUES (?,?,?,?,?)",
                  (emp_id, ind, 0, 0, 0))
    conn.commit()

def generar_qr(data, kpis_df):
    contenido = {
        "id": data["id"],
        "nombre": data["nombre"],
        "cargo": data["cargo"],
        "kpis": kpis_df.to_dict(orient="records")
    }
    img = qrcode.make(json.dumps(contenido))
    buf = BytesIO()
    img.save(buf)
    return buf.getvalue()

def mayus(df):
    df = df.copy()
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: x.upper() if isinstance(x, str) else x
        )
    df.columns = [c.upper() for c in df.columns]
    return df

# ---------------- MENU ----------------
menu = st.sidebar.radio("MENÚ", [
    "DASHBOARD",
    "REGISTRAR",
    "EDITAR",
    "KPIS",
    "ESCÁNER",
    "CARGOS"
])

# =========================================================
# DASHBOARD EJECUTIVO PERFECCIONADO (VERSION CLON REAL V14)
# =========================================================
if menu == "DASHBOARD":

    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background-color: #060b13 !important;
    }
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        max-width: 96% !important;
    }
    
    div[data-testid="stVerticalBlock"] > div:has(div.kpi-contenedor-tarjeta) {
        background: #09101a !important;
        border: 1px solid #142334 !important;
        border-radius: 14px !important;
        padding: 22px !important;
        margin-bottom: 12px !important;
    }

    .hdr-clon-box {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        margin-bottom: 15px;
    }
    .hdr-logo-box {
        background: #09101a;
        border: 1px solid #00E676;
        box-shadow: 0px 0px 12px rgba(0, 230, 118, 0.3);
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 24px;
    }
    .hdr-title-center { text-align: center; flex-grow: 1; }
    .hdr-title-main { font-size: 30px; font-weight: 800; color: white; margin: 0; letter-spacing: 0.5px; }
    .hdr-title-sub { color: #00E676; font-size: 13px; font-weight: 700; letter-spacing: 1.5px; margin-top: 2px; }
    .hdr-date-badge { background-color: #0b131c; border: 1px solid #142334; border-radius: 8px; padding: 8px 16px; text-align: right; }

    .top-metric-frame {
        background: #0b131c;
        border-radius: 10px;
        padding: 12px;
        border: 1px solid #142334;
        display: flex;
        align-items: center;
        gap: 12px;
        height: 68px;
    }
    .top-icon-circle {
        font-size: 18px;
        background: rgba(0, 230, 118, 0.06);
        padding: 8px;
        border-radius: 6px;
        border: 1px solid rgba(0, 230, 118, 0.2);
        display: flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
    }
    .top-lbl { color: #7a8b9e; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    .top-val { color: white; font-size: 20px; font-weight: 700; line-height: 1.1; }
    .top-dsc { color: #4f6174; font-size: 10px; }

    .kpi-card-header-row { display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 12px; }
    .kpi-card-header-left { display: flex; align-items: center; }
    .badge-sym-frame { background: rgba(0, 230, 118, 0.12); color: #00E676; padding: 3px 9px; border-radius: 6px; font-weight: 800; font-size: 14px; margin-right: 12px; border: 1px solid rgba(0, 230, 118, 0.25); }
    .kpi-title-text { color: white; font-size: 16px; font-weight: 700; }

    .row-data-align { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-size: 13px; width: 100%; }
    .bullet-circle { height: 8px; width: 8px; border-radius: 50%; display: inline-block; margin-right: 8px; }
    .b-meta { background-color: #2196F3; }
    .b-proy { background-color: #FFC107; }
    .b-real { background-color: #00E676; }
    .lbl-style { color: #7a8b9e; font-weight: 600; text-transform: uppercase; }
    .val-style { color: white; font-weight: 700; font-family: monospace; font-size: 13.5px; }

    .box-comp-clon { background: #0e1926; border: 1px solid #1a2d42; border-radius: 10px; padding: 12px; text-align: center; margin-top: 15px; width: 100%; }
    .box-comp-lbl { color: #7a8b9e; font-size: 11px; font-weight: 500; }
    .box-comp-val { color: #00E676; font-size: 22px; font-weight: 700; margin: 2px 0; }
    .box-comp-status { color: #00E676; font-size: 11px; font-weight: 600; }

    .card-footer-note { text-align: center; color: #00E676; font-size: 11px; opacity: 0.6; margin-top: 15px; font-weight: 500; width: 100%; }
    .footer-bar-clon { display: flex; justify-content: space-between; padding-top: 12px; border-top: 1px solid #142334; color: #4f6174; font-size: 11px; margin-top: 30px; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

    empleados = pd.read_sql("SELECT * FROM empleados", conn)
    kpis = pd.read_sql("SELECT * FROM kpis", conn)

    total_emp = len(empleados)
    total_kp = len(kpis)
    prom_cump = round((kpis["real"].sum() / (kpis["meta"].sum() + 1)) * 100, 2) if not kpis.empty else 0
    kpis_riesgo = len(kpis[kpis["real"] < kpis["meta"]]) if not kpis.empty else 0
    kpis_ok = max(total_kp - kpis_riesgo, 0)
    fecha_badge = datetime.now().strftime("%d/%m/%Y")

    st.markdown(f"""
    <div class='hdr-clon-box'>
        <div class='hdr-logo-box'>🏦</div>
        <div class='hdr-title-center'>
            <h1 class='hdr-title-main'>DASHBOARD EJECUTIVO</h1>
            <div class='hdr-title-sub'>GERENCIA DE BANCO KPI</div>
        </div>
        <div class='hdr-date-badge'>
            <span style='color:#7a8b9e; font-size:9px; display:block; font-weight:600;'>FECHA ACTUAL</span>
            <span style='color:white; font-size:12px; font-weight:700;'>📅 {fecha_badge}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    t1, t2, t3, t4, t5 = st.columns(5)
    with t1:
        st.markdown(f"<div class='top-metric-frame'><div class='top-icon-circle' style='color:#00E676;'>👥</div><div><div class='top-lbl'>Colaboradores</div><div class='top-val'>{total_emp}</div><div class='top-dsc'>Total Personal</div></div></div>", unsafe_allow_html=True)
    with t2:
        st.markdown(f"<div class='top-metric-frame'><div class='top-icon-circle' style='color:#2196F3;'>📈</div><div><div class='top-lbl'>KPIs Activos</div><div class='top-val'>{total_kp}</div><div class='top-dsc'>Indicadores</div></div></div>", unsafe_allow_html=True)
    with t3:
        st.markdown(f"<div class='top-metric-frame'><div class='top-icon-circle' style='color:#00E676;'>🎯</div><div><div class='top-lbl'>Cumplimiento</div><div class='top-val'>{prom_cump}%</div><div class='top-dsc'>Promedio General</div></div></div>", unsafe_allow_html=True)
    with t4:
        st.markdown(f"<div class='top-metric-frame'><div class='top-icon-circle' style='color:#00E676;'>✅</div><div><div class='top-lbl'>En Objetivo</div><div class='top-val'>{kpis_ok}</div><div class='top-dsc'>Sin Riesgo</div></div></div>", unsafe_allow_html=True)
    with t5:
        c_alert = "#FFC107" if kpis_riesgo > 0 else "#7a8b9e"
        st.markdown(f"<div class='top-metric-frame'><div class='top-icon-circle' style='color:{c_alert};'>⚠️</div><div><div class='top-lbl'>En Riesgo</div><div class='top-val' style='color:{c_alert};'>{kpis_riesgo}</div><div class='top-dsc'>Atención</div></div></div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

    for index in range(0, len(kpis), 2):
        par_kpis = kpis.iloc[index:index+2]
        bloque_columnas = st.columns(2)

        for col_pos, (idx, row) in enumerate(par_kpis.iterrows()):
            m_val = max(row["meta"], 1)
            r_val = row["real"]
            p_val = row["proyectado"]
            pct_cump = round((r_val / m_val) * 100, 2)

            badge_txt = "$"
            ind_title = f"{row['indicador']}"
            txt_footer = "Valores expresados en CÓRDOBAS (C$)"

            if row["indicador"] == "RENTABILIDAD":
                ind_title = "RENTABILIDAD (Utilidad Generada)"
            elif row["indicador"] == "ROA":
                badge_txt = "%"
                ind_title = "ROA (Rendimiento sobre Activos)"
                txt_footer = "Valores expresados en PORCENTAJE (%)"
            elif row["indicador"] == "ROE":
                badge_txt = "%"
                ind_title = "ROE (Rendimiento sobre Patrimonio)"
                txt_footer = "Valores expresados en PORCENTAJE (%)"
            elif row["indicador"] == "LIQUIDEZ":
                ind_title = "LIQUIDEZ (Disponibilidad de Efectivo)"

            with bloque_columnas[col_pos]:
                with st.container():
                    st.markdown(f"<div class='kpi-contenedor-tarjeta'></div>", unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div class='kpi-card-header-row'>
                        <div class='kpi-card-header-left'>
                            <span class='badge-sym-frame'>{badge_txt}</span>
                            <span class='kpi-title-text'>{ind_title}</span>
                        </div>
                        <div style='color:#4f6174; font-weight:bold; font-size:14px;'>•••</div>
                    </div>
                    """, unsafe_allow_html=True)

                    c_grafico, c_datos = st.columns([1.1, 1.2])

                    with c_grafico:
                        val_graf_cump = r_val if r_val <= m_val else m_val
                        val_graf_rest = max(m_val - r_val, 0)
                        
                        fig_donut = go.Figure()
                        fig_donut.add_trace(go.Pie(
                            values=[val_graf_cump, val_graf_rest],
                            hole=0.52,
                            textinfo="none",
                            hoverinfo="none",
                            marker=dict(colors=["#00E676", "#142c1b"]),
                            direction="clockwise",
                            sort=False
                        ))

                        fig_donut.update_layout(
                            height=180,
                            margin=dict(t=0, b=0, l=0, r=0),
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            showlegend=False,
                            annotations=[dict(
                                text=f"<b style='font-size:22px;color:white;'>{pct_cump}%</b><br><span style='font-size:10px;color:#7a8b9e;font-weight:600;'>Cumplimiento</span>",
                                showarrow=False,
                                font=dict(color="white")
                            )]
                        )
                        st.plotly_chart(fig_donut, use_container_width=True, key=f"donut_{idx}", config={'displayModeBar': False})

                    with c_datos:
                        f_str = ",.2f"
                        s_str = "%" if badge_txt == "%" else ""
                        p_str = "C$ " if badge_txt == "$" else ""

                        bloque_datos_html = (
                            f"<div style='padding-top:5px; width:100%;'>"
                            f"  <div class='row-data-align'>"
                            f"      <div><span class='bullet-circle b-meta'></span><span class='lbl-style'>META</span></div>"
                            f"      <div class='val-style'>{p_str}{m_val:{f_str}}{s_str}</div>"
                            f"  </div>"
                            f"  <div class='row-data-align'>"
                            f"      <div><span class='bullet-circle b-proy'></span><span class='lbl-style'>PROYECTADO</span></div>"
                            f"      <div class='val-style'>{p_str}{p_val:{f_str}}{s_str}</div>"
                            f"  </div>"
                            f"  <div class='row-data-align'>"
                            f"      <div><span class='bullet-circle b-real'></span><span class='lbl-style'>REAL</span></div>"
                            f"      <div class='val-style'>{p_str}{r_val:{f_str}}{s_str}</div>"
                            f"  </div>"
                            f"  <div class='box-comp-clon'>"
                            f"      <div class='box-comp-lbl'>Cumplimiento</div>"
                            f"      <div class='box-comp-val'>{pct_cump}%</div>"
                            f"      <div class='box-comp-status'>▲ Por encima de la meta</div>"
                            f"  </div>"
                            f"</div>"
                        )
                        st.markdown(bloque_datos_html, unsafe_allow_html=True)

                    st.markdown(f"<div class='card-footer-note'>{txt_footer}</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class='footer-bar-clon'>
        <div>⚙️ Sistema de Gestión KPI - Banco &nbsp;|&nbsp; Información actualizada en tiempo real</div>
        <div style='color:#00E676;'>Datos confiables para decisiones inteligentes 📈</div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# REGISTRAR
# =========================================================
elif menu == "REGISTRAR":
st.title("➕ REGISTRO DE EMPLEADO")
    cargos = pd.read_sql("SELECT DISTINCT nombre FROM cargos", conn)

    with st.form("form_reg"):
        
        cargo = st.selectbox("CARGO", cargos["nombre"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            id = st.text_input("ID").upper()
            nombre = st.text_input("NOMBRE").upper()
        with col2:
            edad = st.number_input("EDAD", 18, 70)
            estado = st.selectbox("ESTADO", ["SOLTERO","CASADO"])
        with col3:
            profesion = st.text_input("PROFESIÓN").upper()
            cargo = st.selectbox("CARGO", cargos["nombre"])

        foto = st.file_uploader("FOTO", type=["jpg","png"])

        if st.form_submit_button("GUARDAR"):
            img = foto.read() if foto else None
            c.execute("""
            INSERT OR REPLACE INTO empleados
            VALUES (?,?,?,?,?,?,?)
            """, (id,nombre,edad,estado,profesion,cargo,img))
            
            regenerar_kpis(id, cargo)
            st.success("EMPLEADO REGISTRADO")

# =========================================================
# EDITAR
# =========================================================
elif menu == "EDITAR":
    st.title("✏️ EDITAR EMPLEADO")
    df = pd.read_sql("SELECT * FROM empleados", conn)

    if df.empty:
        st.warning("NO HAY EMPLEADOS")
    else:
        emp_id = st.selectbox("EMPLEADO", df["id"])
        data = df[df["id"] == emp_id].iloc[0]

        nombre = st.text_input("NOMBRE", value=data["nombre"]).upper()
        edad = st.number_input("EDAD", value=int(data["edad"]))
        estado = st.selectbox("ESTADO", ["SOLTERO","CASADO"])

        cargos = pd.read_sql("SELECT DISTINCT nombre FROM cargos", conn)
        cargo = st.selectbox("CARGO", cargos["nombre"])
        foto = st.file_uploader("ACTUALIZAR FOTO", type=["jpg","png"])

        if st.button("ACTUALIZAR"):
            img = foto.read() if foto else data["foto"]
            c.execute("""
            UPDATE empleados
            SET nombre=?, edad=?, estado=?, cargo=?, foto=?
            WHERE id=?
            """, (nombre,edad,estado,cargo,img,emp_id))
            
            regenerar_kpis(emp_id, cargo)
            st.success("ACTUALIZADO")

# =========================================================
# KPIS
# =========================================================
elif menu == "KPIS":
    st.title("📊 KPIs")
    df = pd.read_sql("SELECT * FROM empleados", conn)

    if not df.empty:
        emp_id = st.selectbox("EMPLEADO", df["id"])
        kpis_df = pd.read_sql("SELECT * FROM kpis WHERE id=?", conn, params=(emp_id,))

        for i, row in kpis_df.iterrows():
            st.subheader(row["indicador"])
            col1, col2, col3 = st.columns(3)
            with col1:
                m = st.number_input("META", value=row["meta"], key=f"m{i}")
            with col2:
                p = st.number_input("PROYECTADO", value=row["proyectado"], key=f"p{i}")
            with col3:
                r = st.number_input("REAL", value=row["real"], key=f"r{i}")

            if st.button(f"GUARDAR {row['indicador']}", key=f"btn_{i}"):
                c.execute("""
                UPDATE kpis SET meta=?, real=?, proyectado=?
                WHERE id=? AND indicador=?
                """, (m,r,p,emp_id,row["indicador"]))
                conn.commit()
                st.success(f"{row['indicador']} ACTUALIZADO")

# =========================================================
# ESCÁNER VISTA EJECUTIVA
# =========================================================
elif menu == "ESCÁNER":

    st.markdown("""
    <style>
    .stApp { background-color: #050814 !important; }
    .card {
        background: #090e1d;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid #141b2d;
    }
    .tt { font-size: 38px; font-weight: 700; color: white; letter-spacing: 0.5px; }
    .sub { font-size: 16px; color: #7b52ff; font-weight: 600; margin-top: 6px; }
    .section-title { color: white; font-size: 22px; font-weight: 700; margin-bottom: 20px; display: flex; align-items: center; gap: 8px; }
    .box {
        background: #0b1326;
        padding: 16px;
        border-radius: 10px;
        margin-bottom: 14px;
        border: 1px solid #172033;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .lbl { font-size: 14px; color: #637393; font-weight: 700; text-transform: uppercase; }
    .val { font-size: 22px; font-weight: 700; color: white; }
    .profile-container { display: flex; gap: 30px; align-items: center; background: #0b1326; padding: 20px; border-radius: 10px; border: 1px solid #172033; }
    .profile-item { display: flex; align-items: center; gap: 15px; flex: 1; }
    .profile-icon { background: rgba(123, 82, 255, 0.15); color: #7b52ff; padding: 12px; border-radius: 50px; font-size: 26px; display: flex; align-items: center; justify-content: center; width: 55px; height: 55px; }
    .lbl-profile { font-size: 18px; color: #7b52ff; font-weight: 700; }
    .val-profile { font-size: 24px; font-weight: 700; color: white; }
    
    .stDataFrame td, .stDataFrame div[data-testid="stTableDataCell"] p {
        font-size: 24px !important; font-weight: 700 !important; color: white !important;
    }
    .stDataFrame th, .stDataFrame div[data-testid="stHeaderCell"] p {
        font-size: 26px !important; font-weight: 900 !important; color: #8e6eff !important; text-transform: uppercase !important;
    }
    </style>
    """, unsafe_allow_html=True)

    empleados = pd.read_sql("SELECT * FROM empleados", conn)

    if empleados.empty:
        st.warning("SIN EMPLEADOS REGISTRADOS")
        st.stop()

    empleados["vista"] = empleados["id"].astype(str) + " - " + empleados["nombre"]

    parametros_url = st.query_params
    indice_por_defecto = 0
    
    if "emp_id" in parametros_url:
        id_buscado = str(parametros_url["emp_id"])
        coincidencias = empleados[empleados["id"].astype(str) == id_buscado].index
        if not coincidencias.empty:
            indice_por_defecto = int(coincidencias[0])

    c1, c2 = st.columns([3.8, 2.2])
    with c1:
        st.markdown("""
        <div class='card' style='margin-bottom: 15px;'>
            <div style='display: flex; align-items: center; gap: 15px;'>
                <span style='font-size: 32px;'>📄</span>
                <div>
                    <div class='tt'>ESCÁNER EMPLEADO</div>
                    <div class='sub'>Perfil • Cargo • KPIs</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("<p style='color:#637393; font-size:16px; font-weight:700; margin-bottom:4px; margin-top:5px;'>Empleado</p>", unsafe_allow_html=True)
        emp = st.selectbox("Empleado", empleados["vista"], index=indice_por_defecto, label_visibility="collapsed")

    id_emp = emp.split(" - ")[0]
    empleado = empleados[empleados["id"].astype(str) == id_emp].iloc[0]

    izq, der = st.columns([1.3, 3])

    with izq:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>📷 FOTO</div>", unsafe_allow_html=True)

        os.makedirs("fotos", exist_ok=True)
        ruta = f"fotos/{id_emp}.png"
        foto = st.file_uploader("", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

        if foto:
            with open(ruta, "wb") as f:
                f.write(foto.read())
            st.rerun()

        if os.path.exists(ruta):
            st.image(ruta, use_container_width=True)
        else:
            st.markdown("""
            <div style='border: 2px dashed #242f4d; border-radius: 10px; padding: 30px; text-align: center; background: #070c18;'>
                <div style='font-size: 30px; color: #7b52ff; margin-bottom: 8px;'>📥</div>
                <div style='color: white; font-weight: 700; font-size: 14px;'>SUBIR FOTO</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        for x in ["nombre", "edad", "estado", "profesion"]:
            st.markdown(f"""
            <div class='box'>
                <div class='lbl'>{x}</div>
                <div class='val'>{empleado[x]}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with der:
        st.markdown(f"""
        <div class='card'>
            <div class='section-title'>👤 PERFIL</div>
            <div class='profile-container'>
                <div class='profile-item'>
                    <div class='profile-icon'>🏢</div>
                    <div>
                        <div class='lbl-profile'>ÁREA</div>
                        <div class='val-profile'>FINANZAS</div>
                    </div>
                </div>
                <div style='width: 1px; height: 45px; background: #1c263c;'></div>
                <div class='profile-item'>
                    <div class='profile-icon'>💼</div>
                    <div>
                        <div class='lbl-profile'>CARGO</div>
                        <div class='val-profile'>{empleado['cargo'].upper()}</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>📈 KPI DEL PUESTO</div>", unsafe_allow_html=True)

        datos_kpi = pd.read_sql("SELECT * FROM kpis WHERE id=?", conn, params=(id_emp,))

        if not datos_kpi.empty:
            k1, k2 = st.columns([1.8, 1.2])
            with k1:
                tabla = datos_kpi[["indicador", "meta", "proyectado", "real"]]
                st.dataframe(tabla, use_container_width=True, hide_index=True)

            with k2:
                meta = max(datos_kpi["meta"].sum(), 1)
                real = datos_kpi["real"].sum()
                pct = round((real / meta) * 100, 2)

                # Control para que el gráfico no rompa si supera el 100%
                val_cump = min(pct, 100)
                val_rest = max(100 - pct, 0)

                fig = go.Figure()
                fig.add_trace(go.Pie(
                    values=[val_cump, val_rest], 
                    hole=0.72,
                    marker=dict(colors=["#1aff74", "#172033"]),
                    textinfo="none",
                    hoverinfo="skip",
                    sort=False
                ))

                fig.update_layout(
                    height=200,
                    margin=dict(t=0, b=0, l=0, r=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False,
                    annotations=[dict(
                        text=f"<span style='font-size:28px; font-weight:800; color:#1aff74;'>{pct}%</span><br><span style='font-size:11px; font-weight:700; color:white;'>CUMPLIMIENTO</span>",
                        showarrow=False
                    )]
                )
                st.plotly_chart(fig, use_container_width=True, key=f"esc_donut_{id_emp}", config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

        # --- SECCIÓN GENERADOR QR INTEGRADA ---
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>🔑 CÓDIGO QR CREDENCIAL</div>", unsafe_allow_html=True)
        
        qr_bytes = generar_qr(empleado, datos_kpi)
        
        qc1, qc2 = st.columns([1, 2])
        with qc1:
            st.image(qr_bytes, width=180)
        with qc2:
            st.write("Esta credencial QR contiene la información del perfil del colaborador y sus métricas actuales consolidadas.")
            st.download_button(
                label="📥 Descargar Código QR",
                data=qr_bytes,
                file_name=f"QR_{id_emp}.png",
                mime="image/png"
            )
        st.markdown("</div>", unsafe_allow_html=True)


# CARGOS (CORREGIDO PARA EVITAR EL ERROR DE COLUMNAS)
# =========================================================
elif menu == "CARGOS":
    st.title("⚙️ GESTIÓN DE CARGOS")
    
    # 1. Formulario para agregar el cargo manualmente
    st.subheader("➕ Agregar Nuevo Cargo")
    with st.form("form_nuevo_cargo", clear_on_submit=True):
        nuevo_cargo = st.text_input("NOMBRE DEL NUEVO CARGO").upper().strip()
        
        if st.form_submit_button("AGREGAR CARGO"):
            if nuevo_cargo:
                # Comprobamos si el cargo ya existe
                existe = pd.read_sql("SELECT 1 FROM cargos WHERE nombre=?", conn, params=(nuevo_cargo,))
                if existe.empty:
                    # LÍNEA CORREGIDA: Pasamos el nombre del cargo Y un indicador por defecto ("RENDIMIENTO")
                    c.execute("INSERT INTO cargos VALUES (?, ?)", (nuevo_cargo, "RENDIMIENTO"))
                    conn.commit()
                    st.success(f"¡Cargo '{nuevo_cargo}' agregado con éxito!")
                    st.rerun()
                else:
                    st.error("Este cargo ya está registrado.")
            else:
                st.error("Por favor, introduce un nombre para el cargo.")

    st.markdown("---")

    # 2. Visor de KPIs por cargo y opción de añadir más
    st.subheader("📋 KPIs por Puesto")
    cargos = pd.read_sql("SELECT DISTINCT nombre FROM cargos", conn)
    
    if not cargos.empty:
        cargo_sel = st.selectbox("SELECCIONA UN CARGO", cargos["nombre"])
        
        kpis_puesto = pd.read_sql("SELECT indicador FROM cargos WHERE nombre=?", conn, params=(cargo_sel,))
        st.write("**KPIs actualmente vinculados:**", kpis_puesto["indicador"].tolist())
        
        nuevo_kpi = st.text_input("AÑADIR OTRO KPI A ESTE CARGO").upper().strip()
        if st.button("VINCULAR KPI"):
            if nuevo_kpi:
                # Evitamos duplicar el mismo KPI en el mismo cargo
                existe_kpi = pd.read_sql("SELECT 1 FROM cargos WHERE nombre=? AND indicador=?", conn, params=(cargo_sel, nuevo_kpi))
                if existe_kpi.empty:
                    c.execute("INSERT INTO cargos VALUES (?,?)", (cargo_sel, nuevo_kpi))
                    conn.commit()
                    st.success(f"¡KPI '{nuevo_kpi}' vinculado a '{cargo_sel}'!")
                    st.rerun()
                else:
                    st.warning("Este KPI ya está vinculado a este cargo.")
