import streamlit as st
import pandas as pd
import sqlite3
import base64
from datetime import datetime

# =========================================================
# CONFIGURACION GENERAL
# =========================================================

st.set_page_config(
    page_title="GERENCIA DE BANCO KPI",
    page_icon="🏦",
    layout="wide"
)

# =========================================================
# BASE DE DATOS
# =========================================================

conn = sqlite3.connect(
    "banco_kpi.db",
    check_same_thread=False
)

cursor = conn.cursor()

# =========================================================
# TABLA EMPLEADOS
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS empleados(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    puesto TEXT,
    departamento TEXT,
    rendimiento INTEGER,
    unidad_medida TEXT,
    kpi TEXT
)
""")

# =========================================================
# TABLA KPIs
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS kpis(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT
)
""")

# =========================================================
# TABLA PUESTOS
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS puestos(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT
)
""")

conn.commit()

# =========================================================
# INSERTAR KPIs BASE
# =========================================================

kpis_base = [
    "Cumplimiento de metas",
    "Tiempo de respuesta",
    "Atencion al cliente",
    "Productividad diaria",
    "Calidad operativa",
    "Gestion documental",
    "Analisis financiero",
    "Rendimiento bancario"
]

for kpi in kpis_base:

    cursor.execute(
        "SELECT * FROM kpis WHERE nombre=?",
        (kpi,)
    )

    if cursor.fetchone() is None:

        cursor.execute(
            "INSERT INTO kpis(nombre) VALUES(?)",
            (kpi,)
        )

# =========================================================
# INSERTAR PUESTOS BASE
# =========================================================

puestos_base = [
    "Gerente General",
    "Supervisor KPI",
    "Analista KPI",
    "Recursos Humanos",
    "Cajero",
    "Asistente Bancario",
    "Auditor",
    "Gerente Financiero"
]

for puesto in puestos_base:

    cursor.execute(
        "SELECT * FROM puestos WHERE nombre=?",
        (puesto,)
    )

    if cursor.fetchone() is None:

        cursor.execute(
            "INSERT INTO puestos(nombre) VALUES(?)",
            (puesto,)
        )

conn.commit()

# =========================================================
# OBTENER DATOS
# =========================================================

df_empleados = pd.read_sql_query(
    "SELECT * FROM empleados",
    conn
)

df_kpis = pd.read_sql_query(
    "SELECT * FROM kpis",
    conn
)

df_puestos = pd.read_sql_query(
    "SELECT * FROM puestos",
    conn
)

# =========================================================
# FONDO
# =========================================================

try:

    with open(
        "cf28a163-8639-4681-8332-327545f58634.png",
        "rb"
    ) as img:

        encoded = base64.b64encode(
            img.read()
        ).decode()

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
        background: rgba(0,0,0,0.80);
    }}

    h1,h2,h3,h4,h5,h6,p,label {{
        color:white !important;
    }}

    .box {{
        background: rgba(0,0,0,0.60);
        padding:20px;
        border-radius:15px;
        border:1px solid rgba(255,255,255,0.10);
    }}

    </style>
    """, unsafe_allow_html=True)

except:
    pass

# =========================================================
# LOGIN
# =========================================================

if "login" not in st.session_state:
    st.session_state.login = False

USUARIO = "admin"
CLAVE = "1234"

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

# =========================================================
# MENU
# =========================================================

st.sidebar.title("MENU")

menu = st.sidebar.radio(
    "NAVEGACION",
    [
        "Dashboard",
        "Registrar Empleado",
        "Nuevo KPI",
        "Nuevo Puesto",
        "Empleados",
        "Escaner"
    ]
)

# =========================================================
# DASHBOARD
# =========================================================

if menu == "Dashboard":

    st.title("🏦 DASHBOARD DE CUMPLIMIENTO KPI")

    total = len(df_empleados)

    objetivo = 0
    riesgo = 0
    promedio = 0

    if total > 0:

        objetivo = len(
            df_empleados[
                df_empleados["rendimiento"] >= 70
            ]
        )

        riesgo = len(
            df_empleados[
                df_empleados["rendimiento"] < 70
            ]
        )

        promedio = int(
            df_empleados["rendimiento"].mean()
        )

    c1,c2,c3,c4 = st.columns(4)

    with c1:
        st.metric("COLABORADORES", total)

    with c2:
        st.metric("KPIs ACTIVOS", len(df_kpis))

    with c3:
        st.metric("CUMPLIMIENTO", f"{promedio}%")

    with c4:
        st.metric("EN RIESGO", riesgo)

    st.markdown("<br>", unsafe_allow_html=True)

    if total > 0:

        st.subheader("RENDIMIENTO POR EMPLEADO")

        st.bar_chart(
            df_empleados.set_index("nombre")[
                "rendimiento"
            ]
        )

        st.subheader("BASE DE EMPLEADOS")

        st.dataframe(df_empleados)

# =========================================================
# REGISTRO EMPLEADOS
# =========================================================

elif menu == "Registrar Empleado":

    st.title("REGISTRO DE EMPLEADOS")

    nombre = st.text_input("NOMBRE")

    puesto = st.selectbox(
        "PUESTO",
        df_puestos["nombre"]
    )

    departamento = st.selectbox(
        "DEPARTAMENTO",
        [
            "Gerencia",
            "Finanzas",
            "Recursos Humanos",
            "Analitica",
            "Operaciones"
        ]
    )

    kpi = st.selectbox(
        "KPI ASIGNADO",
        df_kpis["nombre"]
    )

    unidad = st.selectbox(
        "UNIDAD DE MEDIDA",
        [
            "%",
            "Minutos",
            "Horas",
            "Cantidad",
            "Documentos",
            "Clientes",
            "Operaciones"
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
            rendimiento,
            unidad_medida,
            kpi
        )
        VALUES(?,?,?,?,?,?)
        """, (
            nombre,
            puesto,
            departamento,
            rendimiento,
            unidad,
            kpi
        ))

        conn.commit()

        st.success(
            "EMPLEADO REGISTRADO"
        )

# =========================================================
# NUEVO KPI
# =========================================================

elif menu == "Nuevo KPI":

    st.title("CREAR NUEVO KPI")

    nuevo_kpi = st.text_input(
        "NOMBRE DEL KPI"
    )

    if st.button("AGREGAR KPI"):

        cursor.execute("""
        INSERT INTO kpis(nombre)
        VALUES(?)
        """, (nuevo_kpi,))

        conn.commit()

        st.success(
            "KPI AGREGADO"
        )

# =========================================================
# NUEVO PUESTO
# =========================================================

elif menu == "Nuevo Puesto":

    st.title("CREAR NUEVO PUESTO")

    nuevo_puesto = st.text_input(
        "NOMBRE DEL PUESTO"
    )

    if st.button("AGREGAR PUESTO"):

        cursor.execute("""
        INSERT INTO puestos(nombre)
        VALUES(?)
        """, (nuevo_puesto,))

        conn.commit()

        st.success(
            "PUESTO AGREGADO"
        )

# =========================================================
# EMPLEADOS
# =========================================================

elif menu == "Empleados":

    st.title("BASE GENERAL DE EMPLEADOS")

    if len(df_empleados) > 0:

        st.dataframe(df_empleados)

    else:

        st.warning(
            "NO HAY EMPLEADOS"
        )

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

        st.success(
            "DOCUMENTO ESCANEADO"
        )

        st.write(
            "ARCHIVO:",
            archivo.name
        )

        st.write(
            "FECHA:",
            datetime.now()
        )
