import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import qrcode
import json
from io import BytesIO

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

def generar_qr(data, kpis):
    contenido = {
        "id": data["id"],
        "nombre": data["nombre"],
        "cargo": data["cargo"],
        "kpis": kpis.to_dict(orient="records")
    }
    img = qrcode.make(json.dumps(contenido))
    buf = BytesIO()
    img.save(buf)
    return buf

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

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

import streamlit as st
import pandas as pd
from datetime import datetime

# =========================================================
# DASHBOARD CLON IDÉNTICO PIXEL-PERFECT (HTML/CSS PURO)
# =========================================================

if menu == "DASHBOARD":

    # Base de estilos CSS para calcar la interfaz de la foto
    st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 95% !important;
    }
    [data-testid="stAppViewContainer"] {
        background-color: #060b13 !important;
    }
    
    /* ENCABEZADO */
    .hdr-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 25px;
    }
    .hdr-logo {
        background: #09101a;
        border: 1px solid #00E676;
        box-shadow: 0px 0px 12px rgba(0, 230, 118, 0.3);
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 24px;
    }
    .hdr-title-box {
        text-align: center;
        flex-grow: 1;
    }
    .hdr-main-title {
        font-size: 32px;
        font-weight: 800;
        color: white;
        margin: 0;
        letter-spacing: 0.5px;
    }
    .hdr-sub-title {
        color: #00E676;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 1.5px;
        margin-top: 2px;
    }
    .hdr-date-box {
        background-color: #0b131c;
        border: 1px solid #142334;
        border-radius: 8px;
        padding: 8px 16px;
        text-align: right;
    }

    /* CONTENEDOR GRID DE TARJETAS FLUIDO */
    .grid-2-columnas {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        margin-bottom: 20px;
    }

    /* TARJETA DE INDICADOR COMPLETA */
    .kpi-card-clon {
        background: #09101a;
        border-radius: 14px;
        padding: 20px;
        border: 1px solid #142334;
        box-sizing: border-box;
    }
    .kpi-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    .kpi-title-left {
        display: flex;
        align-items: center;
    }
    .badge-unit-icon {
        background: rgba(0, 230, 118, 0.12);
        color: #00E676;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 800;
        font-size: 14px;
        margin-right: 12px;
        border: 1px solid rgba(0, 230, 118, 0.25);
    }
    .kpi-main-title {
        color: white;
        font-size: 16px;
        font-weight: 700;
    }
    
    /* CUERPO DE LA TARJETA (DONA + DATOS) */
    .kpi-split-body {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* DONA CSS PURA (Garantiza que no salgan cuadros negros) */
    .donut-css-box {
        position: relative;
        width: 190px;
        height: 190px;
        border-radius: 50%;
        background: conic-gradient(#00E676 0% 80%, #112217 80% 100%);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .donut-css-center {
        position: absolute;
        width: 140px;
        height: 140px;
        background: #09101a;
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    /* BLOQUE DERECHO DE DATOS */
    .split-right-data {
        width: 50%;
    }
    .row-item-data {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        font-size: 13px;
    }
    .bullet-dot {
        height: 8px;
        width: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
    }
    .b-meta { background-color: #2196F3; }
    .b-proy { background-color: #FFC107; }
    .b-real { background-color: #00E676; }
    
    .text-label { color: #7a8b9e; font-weight: 600; }
    .text-value { color: white; font-weight: 700; font-family: monospace; }

    /* CUADRO DE CUMPLIMIENTO INTERNO */
    .inner-compliance-container {
        background: #0e1926;
        border: 1px solid #1a2d42;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
        margin-top: 15px;
    }
    .compliance-label { color: #7a8b9e; font-size: 11px; }
    .compliance-value { color: #00E676; font-size: 22px; font-weight: 700; margin: 2px 0; }
    .compliance-status { color: #00E676; font-size: 11px; font-weight: 600; }

    .card-bottom-note {
        text-align: center;
        color: #00E676;
        font-size: 10.5px;
        opacity: 0.6;
        margin-top: 20px;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)

    # Variables de base de datos SQL
    empleados = pd.read_sql("SELECT * FROM empleados", conn)
    kpis = pd.read_sql("SELECT * FROM kpis", conn)

    total_empleados = len(empleados)
    total_kpis_activos = len(kpis)
    promedio_cumplimiento = round((kpis["real"].sum() / (kpis["meta"].sum() + 1)) * 100, 2) if not kpis.empty else 0
    kpis_en_riesgo = len(kpis[kpis["real"] < kpis["meta"]]) if not kpis.empty else 0
    kpis_en_objetivo = max(total_kpis_activos - kpis_en_riesgo, 0)
    fecha_hoy = datetime.now().strftime("%d/%m/%Y")

    # 1. RENDER DEL ENCABEZADO
    st.markdown(f"""
    <div class='hdr-container'>
        <div class='hdr-logo'>🏦</div>
        <div class='hdr-title-box'>
            <h1 class='hdr-main-title'>🏛️ DASHBOARD EJECUTIVO</h1>
            <div class='hdr-sub-title'>GERENCIA DE BANCO KPI</div>
        </div>
        <div class='hdr-date-box'>
            <span style='color:#7a8b9e; font-size:9px; display:block; font-weight:600;'>FECHA ACTUAL</span>
            <span style='color:white; font-size:12px; font-weight:700;'>📅 {fecha_hoy}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. SECCIÓN DE MÉTRICAS SUPERIORES INTERACTIVAS (Iguales a la foto)
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
         st.markdown(f"<div style='background:#0b131c; border-radius:10px; padding:12px; border:1px solid #142334; display:flex; align-items:center; gap:12px; height:65px;'><div style='font-size:20px; background:rgba(0,230,118,0.06); padding:6px; border-radius:6px; border:1px solid rgba(0,230,118,0.2); display:flex; align-items:center; justify-content:center; width:34px; height:34px; color:#00E676;'>👥</div><div><div style='color:#7a8b9e; font-size:10px; font-weight:600; text-transform:uppercase;'>Colaboradores</div><div style='color:white; font-size:19px; font-weight:700;'>{total_empleados}</div><div style='color:#4f6174; font-size:10px;'>Total Personal</div></div></div>", unsafe_allow_html=True)
    with m2:
         st.markdown(f"<div style='background:#0b131c; border-radius:10px; padding:12px; border:1px solid #142334; display:flex; align-items:center; gap:12px; height:65px;'><div style='font-size:20px; background:rgba(0,230,118,0.06); padding:6px; border-radius:6px; border:1px solid rgba(0,230,118,0.2); display:flex; align-items:center; justify-content:center; width:34px; height:34px; color:#2196F3;'>📈</div><div><div style='color:#7a8b9e; font-size:10px; font-weight:600; text-transform:uppercase;'>KPIs Activos</div><div style='color:white; font-size:19px; font-weight:700;'>{total_kpis_activos}</div><div style='color:#4f6174; font-size:10px;'>Indicadores</div></div></div>", unsafe_allow_html=True)
    with m3:
         st.markdown(f"<div style='background:#0b131c; border-radius:10px; padding:12px; border:1px solid #142334; display:flex; align-items:center; gap:12px; height:65px;'><div style='font-size:20px; background:rgba(0,230,118,0.06); padding:6px; border-radius:6px; border:1px solid rgba(0,230,118,0.2); display:flex; align-items:center; justify-content:center; width:34px; height:34px; color:#00E676;'>🎯</div><div><div style='color:#7a8b9e; font-size:10px; font-weight:600; text-transform:uppercase;'>Cumplimiento</div><div style='color:white; font-size:19px; font-weight:700;'>{promedio_cumplimiento}%</div><div style='color:#4f6174; font-size:10px;'>Promedio General</div></div></div>", unsafe_allow_html=True)
    with m4:
         st.markdown(f"<div style='background:#0b131c; border-radius:10px; padding:12px; border:1px solid #142334; display:flex; align-items:center; gap:12px; height:65px;'><div style='font-size:20px; background:rgba(0,230,118,0.06); padding:6px; border-radius:6px; border:1px solid rgba(0,230,118,0.2); display:flex; align-items:center; justify-content:center; width:34px; height:34px; color:#00E676;'>✅</div><div><div style='color:#7a8b9e; font-size:10px; font-weight:600; text-transform:uppercase;'>En Objetivo</div><div style='color:white; font-size:19px; font-weight:700;'>{kpis_en_objetivo}</div><div style='color:#4f6174; font-size:10px;'>Sin Riesgo</div></div></div>", unsafe_allow_html=True)
    with m5:
         c_r = "#FFC107" if kpis_en_riesgo > 0 else "#7a8b9e"
         st.markdown(f"<div style='background:#0b131c; border-radius:10px; padding:12px; border:1px solid #142334; display:flex; align-items:center; gap:12px; height:65px;'><div style='font-size:20px; background:rgba(0,230,118,0.06); padding:6px; border-radius:6px; border:1px solid rgba(0,230,118,0.2); display:flex; align-items:center; justify-content:center; width:34px; height:34px; color:{c_r};'>⚠️</div><div><div style='color:#7a8b9e; font-size:10px; font-weight:600; text-transform:uppercase;'>En Riesgo</div><div style='color:{c_r}; font-size:19px; font-weight:700;'>{kpis_en_riesgo}</div><div style='color:#4f6174; font-size:10px;'>Atención</div></div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. RENDER DE LAS TARJETAS PRINCIPALES EN HTML LIMPIO DESDE PYTHON
    # Esto une la dona y los datos en una sola estructura sólida sin fugas de código
    html_grid_completo = "<div class='grid-2-columnas'>"

    for idx, row in kpis.iterrows():
        meta_val = max(row["meta"], 1)
        real_val = row["real"]
        proy_val = row["proyectado"]
        porcentaje_cump = round((real_val / meta_val) * 100, 2)

        # Ajuste dinámico de etiquetas e íconos idénticos al prototipo
        badge_sym = "$"
        txt_indicador = f"{row['indicador']}"
        nota_unidad = "Valores expresados en CÓRDOBAS (C$)"

        if row["indicador"] == "RENTABILIDAD":
            txt_indicador = "RENTABILIDAD (Utilidad Generada)"
        elif row["indicador"] == "ROA":
            badge_sym = "%"
            txt_indicador = "ROA (Rendimiento sobre Activos)"
            nota_unidad = "Valores expresados en PORCENTAJE (%)"
        elif row["indicador"] == "ROE":
            badge_sym = "%"
            txt_indicador = "ROE (Rendimiento sobre Patrimonio)"
            nota_unidad = "Valores expresados en PORCENTAJE (%)"
        elif row["indicador"] == "LIQUIDEZ":
            txt_indicador = "LIQUIDEZ (Disponibilidad de Efectivo)"

        fmt = ",.2f"
        suf = "%" if badge_sym == "%" else ""
        pref = "C$ " if badge_sym == "$" else ""

        # Grados calculados dinámicamente para pintar la dona con CSS puro basado en el cumplimiento real
        grados_progreso = min(int((porcentaje_cump / 100) * 360), 360)

        # Inyección del bloque de la tarjeta en el string global
        html_grid_completo += f"""
        <div class='kpi-card-clon'>
            <div class='kpi-card-header'>
                <div class='kpi-title-left'>
                    <span class='badge-unit-icon'>{badge_sym}</span>
                    <span class='kpi-main-title'>{txt_indicador}</span>
                </div>
                <div style='color:#4f6174; font-weight:bold; font-size:14px;'>•••</div>
            </div>
            <div class='kpi-split-body'>
                <div class='donut-css-box' style='background: conic-gradient(#00E676 0deg {grados_progreso}deg, #112217 {grados_progreso}deg 360deg);'>
                    <div class='donut-css-center'>
                        <span style='font-size:22px; font-weight:800; color:white;'>{porcentaje_cump}%</span>
                        <span style='font-size:10px; color:#7a8b9e; font-weight:600; margin-top:2px;'>Cumplimiento</span>
                    </div>
                </div>
                
                <div class='split-right-data'>
                    <div class='row-item-data'>
                        <div><span class='bullet-dot b-meta'></span><span class='text-label'>META</span></div>
                        <div class='text-value'>{pref}{meta_val:{fmt}}{suf}</div>
                    </div>
                    <div class='row-item-data'>
                        <div><span class='bullet-dot b-proy'></span><span class='text-label'>PROYECTADO</span></div>
                        <div class='text-value'>{pref}{proy_val:{fmt}}{suf}</div>
                    </div>
                    <div class='row-item-data'>
                        <div><span class='bullet-dot b-real'></span><span class='text-label'>REAL</span></div>
                        <div class='text-value'>{pref}{real_val:{fmt}}{suf}</div>
                    </div>
                    
                    <div class='inner-compliance-container'>
                        <div class='compliance-label'>Cumplimiento</div>
                        <div class='compliance-value'>{porcentaje_cump}%</div>
                        <div class='compliance-status'>▲ Por encima de la meta</div>
                    </div>
                </div>
            </div>
            <div class='card-bottom-note'>{nota_unidad}</div>
        </div>
        """

    html_grid_completo += "</div>"

    # Pintamos todas las tarjetas empaquetadas juntas de forma segura con un único comando
    st.markdown(html_grid_completo, unsafe_allow_html=True)

    # 4. FOOTER INSTITUCIONAL BASE
    st.markdown("""
    <div style='display:flex; justify-content:between; padding-top:12px; border-top:1px solid #142334; color:#4f6174; font-size:11px; margin-top:15px; width:100%;'>
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
        kpis = pd.read_sql("SELECT * FROM kpis WHERE id=?", conn, params=(emp_id,))

        for i, row in kpis.iterrows():
            st.subheader(row["indicador"])

            col1, col2, col3 = st.columns(3)

            with col1:
                m = st.number_input("META", value=row["meta"], key=f"m{i}")
            with col2:
                p = st.number_input("PROYECTADO", value=row["proyectado"], key=f"p{i}")
            with col3:
                r = st.number_input("REAL", value=row["real"], key=f"r{i}")

            if st.button(f"GUARDAR {row['indicador']}"):
                c.execute("""
                UPDATE kpis SET meta=?, real=?, proyectado=?
                WHERE id=? AND indicador=?
                """, (m,r,p,emp_id,row["indicador"]))
                conn.commit()

# =========================================================
# ESCÁNER (CON GRÁFICOS)
# =========================================================
elif menu == "ESCÁNER":
    st.title("🔍 ESCÁNER")

    df = pd.read_sql("SELECT * FROM empleados", conn)

    if not df.empty:
        df["display"] = df["id"] + " - " + df["nombre"] + " - " + df["cargo"]

        sel = st.selectbox("SELECCIONAR", df["display"])
        emp_id = df[df["display"] == sel]["id"].values[0]

        data = df[df["id"] == emp_id].iloc[0]
        kpis = pd.read_sql("SELECT * FROM kpis WHERE id=?", conn, params=(emp_id,))

        col1, col2 = st.columns([1,2])

        with col1:
            st.dataframe(mayus(pd.DataFrame([data]).drop(columns=["foto"], errors="ignore")))

            if data["foto"]:
                st.image(data["foto"], width=140)

            st.image(generar_qr(data,kpis), width=140)

        with col2:
            st.dataframe(mayus(kpis))

            for i, row in kpis.iterrows():

                labels = ["META","PROYECTADO","REAL"]
                valores = [row["meta"], row["proyectado"], row["real"]]

                fig = go.Figure()

                fig.add_trace(go.Bar(
                    x=labels,
                    y=valores,
                    marker=dict(color=["#A8D5BA","#7FB77E","#4CAF50"]),
                    width=0.25
                ))

                fig.add_trace(go.Scatter(
                    x=labels,
                    y=valores,
                    mode="lines+markers",
                    showlegend=False
                ))

                st.plotly_chart(fig, key=f"graf_{i}")

# =========================================================
# CARGOS
# =========================================================
elif menu == "CARGOS":
    st.title("⚙️ CARGOS")

    cargos = pd.read_sql("SELECT DISTINCT nombre FROM cargos", conn)
    cargo_sel = st.selectbox("CARGO", cargos["nombre"])

    kpis = pd.read_sql("SELECT indicador FROM cargos WHERE nombre=?", conn, params=(cargo_sel,))
    st.write("KPIs:", kpis["indicador"].tolist())

    nuevo = st.text_input("NUEVO KPI")

    if st.button("AGREGAR"):
        c.execute("INSERT INTO cargos VALUES (?,?)",(cargo_sel,nuevo.upper()))
        conn.commit()

    eliminar = st.selectbox("ELIMINAR KPI", kpis["indicador"])

    if st.button("ELIMINAR"):
        c.execute("DELETE FROM cargos WHERE nombre=? AND indicador=?",(cargo_sel,eliminar))
        conn.commit()
