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

# ---------------- DB LIMPIA ----------------
conn = sqlite3.connect("bank.db", check_same_thread=False)
c = conn.cursor()

# RECREAR TABLAS (SOLUCIÓN DEFINITIVA)
c.execute("DROP TABLE IF EXISTS empleados")
c.execute("DROP TABLE IF EXISTS kpis")
c.execute("DROP TABLE IF EXISTS cargos")

c.execute('''CREATE TABLE empleados(
id TEXT PRIMARY KEY,
nombre TEXT,
edad INT,
estado TEXT,
profesion TEXT,
cargo TEXT,
foto BLOB
)''')

c.execute('''CREATE TABLE kpis(
id TEXT,
indicador TEXT,
meta REAL,
real REAL,
proyectado REAL
)''')

c.execute('''CREATE TABLE cargos(
nombre TEXT,
indicador TEXT
)''')

conn.commit()

# ---------------- CARGOS BASE ----------------
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

        c.execute("INSERT INTO empleados VALUES (?,?,?,?,?,?,?)",
                  (id,nombre,edad,"","",cargo,img))

        regenerar_kpis(id,cargo)
        st.success("REGISTRADO")

# ---------------- EDITAR ----------------
elif menu == "EDITAR EMPLEADO":
    st.header("✏️ EDITAR")

    df = pd.read_sql("SELECT * FROM empleados", conn)

    if not df.empty:
        emp_id = st.selectbox("EMPLEADO", df["id"])
        data = df[df["id"]==emp_id].iloc[0]

        nombre = st.text_input("NOMBRE", value=data["nombre"]).upper()
        edad = st.number_input("EDAD", value=int(data["edad"]))

        cargos = pd.read_sql("SELECT DISTINCT nombre FROM cargos", conn)
        cargo = st.selectbox("CARGO", cargos["nombre"])

        if st.button("ACTUALIZAR"):
            c.execute("""UPDATE empleados 
                         SET nombre=?, edad=?, cargo=? 
                         WHERE id=?""",
                      (nombre,edad,cargo,emp_id))

            regenerar_kpis(emp_id,cargo)
            st.success("ACTUALIZADO")

# ---------------- KPIS ----------------
elif menu == "KPIS":
    st.header("📊 KPIS")

    df = pd.read_sql("SELECT * FROM empleados", conn)

    if not df.empty:
        emp_id = st.selectbox("EMPLEADO", df["id"])

        kpis = pd.read_sql("SELECT * FROM kpis WHERE id=?", conn, params=(emp_id,))

        for i,row in kpis.iterrows():

            st.subheader(row["indicador"])

            col1,col2,col3 = st.columns(3)

            with col1:
                m = st.number_input("META",value=row["meta"],key=f"m{i}")
            with col2:
                p = st.number_input("PROYECTADO",value=row["proyectado"],key=f"p{i}")
            with col3:
                r = st.number_input("REAL",value=row["real"],key=f"r{i}")

            if st.button(f"GUARDAR_{i}"):
                c.execute("""UPDATE kpis SET meta=?, real=?, proyectado=? 
                             WHERE id=? AND indicador=?""",
                          (m,r,p,emp_id,row["indicador"]))
                conn.commit()

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

        col1,col2 = st.columns([1,2])

        with col1:
            st.write(a_mayus(pd.DataFrame([data])))

            if data["foto"]:
                st.image(data["foto"], width=140)

            st.image(generar_qr(data,kpis), width=140)

        with col2:
            st.dataframe(a_mayus(kpis))

            for i,row in kpis.iterrows():

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

                fig.update_layout(title=row["indicador"], showlegend=False)

                st.plotly_chart(fig, key=f"graf_{i}")

# ---------------- CARGOS ----------------
elif menu == "CARGOS":
    st.header("⚙️ CARGOS")

    nombre = st.text_input("CARGO").upper()
    inds = st.text_area("INDICADORES")

    if st.button("GUARDAR"):
        for i in inds.split(","):
            c.execute("INSERT INTO cargos VALUES (?,?)",(nombre,i.strip().upper()))
        conn.commit()

# ---------------- DASHBOARD ----------------
elif menu == "DASHBOARD":
    st.header("📊 DASHBOARD")

    df = pd.read_sql("SELECT * FROM empleados", conn)

    if not df.empty:
        st.dataframe(a_mayus(df))
