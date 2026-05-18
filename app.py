# =========================================================
# GERENCIA DE BANCO KPI
# SISTEMA EJECUTIVO KPI BANCARIO
# =========================================================

import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import qrcode
from PIL import Image
import io
import base64
from datetime import datetime

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="GERENCIA DE BANCO KPI",
    page_icon="🏦",
    layout="wide"
)

# =========================================================
# PORTADA / FONDO EJECUTIVO
# =========================================================

def get_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

img = get_base64("portada.png")

page_bg = f"""
<style>

[data-testid="stAppViewContainer"] {{
    background-image:
    linear-gradient(rgba(0,0,0,0.75),
    rgba(0,0,0,0.75)),
    url("data:image/png;base64,{img}");

    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}}

[data-testid="stHeader"] {{
    background: rgba(0,0,0,0);
}}

[data-testid="stSidebar"] {{
    background: rgba(5,15,35,0.90);
    backdrop-filter: blur(10px);
}}

.block-container {{
    padding-top: 1rem;
}}

h1,h2,h3,h4,h5,h6,p,label,div {{
    color:white !important;
}}

.stButton>button {{
    width:100%;
    border-radius:12px;
    height:45px;
    background:linear-gradient(90deg,#0d6efd,#00c6ff);
    color:white;
    border:none;
    font-size:16px;
    font-weight:bold;
}}

.stButton>button:hover {{
    transform:scale(1.02);
}}

.card {{
    background: rgba(10,20,40,0.88);
    border-radius: 18px;
    padding: 20px;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 0 15px rgba(0,0,0,0.4);
}}

.metric-card {{
    background: linear-gradient(145deg,#07162e,#0b2347);
    padding:20px;
    border-radius:16px;
    text-align:center;
    border:1px solid rgba(255,255,255,0.08);
}}

.metric-title {{
    font-size:18px;
    color:#bfc9d4;
}}

.metric-value {{
    font-size:38px;
    font-weight:bold;
    color:#00ffcc;
}}

</style>
"""

st.markdown(page_bg, unsafe_allow_html=True)

# =========================================================
# TITULO PRINCIPAL
# =========================================================

st.markdown("""
<h1 style='text-align:center;
font-size:55px;
font-weight:bold;
margin-bottom:0;'>
🏦 GERENCIA DE BANCO KPI
</h1>
""", unsafe_allow_html=True)

st.markdown("""
<h4 style='text-align:center;
color:#d9d9d9;
margin-top:0;'>
CENTRO EJECUTIVO DE INDICADORES BANCARIOS
</h4>
""", unsafe_allow_html=True)

# =========================================================
# DATABASE
# =========================================================

