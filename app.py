import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import qrcode
import json
from io import BytesIO

# ---------------- CONFIG ----------------

st.set_page_config(
    page_title="BANCO KPI PRO",
    layout="wide"
)

# ---------------- LOGIN ----------------

USERS = {"ADMIN": "1234"}

if "auth" not in st.session_state:
    st.session_state.auth = False

st.sidebar.title("🔐 LOGIN")

user = st.sidebar.text_input(
    "USUARIO"
).upper()

password = st.sidebar.text_input(
    "CONTRASEÑA",
    type="password"
)

if st.sidebar.button("INGRESAR"):

    if USERS.get(user) == password:

        st.session_state.auth = True

    else:

        st.sidebar.error(
            "ACCESO INCORRECTO"
        )

if not st.session_state.auth:
    st.stop()

# ---------------- DB ----------------

conn = sqlite3.connect(
    "bank.db",
    check_same_thread=False
)

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

if pd.read_sql(
    "SELECT * FROM cargos",
    conn
).empty:

    base = {

        "GERENTE FINANCIERO":
        [
            "RENTABILIDAD",
            "ROA",
            "ROE",
            "LIQUIDEZ"
        ],

        "RECURSOS HUMANOS":
        [
            "AUSENTISMO",
            "CLIMA",
            "ROTACION"
        ],

        "ANALISTA DE DATOS":
        [
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
        """,
        (
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
