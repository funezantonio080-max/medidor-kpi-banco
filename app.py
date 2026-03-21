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

c.execute('''CREATE TABLE IF NOT EXISTS empleados(
id TEXT PRIMARY KEY,
nombre TEXT,
edad INT,
estado TEXT,
profesion TEXT,
cargo TEXT
)''')

cols = pd.read_sql("PRAGMA table_info(empleados)", conn)
if "foto" not in cols["name"].values:
    c.execute("ALTER TABLE empleados ADD COLUMN foto BLOB")
    conn.commit()

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

# ---------------- MENU ----------------
menu = st.sidebar.radio("MENÚ",[
    "REGISTRAR","EDITAR EMPLEADO","KPIS","ESCÁNER","CARGOS","DASHBOARD"
])

# ---------------- ESCÁNER ----------------
if menu == "ESCÁNER":
    st.header("🔍 ESCÁNER")

    df = pd.read_sql("SELECT * FROM empleados", conn)

    if not df.empty:
        df["display"] = df["id"] + " - " + df["nombre"] + " - " + df["cargo"]

        seleccion = st.selectbox("SELECCIONAR", df["display"])
        emp_id = df[df["display"]==seleccion]["id"].values[0]

        data = df[df["id"]==emp_id].iloc[0]
        kpis = pd.read_sql("SELECT * FROM kpis WHERE id=?", conn, params=(emp_id,))

        col1,col2 = st.columns([1,2])

        with col1:
            st.write(a_mayus(pd.DataFrame([data])))

            if "foto" in data.index and data["foto"]:
                st.image(data["foto"], width=150)

            st.image(generar_qr(data,kpis), width=150)

        with col2:
            st.dataframe(a_mayus(kpis))

            # 🔥 FIX: usar índice
            for i, row in kpis.iterrows():

                labels = ["META","PROYECTADO","REAL"]
                valores = [row["meta"],row["proyectado"],row["real"]]

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

                fig.update_layout(showlegend=False)

                # 🔥 CLAVE ÚNICA
                st.plotly_chart(fig, key=f"grafico_{i}")
