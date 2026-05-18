# =========================================================
# GERENCIA DE BANCO KPI
# SISTEMA EJECUTIVO BANCARIO
# =========================================================

import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
from PIL import Image
import io
import base64
import os
from datetime import datetime

# =========================================================
# CONFIGURACION
# =========================================================

st.set_page_config(
    page_title="GERENCIA DE BANCO KPI",
    page_icon="🏦",
    layout="wide"
)

# =========================================================
# FUNCION BASE64
# =========================================================

def get_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# =========================================================
# FONDO EJECUTIVO
# =========================================================

ruta_imagen = "portada.png"

img = ""

if os.path.exists(ruta_imagen):
    img = get_base64(ruta_imagen)

if img != "":

    fondo = f"""
    <style>

    [data-testid="stAppViewContainer"] {{
        background-image:
        linear-gradient(
        rgba(0,0,0,0.78),
        rgba(0,0,0,0.78)),
        url("data:image/png;base64,{img}");

        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}

    </style>
    """

else:

    fondo = """
    <style>

    [data-testid="stAppViewContainer"] {
        background: linear-gradient(
        135deg,
        #06121f,
        #0b2340,
        #06121f
        );
    }

    </style>
    """

st.markdown(fondo, unsafe_allow_html=True)

# =========================================================
# ESTILOS GENERALES
# =========================================================

st.markdown("""
<style>

[data-testid="stHeader"]{
    background: rgba(0,0,0,0);
}

[data-testid="stSidebar"]{
    background: rgba(5,15,35,0.92);
    backdrop-filter: blur(10px);
}

.block-container{
    padding-top: 1rem;
}

h1,h2,h3,h4,h5,h6,p,label,div{
    color:white !important;
}

.stButton>button{
    width:100%;
    border-radius:14px;
    height:48px;
    border:none;
    font-size:16px;
    font-weight:bold;
    color:white;
    background:linear-gradient(90deg,#0d6efd,#00c6ff);
}

.stButton>button:hover{
    transform:scale(1.02);
}

.metric-card{
    background:rgba(10,20,40,0.90);
    padding:25px;
    border-radius:18px;
    border:1px solid rgba(255,255,255,0.08);
    text-align:center;
    box-shadow:0 0 18px rgba(0,0,0,0.5);
}

.metric-title{
    color:#c7d0d9;
    font-size:18px;
}

.metric-value{
    font-size:40px;
    font-weight:bold;
    color:#00ffcc;
}

.panel{
    background:rgba(10,20,40,0.90);
    padding:20px;
    border-radius:18px;
    border:1px solid rgba(255,255,255,0.08);
    box-shadow:0 0 15px rgba(0,0,0,0.4);
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# TITULO
# =========================================================

st.markdown("""
<h1 style='text-align:center;
font-size:52px;
font-weight:bold;
margin-bottom:0;'>
🏦 GERENCIA DE BANCO KPI
</h1>
""", unsafe_allow_html=True)

st.markdown("""
<h4 style='text-align:center;
margin-top:0;
color:#d9d9d9;'>
CENTRO EJECUTIVO DE INDICADORES BANCARIOS
</h4>
""", unsafe_allow_html=True)

# =========================================================
# BASE DE DATOS
# =========================================================

conn = sqlite3.connect("banco_kpi.db", check_same_thread=False)
c = conn.cursor()

# =========================================================
# TABLA EMPLEADOS
# =========================================================

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

# =========================================================
# TABLA KPI
# =========================================================

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

    empleados = pd.read_sql(
        "SELECT * FROM empleados",
        conn
    )

    kpis = pd.read_sql(
        "SELECT * FROM indicadores",
        conn
    )

    col1,col2,col3,col4 = st.columns(4)

    with col1:

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">
            COLABORADORES
            </div>

            <div class="metric-value">
            {len(empleados)}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">
            KPIs
            </div>

            <div class="metric-value">
            {len(kpis)}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:

        promedio = 0

        if not kpis.empty:
            promedio = round(kpis["real"].mean(),2)

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">
            PROMEDIO REAL
            </div>

            <div class="metric-value">
            {promedio}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:

        fecha = datetime.now().strftime("%d/%m/%Y")

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">
            FECHA
            </div>

            <div class="metric-value" style="font-size:20px;">
            {fecha}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div class="panel">
    <h3>📊 KPIs GENERALES</h3>
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
            height=600,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white")
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# =========================================================
# REGISTRAR
# =========================================================

elif menu == "REGISTRAR":

    st.markdown("""
    <div class="panel">
    <h2>👨‍💼 REGISTRAR EMPLEADO</h2>
    </div>
    """, unsafe_allow_html=True)

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

        foto = st.file_uploader(
            "FOTO",
            type=["png","jpg","jpeg"]
        )

        st.markdown("### KPIs")

        indicadores = []

        for i in range(3):

            st.markdown(f"#### KPI {i+1}")

            ind = st.text_input(
                f"INDICADOR {i+1}",
                key=f"i{i}"
            )

            meta = st.number_input(
                f"META {i+1}",
                key=f"m{i}"
            )

            proy = st.number_input(
                f"PROYECTADO {i+1}",
                key=f"p{i}"
            )

            real = st.number_input(
                f"REAL {i+1}",
                key=f"r{i}"
            )

            indicadores.append(
                [ind,meta,proy,real]
            )

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

            c.execute("""
            DELETE FROM indicadores
            WHERE id_empleado=?
            """,(id_emp,))

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

    st.markdown("""
    <div class="panel">
    <h2>👥 EMPLEADOS</h2>
    </div>
    """, unsafe_allow_html=True)

    empleados = pd.read_sql(
        "SELECT * FROM empleados",
        conn
    )

    st.dataframe(empleados)

# =========================================================
# ESCANER
# =========================================================

elif menu == "ESCANER":

    st.markdown("""
    <div class="panel">
    <h2>📺 PANEL EJECUTIVO KPI</h2>
    </div>
    """, unsafe_allow_html=True)

    empleados = pd.read_sql(
        "SELECT * FROM empleados",
        conn
    )

    if not empleados.empty:

        empleados["mostrar"] = (
            empleados["id"]
            + " - "
            + empleados["nombre"]
            + " - "
            + empleados["cargo"]
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
            f"""
            SELECT * FROM indicadores
            WHERE id_empleado='{emp_id}'
            """,
            conn
        )

        col1,col2 = st.columns([1,2])

        # =====================================================
        # PERFIL
        # =====================================================

        with col1:

            st.markdown("""
            <div class="panel">
            """, unsafe_allow_html=True)

            if data["foto"]:

                image = Image.open(
                    io.BytesIO(data["foto"])
                )

                st.image(
                    image,
                    use_container_width=True
                )

            st.markdown(f"""
            ### {data["nombre"].upper()}
            #### {data["cargo"].upper()}
            """)

            st.write("**ID:**", data["id"])
            st.write("**EDAD:**", data["edad"])
            st.write("**ESTADO CIVIL:**", data["estado"])
            st.write("**PROFESION:**", data["profesion"])

            st.markdown("</div>", unsafe_allow_html=True)

        # =====================================================
        # TV KPI
        # =====================================================

        with col2:

            st.markdown("""
            <div class="panel">
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
