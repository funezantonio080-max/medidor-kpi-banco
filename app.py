import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
from PIL import Image
import io
from datetime import datetime
import base64
import os

# =====================================================
# CONFIGURACION
# =====================================================

st.set_page_config(
    page_title="GERENCIA DE BANCO KPI",
    page_icon="🏦",
    layout="wide"
)

# =====================================================
# IMAGEN PORTADA
# =====================================================

IMAGEN_PORTADA = "8e2ed00a-50f4-48f2-a807-a11e06a29108.png"

def get_base64(imagen):

    with open(imagen, "rb") as f:
        data = f.read()

    return base64.b64encode(data).decode()

img = ""

if os.path.exists(IMAGEN_PORTADA):

    img = get_base64(IMAGEN_PORTADA)

# =====================================================
# CSS
# =====================================================

st.markdown(f"""
<style>

[data-testid="stAppViewContainer"] {{
    background-image:
    linear-gradient(
    rgba(0,0,0,0.72),
    rgba(0,0,0,0.72)),
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
    background: rgba(0,0,0,0.92);
}}

.block-container {{
    padding-top: 1rem;
}}

h1,h2,h3,h4,h5,h6,p,label {{
    color:white !important;
}}

.metric {{
    background: rgba(5,15,35,0.88);
    padding:20px;
    border-radius:18px;
    text-align:center;
    border:1px solid rgba(255,255,255,0.08);
    box-shadow:0 0 15px rgba(0,0,0,0.5);
}}

.valor {{
    font-size:42px;
    font-weight:bold;
    color:#00ffcc;
}}

.panel {{
    background: rgba(5,15,35,0.88);
    padding:20px;
    border-radius:18px;
    border:1px solid rgba(255,255,255,0.08);
}}

.stButton>button {{
    width:100%;
    border:none;
    border-radius:12px;
    height:48px;
    background:linear-gradient(90deg,#0066ff,#00c6ff);
    color:white;
    font-weight:bold;
    font-size:16px;
}}

.stTextInput input {{
    border-radius:10px;
}}

</style>
""", unsafe_allow_html=True)

# =====================================================
# LOGIN
# =====================================================

if "login" not in st.session_state:
    st.session_state.login = False

USUARIO = "ADMIN"
CLAVE = "1234"

# =====================================================
# LOGIN SCREEN
# =====================================================

if not st.session_state.login:

    st.markdown("""
    <h1 style='text-align:center;font-size:62px;'>
    🏦 GERENCIA DE BANCO KPI
    </h1>
    """, unsafe_allow_html=True)

    st.markdown("""
    <h3 style='text-align:center;'>
    CENTRO EJECUTIVO DE INDICADORES BANCARIOS
    </h3>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    c1,c2,c3 = st.columns([1,1,1])

    with c2:

        st.markdown("""
        <div class="panel">
        <h2 style='text-align:center;'>
        INICIAR SESION
        </h2>
        </div>
        """, unsafe_allow_html=True)

        usuario = st.text_input("USUARIO")
        clave = st.text_input(
            "CONTRASEÑA",
            type="password"
        )

        if st.button("INGRESAR"):

            if usuario == USUARIO and clave == CLAVE:

                st.session_state.login = True
                st.rerun()

            else:

                st.error(
                    "USUARIO O CONTRASEÑA INCORRECTA"
                )

    st.stop()

# =====================================================
# TITULO
# =====================================================

st.markdown("""
<h1 style='text-align:center;font-size:55px;'>
🏦 GERENCIA DE BANCO KPI
</h1>
""", unsafe_allow_html=True)

st.markdown("""
<h3 style='text-align:center;'>
CENTRO EJECUTIVO DE INDICADORES BANCARIOS
</h3>
""", unsafe_allow_html=True)

# =====================================================
# DATABASE
# =====================================================

conn = sqlite3.connect(
    "banco_kpi.db",
    check_same_thread=False
)

c = conn.cursor()

# =====================================================
# TABLA EMPLEADOS
# =====================================================

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

# =====================================================
# TABLA KPIs
# =====================================================

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

# =====================================================
# MENU
# =====================================================

menu = st.sidebar.radio(
    "MENU",
    [
        "DASHBOARD",
        "REGISTRAR",
        "EMPLEADOS",
        "ESCANER"
    ]
)

# =====================================================
# DASHBOARD
# =====================================================

if menu == "DASHBOARD":

    empleados = pd.read_sql(
        "SELECT * FROM empleados",
        conn
    )

    kpis = pd.read_sql(
        "SELECT * FROM indicadores",
        conn
    )

    c1,c2,c3,c4 = st.columns(4)

    # =================================================
    # COLABORADORES
    # =================================================

    with c1:

        st.markdown(
            f"""
            <div class="metric">
            <h3>COLABORADORES</h3>

            <div class="valor">
            {len(empleados)}
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    # =================================================
    # KPIs
    # =================================================

    with c2:

        st.markdown(
            f"""
            <div class="metric">
            <h3>KPIs</h3>

            <div class="valor">
            {len(kpis)}
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    # =================================================
    # PROMEDIO
    # =================================================

    with c3:

        promedio = 0

        if not kpis.empty:

            promedio = round(
                kpis["real"].mean(),
                2
            )

        st.markdown(
            f"""
            <div class="metric">
            <h3>PROMEDIO REAL</h3>

            <div class="valor">
            {promedio}
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    # =================================================
    # FECHA
    # =================================================

    with c4:

        fecha = datetime.now().strftime(
            "%d/%m/%Y"
        )

        st.markdown(
            f"""
            <div class="metric">
            <h3>FECHA</h3>

            <div class="valor" style="font-size:22px;">
            {fecha}
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # =================================================
    # GRAFICO GENERAL
    # =================================================

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
