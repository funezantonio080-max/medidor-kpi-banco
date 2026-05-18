import streamlit as st
import pandas as pd
import sqlite3
import base64
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
# BASE DE DATOS
# =========================================================

conn = sqlite3.connect("banco_kpi.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS empleados(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    puesto TEXT,
    departamento TEXT,
    rendimiento INTEGER
)
""")

conn.commit()

# =========================================================
# LOGIN
# =========================================================

if "login" not in st.session_state:
    st.session_state.login = False

USUARIO = "admin"
CLAVE = "1234"

# =========================================================
# IMAGEN DE FONDO
# =========================================================

def fondo():

    try:

        with open("cf28a163-8639-4681-8332-327545f58634.png", "rb") as img:

            encoded = base64.b64encode(img.read()).decode()

        st.markdown(f"""
        <style>

        [data-testid="stAppViewContainer"] {{

            background-image:
            linear-gradient(
            rgba(0,0,0,0.45),
            rgba(0,0,0,0.45)),
            url("data:image/png;base64,{encoded}");

            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        [data-testid="stHeader"] {{
            background: rgba(0,0,0,0);
        }}

        [data-testid="stSidebar"] {{
            background: rgba(0,0,0,0.75);
        }}

        h1,h2,h3,h4,h5,h6,p,label {{
            color:white !important;
        }}

        .box {{
            background: rgba(0,0,0,0.60);
            padding:20px;
            border-radius:15px;
            border:1px solid rgba(255,255,255,0.1);
        }}

        </style>
        """, unsafe_allow_html=True)

    except:
        pass

fondo()

# =========================================================
# LOGIN SCREEN
# =========================================================

if not st.session_state.login:

    st.markdown("""
    <h1 style='text-align:center;font-size:70px;'>
    🏦 GERENCIA DE BANCO KPI
    </h1>
    """, unsafe_allow_html=True)

    st.markdown("""
    <h2 style='text-align:center;'>
    CENTRO EJECUTIVO DE INDICADORES BANCARIOS
    </h2>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    c1,c2,c3 = st.columns([1,1,1])

    with c2:

        st.markdown("""
        <div class="box">
        <h1 style='text-align:center;'>
        INICIAR SESION
        </h1>
        </div>
        """, unsafe_allow_html=True)

        usuario = st.text_input("USUARIO")
        clave = st.text_input("CONTRASEÑA", type="password")

        if st.button("INGRESAR"):

            if usuario == USUARIO and clave == CLAVE:

                st.session_state.login = True
                st.rerun()

            else:

                st.error("USUARIO O CONTRASEÑA INCORRECTA")

    st.stop()

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("MENU")

menu = st.sidebar.radio(
    "NAVEGACION",
    [
        "Dashboard",
        "Registrar",
        "Empleados",
        "Escaner"
    ]
)

# =========================================================
# OBTENER EMPLEADOS
# =========================================================

df = pd.read_sql_query(
    "SELECT * FROM empleados",
    conn
)

# =========================================================
# DASHBOARD
# =========================================================

if menu == "Dashboard":

    st.markdown("""
    <h1 style='text-align:center;font-size:60px;'>
    🏦 GERENCIA DE BANCO KPI
    </h1>
    """, unsafe_allow_html=True)

    st.markdown("""
    <h2 style='text-align:center;'>
    DASHBOARD EJECUTIVO BANCARIO
    </h2>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    total = len(df)

    promedio = 0

    if total > 0:
        promedio = int(df["rendimiento"].mean())

    riesgo = len(df[df["rendimiento"] < 70])

    objetivo = len(df[df["rendimiento"] >= 70])

    c1,c2,c3,c4 = st.columns(4)

    with c1:
        st.metric("COLABORADORES", total)

    with c2:
        st.metric("KPIs", total)

    with c3:
        st.metric("EN OBJETIVO", objetivo)

    with c4:
        st.metric("EN RIESGO", riesgo)

    st.markdown("<br><br>", unsafe_allow_html=True)

    st.subheader("KPIs GENERALES")

    if total > 0:

        st.dataframe(df)

        st.bar_chart(
            df.set_index("nombre")["rendimiento"]
        )

    else:

        st.info("NO HAY EMPLEADOS REGISTRADOS")

# =========================================================
# REGISTRAR
# =========================================================

elif menu == "Registrar":

    st.title("REGISTRO DE EMPLEADOS")

    nombre = st.text_input("NOMBRE")

    puesto = st.selectbox(
        "PUESTO",
        [
            "Gerente",
            "Supervisor",
            "Analista KPI",
            "Recursos Humanos",
            "Cajero",
            "Asistente"
        ]
    )

    departamento = st.selectbox(
        "DEPARTAMENTO",
        [
            "Finanzas",
            "Recursos Humanos",
            "Analitica",
            "Operaciones",
            "Gerencia"
        ]
    )

    rendimiento = st.slider(
        "RENDIMIENTO KPI",
        0,
        100,
        80
    )

    if st.button("GUARDAR EMPLEADO"):

        cursor.execute("""
        INSERT INTO empleados(
        nombre,
        puesto,
        departamento,
        rendimiento
        )
        VALUES(?,?,?,?)
        """, (
            nombre,
            puesto,
            departamento,
            rendimiento
        ))

        conn.commit()

        st.success("EMPLEADO REGISTRADO")

# =========================================================
# EMPLEADOS
# =========================================================

elif menu == "Empleados":

    st.title("LISTA DE EMPLEADOS")

    if len(df) > 0:

        st.dataframe(df)

    else:

        st.warning("NO HAY EMPLEADOS")

# =========================================================
# ESCANER
# =========================================================

elif menu == "Escaner":

    st.title("ESCANER DE DOCUMENTOS")

    archivo = st.file_uploader(
        "SUBIR DOCUMENTO",
        type=["png","jpg","jpeg","pdf"]
    )

    if archivo:

        st.success("DOCUMENTO ESCANEADO")

        st.write("Nombre:", archivo.name)

        st.write("Fecha:", datetime.now())
