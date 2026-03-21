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

st.sidebar.subheader("🔐 LOGIN")
user = st.sidebar.text_input("USUARIO").upper()
password = st.sidebar.text_input("CONTRASEÑA", type="password")

if st.sidebar.button("INGRESAR"):
    if USERS.get(user) == password:
        st.session_state.auth = True
    else:
        st.error("ACCESO INCORRECTO")

if not st.session_state.auth:
    st.stop()

# ---------------- DB ----------------
conn = sqlite3.connect("bank.db", check_same_thread=False)
c = conn.cursor()

# TABLA EMPLEADOS
c.execute('''CREATE TABLE IF NOT EXISTS empleados(
id TEXT PRIMARY KEY,
nombre TEXT,
edad INT,
estado TEXT,
profesion TEXT,
cargo TEXT
)''')

# 🔥 VERIFICAR Y AGREGAR COLUMNA FOTO SI NO EXISTE
columnas = pd.read_sql("PRAGMA table_info(empleados)", conn)

if "foto" not in columnas["name"].values:
    c.execute("ALTER TABLE empleados ADD COLUMN foto BLOB")
    conn.commit()

# TABLAS RESTANTES
c.execute('''CREATE TABLE IF NOT EXISTS kpis(
id TEXT,
indicador TEXT,
meta REAL,
real REAL,
proyectado REAL
)''')

c.execute('''CREATE TABLE IF NOT EXISTS cargos(
nombre TEXT,
indicador TEXT
)''')

conn.commit()

# ---------------- FUNCIONES ----------------
def generar_qr(data, kpis):
    contenido = {
        "id": data["id"],
        "nombre": data["nombre"],
        "cargo": data["cargo"],
        "kpis": kpis.to_dict(orient="records")
    }
    qr = qrcode.make(json.dumps(contenido))
    buf = BytesIO()
    qr.save(buf)
    return buf

def regenerar_kpis(emp_id, cargo):
    c.execute("DELETE FROM kpis WHERE id=?", (emp_id,))
    indicadores = pd.read_sql("SELECT indicador FROM cargos WHERE nombre=?", conn, params=(cargo,))
    for ind in indicadores["indicador"]:
        c.execute("INSERT INTO kpis VALUES (?,?,?,?,?)",(emp_id, ind.upper(), 0, 0, 0))
    conn.commit()

def a_mayus(df):
    return df.applymap(lambda x: str(x).upper())

# ---------------- INIT ----------------
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

# ---------------- MENU ----------------
menu = st.sidebar.radio("MENÚ",[
    "REGISTRAR","EDITAR EMPLEADO","ESCÁNER"
])

# ---------------- REGISTRAR ----------------
if menu == "REGISTRAR":
    st.header("REGISTRO")

    cargos = pd.read_sql("SELECT DISTINCT nombre FROM cargos", conn)

    with st.form("form"):
        col1,col2 = st.columns(2)

        with col1:
            id = st.text_input("ID").upper()
            nombre = st.text_input("NOMBRE").upper()

        with col2:
            edad = st.number_input("EDAD",18,70)
            cargo = st.selectbox("CARGO",cargos["nombre"])

        foto = st.file_uploader("FOTO", type=["jpg","png"])

        if st.form_submit_button("GUARDAR"):
            img = foto.read() if foto else None

            c.execute("INSERT OR REPLACE INTO empleados VALUES (?,?,?,?,?,?,?)",
                      (id,nombre,edad,"","",cargo,img))

            regenerar_kpis(id,cargo)
            st.success("OK")

# ---------------- ESCÁNER ----------------
elif menu == "ESCÁNER":
    df = pd.read_sql("SELECT * FROM empleados", conn)

    df["display"] = df["id"] + " - " + df["nombre"]

    sel = st.selectbox("Empleado", df["display"])
    emp_id = df[df["display"]==sel]["id"].values[0]

    data = df[df["id"]==emp_id].iloc[0]
    kpis = pd.read_sql("SELECT * FROM kpis WHERE id=?", conn, params=(emp_id,))

    st.write(a_mayus(pd.DataFrame([data])))

    # 🔥 PROTECCIÓN CONTRA ERROR
    if "foto" in data.index and data["foto"] is not None:
        st.image(data["foto"], width=150)

    st.image(generar_qr(data,kpis), width=150)
