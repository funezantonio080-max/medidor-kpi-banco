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

# =========================================================
# DASHBOARD EXECUTIVO PIXEL-PERFECT V10 (SOLUCIÓN TOTAL)
# =========================================================

if menu == "DASHBOARD":

    # Inyección de Estilos CSS Globales
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

    /* Encabezado Principal */
    .hdr-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    .hdr-logo {
        background: #09101a;
        border: 1px solid #00E676;
        box-shadow: 0px 0px 10px rgba(0, 230, 118, 0.3);
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 22px;
    }
    .hdr-title-box {
        text-align: center;
        flex-grow: 1;
    }
    .hdr-main-title {
        font-size: 28px;
        font-weight: 800;
        color: white;
        margin: 0;
    }
    .hdr-sub-title {
        color: #00E676;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .hdr-date-box {
        background-color: #0b131c;
        border: 1px solid #142334;
        border-radius: 8px;
        padding: 6px 12px;
        text-align: right;
    }

    /* Tarjetas Superiores */
    .top-card {
        background: #0b131c;
        border-radius: 10px;
        padding: 10px 12px;
        border: 1px solid #142334;
        display: flex;
        align-items: center;
        gap: 12px;
        height: 65px;
    }
    .top-icon-frame {
        font-size: 18px;
        background: rgba(0, 230, 118, 0.06);
        padding: 6px;
        border-radius: 6px;
        border: 1px solid rgba(0, 230, 118, 0.2);
        display: flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 34px;
    }
    .top-card-lbl { color: #7a8b9e; font-size: 10px; font-weight: 600; text-transform: uppercase; }
    .top-card-val { color: white; font-size: 18px; font-weight: 700; line-height: 1.1; }
    .top-card-desc { color: #4f6174; font-size: 10px; }

    /* Estructura Interna de Tarjetas de Gráficos */
    .kpi-main-frame {
        background: #09101a;
        border-radius: 14px;
        padding: 15px;
        border: 1px solid #142334;
        margin-bottom: 15px;
    }
    .kpi-frame-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
    }
    .kpi-frame-title-left {
        display: flex;
        align-items: center;
    }
    .badge-icon {
        background: rgba(0, 230, 118, 0.12);
        color: #00E676;
        padding: 2px 8px;
        border-radius: 5px;
        font-weight: 800;
        font-size: 13px;
        margin-right: 10px;
        border: 1px solid rgba(0, 230, 118, 0.25);
    }
    .title-text {
        color: white;
        font-size: 15px;
        font-weight: 700;
    }

    /* Filas de Datos y Leyendas */
    .data-align-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        font-size: 12.5px;
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
    
    .lbl-txt { color: #7a8b9e; font-weight: 600; }
    .val-txt { color: white; font-weight: 700; font-family: monospace; }

    /* Cuadro de Cumplimiento */
    .box-compliance {
        background: #0e1926;
        border: 1px solid #1a2d42;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        margin-top: 15px;
    }
    .box-comp-lbl { color: #7a8b9e; font-size: 11px; }
    .box-comp-val { color: #00E676; font-size: 20px; font-weight: 700; margin: 2px 0; }
    .box-comp-status { color: #00E676; font-size: 11px; font-weight: 600; }

    .bottom-note {
        text-align: center;
        color: #00E676;
        font-size: 10px;
        opacity: 0.6;
        margin-top: 15px;
    }

    .footer-container {
        display: flex;
        justify-content: space-between;
        padding-top: 12px;
        border-top: 1px solid #142334;
        color: #4f6174;
        font-size: 11px;
        margin-top: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Variables de base de datos SQL
    empleados = pd.read_sql("SELECT * FROM empleados", conn)
    kpis = pd.read_sql("SELECT * FROM kpis", conn)

    total_e = len(empleados)
    total_k = len(kpis)
    
    cump_gen = 0
    if not kpis.empty:
        cump_gen = round((kpis["real"].sum() / (kpis["meta"].sum() + 1)) * 100, 2)

    riesgo_k = 0
    if not kpis.empty:
        riesgo_k = len(kpis[kpis["real"] < kpis["meta"]])

    objetivo_k = max(total_k - riesgo_k, 0)
    fecha_actual = datetime.now().strftime("%d/%m/%Y")

    # 1. ENCABEZADO COMPLETO
    st.markdown(f"""
    <div class='hdr-container'>
        <div class='hdr-logo'>🏛️</div>
        <div class='hdr-title-box'>
            <h1 class='hdr-main-title'>DASHBOARD EJECUTIVO</h1>
            <div class='hdr-sub-title'>GERENCIA DE BANCO KPI</div>
        </div>
        <div class='hdr-date-box'>
            <span style='color:#7a8b9e; font-size:9px; display:block; font-weight:600;'>FECHA ACTUAL</span>
            <span style='color:white; font-size:12px; font-weight:700;'>📅 {fecha_actual}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. BLOQUES DE MÉTRICAS SUPERIORES
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown(f"<div class='top-card'><div class='top-icon-frame' style='color:#00E676;'>👥</div><div><div class='top-card-lbl'>Colaboradores</div><div class='top-card-val'>{total_e}</div><div class='top-card-desc'>Total Personal</div></div></div>", unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div class='top-card'><div class='top-icon-frame' style='color:#2196F3;'>📈</div><div><div class='top-card-lbl'>KPIs Activos</div><div class='top-card-val'>{total_k}</div><div class='top-card-desc'>Indicadores</div></div></div>", unsafe_allow_html=True)
    with m3:
        st.markdown(f"<div class='top-card'><div class='top-icon-frame' style='color:#00E676;'>🎯</div><div><div class='top-card-lbl'>Cumplimiento General</div><div class='top-card-val'>{cump_gen}%</div><div class='top-card-desc'>Promedio de Cumplimiento</div></div></div>", unsafe_allow_html=True)
    with m4:
        st.markdown(f"<div class='top-card'><div class='top-icon-frame' style='color:#00E676;'>✅</div><div><div class='top-card-lbl'>KPIs en Objetivo</div><div class='top-card-val'>{objetivo_k}</div><div class='top-card-desc'>Sin Riesgo</div></div></div>", unsafe_allow_html=True)
    with m5:
        color_alert = "#FFC107" if riesgo_k > 0 else "#7a8b9e"
        st.markdown(f"<div class='top-card'><div class='top-icon-frame' style='color:{color_alert};'>⚠️</div><div><div class='top-card-lbl'>KPIs en Riesgo</div><div class='top-card-val' style='color:{color_alert};'>{riesgo_k}</div><div class='top-card-desc'>Requieren Atención</div></div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. GENERACIÓN DE FILAS PARA LOS CUATRO GRÁFICOS
    for index in range(0, len(kpis), 2):
        chunk_kpis = kpis.iloc[index:index+2]
        columnas_dashboard = st.columns(2)

        for col_pos, (_, row) in enumerate(chunk_kpis.iterrows()):
            meta_val = max(row["meta"], 1)
            real_val = row["real"]
            proy_val = row["proyectado"]
            porcentaje_cump = round((real_val / meta_val) * 100, 2)

            # Adaptación dinámica de textos de la base de datos
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

            with columnas_dashboard[col_pos]:
                # Contenedor principal de la tarjeta (Abierto de forma segura)
                st.markdown(f"""
                <div class='kpi-main-frame'>
                    <div class='kpi-frame-header'>
                        <div class='kpi-frame-title-left'>
                            <span class='badge-icon'>{badge_sym}</span>
                            <span class='title-text'>{txt_indicador}</span>
                        </div>
                        <div style='color:#4f6174; font-weight:bold;'>•••</div>
                    </div>
                """, unsafe_allow_html=True)

                # Creamos las subcolumnas usando la API nativa de Streamlit para obligar el renderizado correcto
                col_grafico, col_datos = st.columns([1.1, 1.2])

                with col_grafico:
                    # Configuración exacta de la dona de dos colores (Verde brillante y verde oscuro)
                    val_cumplido = real_val if real_val <= meta_val else meta_val
                    val_restante = max(meta_val - real_val, 0)
                    
                    fig_donut = go.Figure()
                    fig_donut.add_trace(go.Pie(
                        values=[val_cumplido, val_restante],
                        hole=0.74,
                        textinfo="none",
                        hoverinfo="none",
                        marker=dict(colors=["#00E676", "#142c1b"]), # Dos tonos de verde idénticos a la referencia
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
                            text=f"<b style='font-size:20px;color:white;'>{porcentaje_cump}%</b><br><span style='font-size:10px;color:#7a8b9e;font-weight:600;'>Cumplimiento</span>",
                            showarrow=False,
                            font=dict(color="white")
                        )]
                    )
                    st.plotly_chart(fig_donut, use_container_width=True, key=f"v10_chart_{row['indicador']}")

                with col_datos:
                    # Formateadores de monedas y porcentajes
                    fmt = ",.2f"
                    suf = "%" if badge_sym == "%" else ""
                    pref = "C$ " if badge_sym == "$" else ""

                    # Bloque HTML de datos derecho - Inyectado con su parámetro correspondiente activado
                    st.markdown(f"""
                    <div>
                        <div class='data-align-row'>
                            <div><span class='bullet-dot b-meta'></span><span class='lbl-txt'>META</span></div>
                            <div class='val-txt'>{pref}{meta_val:{fmt}}{suf}</div>
                        </div>
                        <div class='data-align-row'>
                            <div><span class='bullet-dot b-proy'></span><span class='lbl-txt'>PROYECTADO</span></div>
                            <div class='val-txt'>{pref}{proy_val:{fmt}}{suf}</div>
                        </div>
                        <div class='data-align-row'>
                            <div><span class='bullet-dot b-real'></span><span class='lbl-txt'>REAL</span></div>
                            <div class='val-txt'>{pref}{real_val:{fmt}}{suf}</div>
                        </div>
                        
                        <div class='box-compliance'>
                            <div class='box-comp-lbl'>Cumplimiento</div>
                            <div class='box-comp-val'>{porcentaje_cump}%</div>
                            <div class='box-comp-status'>▲ Por encima de la meta</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                # Pie de la tarjeta y cierre definitivo del contenedor
                st.markdown(f"""
                    <div class='bottom-note'>{nota_unidad}</div>
                </div>
                """, unsafe_allow_html=True)

    # 4. FOOTER BASE DEL DASHBOARD
    st.markdown("""
    <div class='footer-container'>
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
