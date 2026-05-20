import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import qrcode
import json
import base64
import os
from io import BytesIO

# =========================================================
# CONFIGURACION
# =========================================================

st.set_page_config(
    page_title="BANCO KPI PRO",
    layout="wide",
    page_icon="🏦"
)

# =========================================================
# FONDO SOLO LOGIN
# =========================================================

def aplicar_fondo_login():

    imagen = "fondo.png"

    if not os.path.exists(imagen):
        return

    with open(imagen, "rb") as f:

        img = base64.b64encode(
            f.read()
        ).decode()

    st.markdown(f"""
    <style>

    [data-testid="stAppViewContainer"] {{

        background:
        linear-gradient(
        rgba(0,0,0,.25),
        rgba(0,0,0,.55)
        ),

        url(
        "data:image/png;base64,{img}"
        );

        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}

    [data-testid="stHeader"] {{
        background: transparent;
    }}

    [data-testid="stSidebar"] {{
        background: rgba(0,0,0,0.85);
    }}

    h1,h2,h3,h4,h5,h6,p,label,div {{
        color:white !important;
    }}

    .stTextInput input {{

        background:
        rgba(0,0,0,.35);

        color:white;

        border-radius:14px;
    }}

    .stButton button {{

        border-radius:14px;

        background:#0066ff;

        color:white;
    }}

    .stDataFrame {{
        background: rgba(0,0,0,0.5);
    }}

    </style>
    """, unsafe_allow_html=True)

# =========================================================
# LOGIN
# =========================================================

USERS = {
    "ADMIN": "1234"
}

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:

    aplicar_fondo_login()

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

    c1, c2, c3 = st.columns([1,1,1])

    with c2:

        st.sidebar.title("🔐 LOGIN")

        user = st.text_input(
            "USUARIO"
        ).upper()

        password = st.text_input(
            "CONTRASEÑA",
            type="password"
        )

        if st.button("INGRESAR"):

            if USERS.get(user) == password:

                st.session_state.auth = True
                st.rerun()

            else:

                st.error(
                    "ACCESO INCORRECTO"
                )

    st.stop()

# =========================================================
# BASE DE DATOS
# =========================================================

conn = sqlite3.connect(
    "bank.db",
    check_same_thread=False
)

c = conn.cursor()

# =========================================================
# TABLAS
# =========================================================

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

# =========================================================
# CARGOS BASE
# =========================================================

if pd.read_sql(
    "SELECT * FROM cargos",
    conn
).empty:

    base = {

        "GERENTE FINANCIERO": [
            "RENTABILIDAD",
            "ROA",
            "ROE",
            "LIQUIDEZ"
        ],

        "RECURSOS HUMANOS": [
            "AUSENTISMO",
            "CLIMA",
            "ROTACION"
        ],

        "ANALISTA DE DATOS": [
            "PRECISION",
            "TIEMPO",
            "SISTEMAS"
        ]
    }

    for cargo, inds in base.items():

        for i in inds:

            c.execute(
                "INSERT INTO cargos VALUES (?,?)",
                (cargo, i)
            )

    conn.commit()

# =========================================================
# FUNCIONES
# =========================================================

def regenerar_kpis(emp_id, cargo):

    c.execute(
        "DELETE FROM kpis WHERE id=?",
        (emp_id,)
    )

    indicadores = pd.read_sql(
        "SELECT indicador FROM cargos WHERE nombre=?",
        conn,
        params=(cargo,)
    )

    for ind in indicadores["indicador"]:

        c.execute("""
        INSERT INTO kpis
        VALUES (?,?,?,?,?)
        """, (
            emp_id,
            ind,
            0,
            0,
            0
        ))

    conn.commit()

def generar_qr(data, kpis):

    contenido = {

        "id": data["id"],
        "nombre": data["nombre"],
        "cargo": data["cargo"],
        "kpis": kpis.to_dict(
            orient="records"
        )
    }

    img = qrcode.make(
        json.dumps(contenido)
    )

    buf = BytesIO()

    img.save(buf)

    return buf

def mayus(df):

    df = df.copy()

    for col in df.columns:

        df[col] = df[col].apply(
            lambda x:
            x.upper()
            if isinstance(x, str)
            else x
        )

    df.columns = [
        c.upper()
        for c in df.columns
    ]

    return df

# =========================================================
# MENU
# =========================================================

menu = st.sidebar.radio(
    "MENÚ",
    [
        "DASHBOARD",
        "REGISTRAR",
        "EDITAR",
        "KPIS",
        "ESCÁNER",
        "CARGOS"
    ]
)

