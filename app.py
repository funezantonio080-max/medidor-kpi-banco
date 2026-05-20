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
# DASHBOARD PREMIUM PIXEL-PERFECT V5
# =========================================================

if menu == "DASHBOARD":

    # Inyección de CSS Avanzado para calcar la imagen de referencia
    st.markdown("""
    <style>
    /* Reset de contenedor de Streamlit */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 95%;
    }
    
    body {
        background-color: #060b13;
    }

    /* Encabezado */
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
        margin-bottom: 2px;
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
        padding: 15px;
        border: 1px solid #152535;
        display: flex;
        align-items: center;
        gap: 15px;
        height: 85px;
    }
    .top-icon-container {
        font-size: 24px;
        background: rgba(0, 230, 118, 0.08);
        padding: 10px;
        border-radius: 8px;
        border: 1px solid rgba(0, 230, 118, 0.2);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .top-card-title {
        color: #7a8b9e;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
    }
    .top-card-value {
        color: white;
        font-size: 22px;
        font-weight: 700;
    }
    .top-card-sub {
        color: #4f6174;
        font-size: 11px;
    }

    /* Tarjetas de Indicadores (Grid Principal) */
    .kpi-main-card {
        background: #09101a;
        border-radius: 16px;
        padding: 22px;
        border: 1px solid #142334;
        margin-bottom: 20px;
        height: 440px;
        position: relative;
    }
    .kpi-card-header {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
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
        font-size: 18px;
        font-weight: 700;
    }
    .kpi-card-subtitle {
        color: #7a8b9e;
        font-size: 14px;
        font-weight: 400;
    }

    /* Filas de Datos Leyenda Derecha */
    .data-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        font-size: 14px;
    }
    .dot {
        height: 10px;
        width: 10px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
    }
    .dot-meta { background-color: #2196F3; }
    .dot-proy { background-color: #FFC107; }
    .dot-real { background-color: #00E676; }
    
    .lbl-text { color: #a0aec0; }
    .val-text { color: white; font-weight: 600; font-family: monospace; }

    /* Cuadro de cumplimiento interno derecho */
    .comp-inner-box {
        background: #0e1926;
        border: 1px solid #1a2d42;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        margin-top: 20px;
    }
    .comp-inner-title {
        color: #7a8b9e;
        font-size: 12px;
    }
    .comp-inner-val {
        color: #00E676;
        font-size: 24px;
        font-weight: 700;
    }
    .comp-inner-status {
        color: #00E676;
        font-size: 12px;
        margin-top: 4px;
    }

    /* Nota al pie de tarjeta */
    .kpi-footer-note {
        text-align: center;
        color: #00E676;
        font-size: 11px;
        opacity: 0.8;
        position: absolute;
        bottom: 15px;
        width: 90%;
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

    # Lectura de Datos desde SQLite
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

    # 1. HEADER SUPERIOR REPLICADO
    st.markdown(f"""
    <div class='header-container'>
        <div style='font-size: 32px;'>🏦</div>
        <div class='header-title-box'>
            <div class='main-title'>🏛️ DASHBOARD EJECUTIVO</div>
            <div class='sub-title'>GERENCIA DE BANCO KPI</div>
        </div>
        <div class='date-box'>
            <span style='color:#7a8b9e; font-size:10px; display:block;'>FECHA ACTUAL</span>
            <span style='color:white; font-size:14px; font-weight:700;'>📅 {fecha_actual}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. BLOQUE DE 5 MÉTRICAS GENERALES SUPERIORES
    a, b, c, d, e = st.columns(5)
    
    with a:
        st.markdown(f"<div class='top-card'><div class='top-icon-container' style='color:#00E676;'>👥</div><div><div class='top-card-title'>Colaboradores</div><div class='top-card-value'>{total}</div><div class='top-card-sub'>Total Personal</div></div></div>", unsafe_allow_html=True)
    with b:
        st.markdown(f"<div class='top-card'><div class='top-icon-container' style='color:#2196F3;'>📈</div><div><div class='top-card-title'>KPIs Activos</div><div class='top-card-value'>{total_kpi}</div><div class='top-card-sub'>Indicadores</div></div></div>", unsafe_allow_html=True)
    with c:
        st.markdown(f"<div class='top-card'><div class='top-icon-container' style='color:#00E676;'>🎯</div><div><div class='top-card-title'>Cumplimiento General</div><div class='top-card-value'>{cumplimiento}%</div><div class='top-card-sub'>Promedio de Cumplimiento</div></div></div>", unsafe_allow_html=True)
    with d:
        st.markdown(f"<div class='top-card'><div class='top-icon-container' style='color:#00E676;'>🛡️</div><div><div class='top-card-title'>KPIs en Objetivo</div><div class='top-card-value'>{objetivo}</div><div class='top-card-sub'>Sin Riesgo</div></div></div>", unsafe_allow_html=True)
    with e:
        # Si hay riesgo se pone amarillo, si no, se queda apagado igual que en la foto de referencia
        color_riesgo = "#FFC107" if riesgo > 0 else "#7a8b9e"
        st.markdown(f"<div class='top-card'><div class='top-icon-container' style='color:{color_riesgo};'>⚠️</div><div><div class='top-card-title'>KPIs en Riesgo</div><div class='top-card-value' style='color:{color_riesgo};'>{riesgo}</div><div class='top-card-sub'>Requieren Atención</div></div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. CONSTRUCCIÓN DE LA CUADRÍCULA (GRID 2x2) DE CONTENEDORES PRINCIPALES
    # Iteramos los KPIs de la BD en bloques de dos para generar filas perfectas
    for i in range(0, len(kpis), 2):
        fila_kpis = kpis.iloc[i:i+2]
        cols_pantalla = st.columns(2)

        for col, (_, row) in zip(cols_pantalla, fila_kpis.iterrows()):
            meta = max(row["meta"], 1)
            real = row["real"]
            proy = row["proyectado"]
            comp = round((real / meta) * 100, 2)

            # Configuraciones dinámicas de nombres y formatos según la imagen
            badge_icon = "$"
            nombre_extendido = ""
            signo_unidad = ""
            nota_pie = "Valores expresados en CÓRDOBAS (C$)"

            if row["indicador"] == "RENTABILIDAD":
                nombre_extendido = "RENTABILIDAD (Utilidad Generada)"
            elif row["indicador"] == "ROA":
                badge_icon = "%"
                nombre_extendido = "ROA (Rendimiento sobre Activos)"
                nota_pie = "Valores expresados en PORCENTAJE (%)"
            elif row["indicador"] == "ROE":
                badge_icon = "%"
                nombre_extendido = "ROE (Rendimiento sobre Patrimonio)"
                nota_pie = "Valores expresados en PORCENTAJE (%)"
            elif row["indicador"] == "LIQUIDEZ":
                nombre_extendido = "LIQUIDEZ (Disponibilidad de Efectivo)"
            else:
                nombre_extendido = f"{row['indicador']}"

            with col:
                # Apertura de la tarjeta contenedora externa
                st.markdown(f"""
                <div class='kpi-main-card'>
                    <div class='kpi-card-header'>
                        <span class='kpi-badge-icon'>{badge_icon}</span>
                        <span class='kpi-card-title'>{nombre_extendido}</span>
                    </div>
                """, unsafe_allow_html=True)

                # Divisiones internas: Gráfico (Izquierda) y Tabla/Estatus (Derecha)
                l_inner, r_inner = st.columns([1.3, 1.2])

                with l_inner:
                    # Render de la Dona usando la paleta exacta de degradados verdes de tu imagen
                    # Si excede el 100%, rellenamos la dona completa de verde brillante
                    valores_donat = [real, max(meta - real, 0)] if real <= meta else [100, 0]
                    colores_donat = ["#00E676", "#11291b"] if real <= meta else ["#7C4DFF" if comp > 110 else "#00E676", "#11291b"]

                    # Ajuste fino basado en la imagen: si el cumplimiento es muy alto, usamos tonalidades vivas
                    if comp > 100:
                        colores_donat = ["#00E676", "#81C784"] 

                    donut = go.Figure()
                    donut.add_trace(go.Pie(
                        values=valores_donat,
                        hole=0.70,
                        textinfo="none",
                        hoverinfo="none",
                        marker=dict(colors=colores_donat),
                        direction="clockwise"
                    ))

                    donut.update_layout(
                        height=240,
                        margin=dict(t=5, b=5, l=5, r=5),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        showlegend=False,
                        annotations=[dict(
                            text=f"<b style='font-size:24px;color:white;'>{comp}%</b><br><span style='font-size:11px;color:#7a8b9e;font-weight:600;'>Cumplimiento</span>",
                            showarrow=False,
                            font=dict(color="white")
                        )]
                    )

                    st.plotly_chart(donut, use_container_width=True, key=f"chart_premium_{row['indicador']}")

                with r_inner:
                    # Mapeo de formatos numéricos limpios ($ o %)
                    fmt = ",.2f"
                    sufijo = "%" if badge_icon == "%" else ""
                    prefijo = "C$ " if badge_icon == "$" else ""

                    # Bloque HTML con las filas alineadas de la leyenda personalizada
                    st.markdown(f"""
                    <div style='margin-top:10px;'>
                        <div class='data-row'>
                            <div><span class='dot dot-meta'></span><span class='lbl-text'>META</span></div>
                            <div class='val-text'>{prefijo}{meta:{fmt}}{sufijo}</div>
                        </div>
                        <div class='data-row'>
                            <div><span class='dot dot-proy'></span><span class='lbl-text'>PROYECTADO</span></div>
                            <div class='val-text'>{prefijo}{proy:{fmt}}{sufijo}</div>
                        </div>
                        <div class='data-row'>
                            <div><span class='dot dot-real'></span><span class='lbl-text'>REAL</span></div>
                            <div class='val-text'>{prefijo}{real:{fmt}}{sufijo}</div>
                        </div>
                    </div>
                    
                    <div class='comp-inner-box'>
                        <div class='comp-inner-title'>Cumplimiento</div>
                        <div class='comp-inner-val'>{comp}%</div>
                        <div class='comp-inner-status'>▲ Por encima de la meta</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Nota aclaratoria y etiqueta de cierre absoluto
                st.markdown(f"""
                    <div class='kpi-footer-note'>{nota_pie}</div>
                </div>
                """, unsafe_allow_html=True)

    # 4. FOOTER INSTITUCIONAL DE LA BASE DE LA IMAGEN
    st.markdown("""
    <div class='footer-bar'>
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