conn = sqlite3.connect("banco_kpi.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS empleados(
id TEXT PRIMARY KEY,
nombre TEXT,
edad TEXT,
estado TEXT,
profesion TEXT,
cargo TEXT,
foto BLOB
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS indicadores(
id_empleado TEXT,
indicador TEXT,
meta REAL,
proyectado REAL,
real REAL
)
""")

conn.commit()

# =========================================================
# SIDEBAR
# =========================================================

menu = st.sidebar.radio(
    "MENU",
    [
        "DASHBOARD",
        "REGISTRAR",
        "EMPLEADOS",
        "ESCANER"
    ]
)

# =========================================================
# DASHBOARD
# =========================================================

if menu == "DASHBOARD":

    total_emp = pd.read_sql("SELECT * FROM empleados", conn)

    total_kpi = pd.read_sql("SELECT * FROM indicadores", conn)

    col1,col2,col3,col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">COLABORADORES</div>
            <div class="metric-value">{len(total_emp)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">KPIs</div>
            <div class="metric-value">{len(total_kpi)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        promedio = round(total_kpi["real"].mean(),2) if not total_kpi.empty else 0

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">PROMEDIO REAL</div>
            <div class="metric-value">{promedio}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">FECHA</div>
            <div class="metric-value" style="font-size:20px;">
            {datetime.now().strftime("%d/%m/%Y")}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.subheader("📊 KPIs GENERALES")

    if not total_kpi.empty:

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=total_kpi["indicador"],
            y=total_kpi["meta"],
            name="META",
            marker_color="#0066ff",
            width=0.20
        ))

        fig.add_trace(go.Bar(
            x=total_kpi["indicador"],
            y=total_kpi["proyectado"],
            name="PROYECTADO",
            marker_color="#00cc99",
            width=0.20
        ))

        fig.add_trace(go.Bar(
            x=total_kpi["indicador"],
            y=total_kpi["real"],
            name="REAL",
            marker_color="#00ffcc",
            width=0.20
        ))

        fig.update_layout(
            barmode="group",
            height=600,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white")
        )

        st.plotly_chart(fig, use_container_width=True)

# =========================================================
# REGISTRAR
# =========================================================

elif menu == "REGISTRAR":

    st.subheader("👨‍💼 REGISTRAR EMPLEADO")

    with st.form("registro"):

        col1,col2 = st.columns(2)

        with col1:
            id_emp = st.text_input("ID")
            nombre = st.text_input("NOMBRE")
            edad = st.text_input("EDAD")

        with col2:
            estado = st.text_input("ESTADO CIVIL")
            profesion = st.text_input("PROFESION")
            cargo = st.text_input("CARGO")

        foto = st.file_uploader("FOTO", type=["png","jpg","jpeg"])

        st.markdown("### KPIs")

        indicadores = []

        for i in range(3):

            st.markdown(f"#### KPI {i+1}")

            ind = st.text_input(f"INDICADOR {i}", key=f"ind{i}")
            meta = st.number_input(f"META {i}", key=f"m{i}")
            proy = st.number_input(f"PROYECTADO {i}", key=f"p{i}")
            real = st.number_input(f"REAL {i}", key=f"r{i}")

            indicadores.append([ind,meta,proy,real])

        guardar = st.form_submit_button("GUARDAR")

        if guardar:

            foto_bytes = foto.read() if foto else None

            c.execute("""
            INSERT OR REPLACE INTO empleados
            VALUES(?,?,?,?,?,?,?)
            """,(
                id_emp,
                nombre,
                edad,
                estado,
                profesion,
                cargo,
                foto_bytes
            ))

            c.execute("DELETE FROM indicadores WHERE id_empleado=?",(id_emp,))

            for x in indicadores:

                c.execute("""
                INSERT INTO indicadores
                VALUES(?,?,?,?,?)
                """,(
                    id_emp,
                    x[0],
                    x[1],
                    x[2],
                    x[3]
                ))

            conn.commit()

            st.success("EMPLEADO REGISTRADO")

# =========================================================
# EMPLEADOS
# =========================================================

elif menu == "EMPLEADOS":

    st.subheader("👥 EMPLEADOS")

    df = pd.read_sql("SELECT * FROM empleados", conn)

    st.dataframe(df)

# =========================================================
# ESCANER
# =========================================================

elif menu == "ESCANER":

    st.subheader("📺 PANEL EJECUTIVO KPI")

    empleados = pd.read_sql("SELECT * FROM empleados", conn)

    if not empleados.empty:

        empleados["mostrar"] = (
            empleados["id"] +
            " - " +
            empleados["nombre"] +
            " - " +
            empleados["cargo"]
        )

        seleccionado = st.selectbox(
            "SELECCIONAR EMPLEADO",
            empleados["mostrar"]
        )

        emp_id = seleccionado.split(" - ")[0]

        data = pd.read_sql(
            f"SELECT * FROM empleados WHERE id='{emp_id}'",
            conn
        ).iloc[0]

        kpis = pd.read_sql(
            f"SELECT * FROM indicadores WHERE id_empleado='{emp_id}'",
            conn
        )

        col1,col2 = st.columns([1,2])

        with col1:

            st.markdown('<div class="card">', unsafe_allow_html=True)

            if data["foto"]:

                image = Image.open(io.BytesIO(data["foto"]))
                st.image(image, use_container_width=True)

            st.markdown(f"""
            ### {data["nombre"].upper()}
            #### {data["cargo"].upper()}
            """)

            st.write("**ID:**", data["id"])
            st.write("**EDAD:**", data["edad"])
            st.write("**ESTADO CIVIL:**", data["estado"])
            st.write("**PROFESION:**", data["profesion"])

            st.markdown('</div>', unsafe_allow_html=True)

        with col2:

            st.markdown("""
            <div class="card">
            <h2 style='text-align:center;'>
            📺 GERENCIA DE BANCO KPI
            </h2>
            </div>
            """, unsafe_allow_html=True)

            if not kpis.empty:

                fig = go.Figure()

                fig.add_trace(go.Bar(
                    x=kpis["indicador"],
                    y=kpis["meta"],
                    name="META",
                    marker_color="#0066ff",
                    width=0.20
                ))

                fig.add_trace(go.Bar(
                    x=kpis["indicador"],
                    y=kpis["proyectado"],
                    name="PROYECTADO",
                    marker_color="#00cc99",
                    width=0.20
                ))

                fig.add_trace(go.Bar(
                    x=kpis["indicador"],
                    y=kpis["real"],
                    name="REAL",
                    marker_color="#00ffcc",
                    width=0.20
                ))

                fig.update_layout(
                    barmode="group",
                    height=550,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="white")
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

                st.dataframe(kpis)
