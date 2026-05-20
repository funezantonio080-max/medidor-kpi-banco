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

# =========================================================
# DASHBOARD PREMIUM PIXEL-PERFECT V6 (CORRECCIÓN DE REPOSITORIO Y ALTURAS)
# =========================================================

if menu == "DASHBOARD":

    # CSS Avanzado corregido para evitar cortes y vacíos
    st.markdown("""
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1rem;
        max-width: 95%;
    }
    
    body {
        background-color: #060b13;
    }

    /* Encabezado Principal */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 25px;
    }
    .header-title-box {
        text-align: center;
        flex-grow: 1;
    }
    .main-title {
        font-size: 32px;
        font-weight: 700;
        color: white;
        letter-spacing: 0.5px;
    }
    .sub-title {
        color: #00E676;
        font-size: 14px;
        font-weight: 600;
        letter-spacing: 1px;
    }
    .date-box {
        background-color: #0f1922;
        border: 1px solid #1c2e3d;
        border-radius: 8px;
        padding: 8px 15px;
        text-align: right;
    }

    /* Bloques Superiores KPI */
    .top-card {
        background: #0b131c;
        border-radius: 12px;
        padding: 12px 15px;
        border: 1px solid #152535;
        display: flex;
        align-items: center;
        gap: 15px;
        height: 75px;
    }
    .top-icon-container {
        font-size: 22px;
        background: rgba(0, 230, 118, 0.08);
        padding: 8px;
        border-radius: 8px;
        border: 1px solid rgba(0, 230, 118, 0.2);
        display: flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
    }
    .top-card-title {
        color: #7a8b9e;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
    }
    .top-card-value {
        color: white;
        font-size: 20px;
        font-weight: 700;
        line-height: 1.2;
    }
    .top-card-sub {
        color: #4f6174;
        font-size: 11px;
    }

    /* Tarjetas de Indicadores (Grid Principal) */
    .kpi-main-card {
        background: #09101a;
        border-radius: 16px;
        padding: 20px;
        border: 1px solid #142334;
        margin-bottom: 20px;
        height: 360px; /* Altura corregida para evitar espacios vacíos gigantes */
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .kpi-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 5px;
    }
    .kpi-title-left {
        display: flex;
        align-items: center;
    }
    .kpi-badge-icon {
        background: rgba(0, 230, 118, 0.15);
        color: #00E676;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 14px;
        margin-right: 12px;
    }
    .kpi-card-title {
        color: white;
        font-size: 17px;
        font-weight: 700;
    }
    
    /* Contenedor Flex para alinear Gráfico y Datos en paralelo */
    .kpi-body-flex {
        display: flex;
        justify-content: space-between;
        align-items: center;
        height: 260px;
    }
    .chart-side {
        width: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .data-side {
        width: 48%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    /* Filas de Datos Leyenda Derecha */
    .data-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        font-size: 13px;
    }
    .dot {
        height: 9px;
        width: 9px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
    }
    .dot-meta { background-color: #2196F3; }
    .dot-proy { background-color: #FFC107; }
    .dot-real { background-color: #00E676; }
    
    .lbl-text { color: #7a8b9e; font-weight: 500; }
    .val-text { color: white; font-weight: 600; font-family: monospace; }

    /* Cuadro de cumplimiento interno derecho */
    .comp-inner-box {
        background: #0e1926;
        border: 1px solid #1a2d42;
        border-radius: 12px;
        padding: 12px;
        text-align: center;
        margin-top: 10px;
    }
    .comp-inner-title {
        color: #7a8b9e;
        font-size: 11px;
    }
    .comp-inner-val {
        color: #00E676;
        font-size: 22px;
        font-weight: 700;
    }
    .comp-inner-status {
        color: #00E676;
        font-size: 11px;
        margin-top: 2px;
        font-weight: 500;
    }

    /* Nota al pie de tarjeta */
    .kpi-footer-note {
        text-align: center;
        color: #00E676;
        font-size: 11px;
        opacity: 0.7;
        margin-top: 5px;
    }

    /* Footer Institucional */
    .footer-bar {
        display: flex;
        justify-content: space-between;
        padding: 15px 0;
        border-top: 1px solid #142334;
        color: #4f6174;
        font-size: 12px;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Datos (Simulados o de tu consulta SQL activa)
    empleados = pd.read_sql("SELECT * FROM empleados", conn)
    kpis = pd.read_sql("SELECT * FROM kpis", conn)

    total = len(empleados)
    total_kpi = len(kpis)
    cumplimiento = 0
    if not kpis.empty:
        cumplimiento = round((kpis["real"].sum() / (kpis["meta"].sum() + 1)) * 100, 2)

    riesgo = 0
    if not kpis.empty:
        riesgo = len(kpis[kpis["real"] < kpis["meta"]])

    objetivo = max(total_kpi - riesgo, 0)
    fecha_actual = datetime.now().strftime("%d/%m/%Y")

    # 1. HEADER SUPERIOR
    st.markdown(f"""
    <div class='header-container'>
        <div style='font-size: 32px;'>🏛️</div>
        <div class='header-title-box'>
            <div class='main-title'>DASHBOARD EJECUTIVO</div>
            <div class='sub-title'>GERENCIA DE BANCO KPI</div>
        </div>
        <div class='date-box'>
            <span style='color:#7a8b9e; font-size:10px; display:block;'>FECHA ACTUAL</span>
            <span style='color:white; font-size:13px; font-weight:700;'>📅 {fecha_actual}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. BLOQUE DE METRICAS SUPERIORES
    a, b, c, d, e = st.columns(5)
    with a:
        st.markdown(f"<div class='top-card'><div class='top-icon-container'>👥</div><div><div class='top-card-title'>Colaboradores</div><div class='top-card-value'>{total}</div><div class='top-card-sub'>Total Personal</div></div></div>", unsafe_allow_html=True)
    with b:
        st.markdown(f"<div class='top-card'><div class='top-icon-container'>📈</div><div><div class='top-card-title'>KPIs Activos</div><div class='top-card-value'>{total_kpi}</div><div class='top-card-sub'>Indicadores</div></div></div>", unsafe_allow_html=True)
    with c:
        st.markdown(f"<div class='top-card'><div class='top-icon-container'>🎯</div><div><div class='top-card-title'>Cumplimiento General</div><div class='top-card-value'>{cumplimiento}%</div><div class='top-card-sub'>Promedio de Cumplimiento</div></div></div>", unsafe_allow_html=True)
    with d:
        st.markdown(f"<div class='top-
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
