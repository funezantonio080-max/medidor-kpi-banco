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
        st.error("ACCESO INCORRECTO")

if not st.session_state.auth:
    st.stop()

# ---------------- DB SEGURA ----------------
conn = sqlite3.connect("bank.db", check_same_thread=False)
c = conn.cursor()

# CREAR TABLA SOLO SI NO EXISTE
c.execute('''CREATE TABLE IF NOT EXISTS empleados(
id TEXT PRIMARY KEY,
nombre TEXT,
edad INT,
estado TEXT,
profesion TEXT,
cargo TEXT
)''')

# 🔥 MIGRACIÓN SEGURA (AGREGAR FOTO)
cols = pd.read_sql("PRAGMA table_info(empleados)", conn)

if "foto" not in cols["name"].values:
    c.execute("ALTER TABLE empleados ADD COLUMN foto BLOB")
    conn.commit()

# OTRAS TABLAS
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
    indicadores = pd.read_sql("SELECT indicador FROM cargos WHERE nombre=?", conn, params=(cargo,))
    for ind in indicadores["indicador"]:
        c.execute("INSERT INTO kpis VALUES (?,?,?,?,?)",(emp_id, ind, 0, 0, 0))
    conn.commit()

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

def a_mayus(df):
    return df.applymap(lambda x: str(x).upper())

# ---------------- MENU ----------------
menu = st.sidebar.radio("MENÚ",[
    "REGISTRAR",
    "EDITAR EMPLEADO",
    "KPIS",
    "ESCÁNER",
    "CARGOS",
    "DASHBOARD"
])

# ---------------- REGISTRAR ----------------
if menu == "REGISTRAR":
    st.header("➕ REGISTRO")

    cargos = pd.read_sql("SELECT DISTINCT nombre FROM cargos", conn)

    col1,col2 = st.columns(2)

    with col1:
        id = st.text_input("ID").upper()
        nombre = st.text_input("NOMBRE").upper()

    with col2:
        edad = st.number_input("EDAD",18,70)
        cargo = st.selectbox("CARGO",cargos["nombre"])

    foto = st.file_uploader("FOTO", type=["jpg","png"])

    if st.button("GUARDAR"):
        img = foto.read() if foto else None

        c.execute("INSERT OR REPLACE INTO empleados VALUES (?,?,?,?,?,?,?)",
                  (id,nombre,edad,"","",cargo,img))

        regenerar_kpis(id,cargo)
        st.success("REGISTRADO")

# ---------------- ESCÁNER ----------------
elif menu == "ESCÁNER":
    st.header("🔍 ESCÁNER")

    df = pd.read_sql("SELECT * FROM empleados", conn)

    if not df.empty:
        df["display"] = df["id"] + " - " + df["nombre"] + " - " + df["cargo"]

        sel = st.selectbox("SELECCIONAR", df["display"])
        emp_id = df[df["display"]==sel]["id"].values[0]

        data = df[df["id"]==emp_id].iloc[0]
        kpis = pd.read_sql("SELECT * FROM kpis WHERE id=?", conn, params=(emp_id,))

        st.write(a_mayus(pd.DataFrame([data])))

        if "foto" in data.index and data["foto"]:
            st.image(data["foto"], width=140)

        st.image(generar_qr(data,kpis), width=140)

        for i,row in kpis.iterrows():
            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=["META","PROYECTADO","REAL"],
                y=[row["meta"],row["proyectado"],row["real"]],
                width=0.25
            ))

            st.plotly_chart(fig, key=f"graf_{i}")