# =========================================================
# DASHBOARD
# =========================================================

if menu == "DASHBOARD":

    st.title("📊 DASHBOARD GENERAL")

    empleados = pd.read_sql(
        "SELECT * FROM empleados",
        conn
    )

    kpis = pd.read_sql(
        "SELECT * FROM kpis",
        conn
    )

    total_empleados = len(empleados)

    total_kpis = len(kpis)

    cumplimiento = 0

    if not kpis.empty:

        cumplimiento = round(
            (kpis["real"].sum() /
            (kpis["meta"].sum() + 1)) * 100,
            1
        )

    riesgo = len(
        kpis[kpis["real"] < kpis["meta"]]
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "👥 EMPLEADOS",
            total_empleados
        )

    with c2:
        st.metric(
            "📈 KPIs",
            total_kpis
        )

    with c3:
        st.metric(
            "✅ CUMPLIMIENTO",
            f"{cumplimiento}%"
        )

    with c4:
        st.metric(
            "⚠️ EN RIESGO",
            riesgo
        )

    st.markdown("---")

    if not empleados.empty:

        empleados_view = empleados.drop(
            columns=["foto"],
            errors="ignore"
        )

        st.dataframe(
            mayus(empleados_view)
        )

    if not kpis.empty:

        resumen = kpis.groupby(
            "indicador"
        )["real"].sum()

        st.subheader(
            "📊 RENDIMIENTO KPI"
        )

        st.bar_chart(resumen)

# =========================================================
# REGISTRAR
# =========================================================

elif menu == "REGISTRAR":

    st.title("➕ REGISTRO DE EMPLEADO")

    cargos = pd.read_sql(
        "SELECT DISTINCT nombre FROM cargos",
        conn
    )

    with st.form("form_reg"):

        col1, col2, col3 = st.columns(3)

        with col1:

            id = st.text_input(
                "ID"
            ).upper()

            nombre = st.text_input(
                "NOMBRE"
            ).upper()

        with col2:

            edad = st.number_input(
                "EDAD",
                18,
                70
            )

            estado = st.selectbox(
                "ESTADO",
                ["SOLTERO","CASADO"]
            )

        with col3:

            profesion = st.text_input(
                "PROFESIÓN"
            ).upper()

            cargo = st.selectbox(
                "CARGO",
                cargos["nombre"]
            )

        foto = st.file_uploader(
            "FOTO",
            type=["jpg","png"]
        )

        if st.form_submit_button(
            "GUARDAR"
        ):

            img = foto.read() if foto else None

            c.execute("""
            INSERT OR REPLACE INTO empleados
            VALUES (?,?,?,?,?,?,?)
            """, (
                id,
                nombre,
                edad,
                estado,
                profesion,
                cargo,
                img
            ))

            regenerar_kpis(id, cargo)

            conn.commit()

            st.success(
                "EMPLEADO REGISTRADO"
            )

# =========================================================
# EDITAR
# =========================================================

elif menu == "EDITAR":

    st.title("✏️ EDITAR EMPLEADO")

    df = pd.read_sql(
        "SELECT * FROM empleados",
        conn
    )

    if df.empty:

        st.warning(
            "NO HAY EMPLEADOS"
        )

    else:

        emp_id = st.selectbox(
            "EMPLEADO",
            df["id"]
        )

        data = df[
            df["id"] == emp_id
        ].iloc[0]

        nombre = st.text_input(
            "NOMBRE",
            value=data["nombre"]
        ).upper()

        edad = st.number_input(
            "EDAD",
            value=int(data["edad"])
        )

        estado = st.selectbox(
            "ESTADO",
            ["SOLTERO","CASADO"]
        )

        cargos = pd.read_sql(
            "SELECT DISTINCT nombre FROM cargos",
            conn
        )

        cargo = st.selectbox(
            "CARGO",
            cargos["nombre"]
        )

        foto = st.file_uploader(
            "ACTUALIZAR FOTO",
            type=["jpg","png"]
        )

        if st.button(
            "ACTUALIZAR"
        ):

            img = foto.read() if foto else data["foto"]

            c.execute("""
            UPDATE empleados
            SET nombre=?,
                edad=?,
                estado=?,
                cargo=?,
                foto=?
            WHERE id=?
            """, (
                nombre,
                edad,
                estado,
                cargo,
                img,
                emp_id
            ))

            regenerar_kpis(
                emp_id,
                cargo
            )

            conn.commit()

            st.success(
                "ACTUALIZADO"
            )
