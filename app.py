import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import qrcode
import json
from io import BytesIO

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Banco KPI PRO", layout="wide")

# ---------------- LOGIN ----------------
USERS = {"admin": "1234"}

if "auth" not in st.session_state:
    st.session_state.auth = False

st.sidebar.subheader("🔐 Login")
user = st.sidebar.text_input("Usuario")
password = st.sidebar.text_input("Contraseña", type="password")

if st.sidebar.button("Ingresar"):
    if USERS.get(user) == password:
        st.session_state.auth = True
    else:
        st.error("Acceso incorrecto")

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
    data_json = json.dumps(contenido)
    qr = qrcode.make(data_json)
    buf = BytesIO()
    qr.save(buf)
    return buf

def regenerar_kpis(emp_id, cargo):
    c.execute("DELETE FROM kpis WHERE id=?", (emp_id,))
    indicadores = pd.read_sql("SELECT indicador FROM cargos WHERE nombre=?", conn, params=(cargo,))
    for ind in indicadores["indicador"]:
        c.execute("INSERT INTO kpis VALUES (?,?,?,?,?)",(emp_id, ind, 0, 0, 0))
    conn.commit()

# ---------------- INIT CARGOS ----------------
if pd.read_sql("SELECT * FROM cargos", conn).empty:
    base = {
        "Gerente Financiero": ["Rentabilidad","ROA","ROE","Liquidez"],
        "Recursos Humanos": ["Ausentismo","Clima","Rotación"],
        "Analista de Datos": ["Precisión","Tiempo","Sistemas"]
    }
    for cargo, inds in base.items():
        for i in inds:
            c.execute("INSERT INTO cargos VALUES (?,?)",(cargo,i))
    conn.commit()

# ---------------- MENU ----------------
menu = st.sidebar.radio("Menú",[
    "Registrar","Editar Empleado","KPIs","Escáner","Cargos","Dashboard"
])

# ---------------- REGISTRAR ----------------
if menu == "Registrar":
    st.header("➕ Registrar Empleado")

    cargos = pd.read_sql("SELECT DISTINCT nombre FROM cargos", conn)

    with st.form("form"):
        id = st.text_input("ID")
        nombre = st.text_input("Nombre")
        edad = st.number_input("Edad",18,70)
        estado = st.selectbox("Estado",["Soltero","Casado"])
        profesion = st.text_input("Profesión")
        cargo = st.selectbox("Cargo",cargos["nombre"])

        if st.form_submit_button("Guardar"):
            c.execute("INSERT OR REPLACE INTO empleados VALUES (?,?,?,?,?,?)",
                      (id,nombre,edad,estado,profesion,cargo))
            regenerar_kpis(id, cargo)
            st.success("Empleado registrado")

# ---------------- EDITAR ----------------
elif menu == "Editar Empleado":
    st.header("✏️ Editar Empleado")

    df = pd.read_sql("SELECT * FROM empleados", conn)

    emp_id = st.selectbox("Empleado", df["id"])
    data = df[df["id"]==emp_id].iloc[0]

    nombre = st.text_input("Nombre", value=data["nombre"])
    edad = st.number_input("Edad", value=int(data["edad"]))
    estado = st.selectbox("Estado",["Soltero","Casado"])
    profesion = st.text_input("Profesión", value=data["profesion"])

    cargos = pd.read_sql("SELECT DISTINCT nombre FROM cargos", conn)
    cargo = st.selectbox("Cargo", cargos["nombre"])

    if st.button("Actualizar"):
        c.execute("""UPDATE empleados 
                     SET nombre=?, edad=?, estado=?, profesion=?, cargo=? 
                     WHERE id=?""",
                  (nombre,edad,estado,profesion,cargo,emp_id))
        regenerar_kpis(emp_id, cargo)
        st.success("Actualizado")

# ---------------- KPIs ----------------
elif menu == "KPIs":
    st.header("📊 Gestión KPIs")

    df = pd.read_sql("SELECT * FROM empleados", conn)
    emp_id = st.selectbox("Empleado", df["id"])

    kpis = pd.read_sql("SELECT * FROM kpis WHERE id=?", conn, params=(emp_id,))

    for i,row in kpis.iterrows():
        col1,col2,col3 = st.columns(3)

        with col1:
            m = st.number_input("Meta",value=row["meta"],key=f"m{i}")
        with col2:
            p = st.number_input("Proyectado",value=row["proyectado"],key=f"p{i}")
        with col3:
            r = st.number_input("Real",value=row["real"],key=f"r{i}")

        if st.button(f"Guardar {row['indicador']}"):
            c.execute("""UPDATE kpis SET meta=?, real=?, proyectado=? 
                         WHERE id=? AND indicador=?""",
                      (m,r,p,emp_id,row["indicador"]))
            conn.commit()

# ---------------- ESCÁNER ----------------
elif menu == "Escáner":
    st.header("🔍 Escáner Inteligente")

    df = pd.read_sql("SELECT * FROM empleados", conn)

    if not df.empty:
        df["display"] = df["id"] + " - " + df["nombre"] + " - " + df["cargo"]

        seleccion = st.selectbox("Seleccionar Empleado", df["display"])

        emp_id = df[df["display"] == seleccion]["id"].values[0]

        data = df[df["id"] == emp_id].iloc[0]
        kpis = pd.read_sql("SELECT * FROM kpis WHERE id=?", conn, params=(emp_id,))

        col1,col2 = st.columns([1,2])

        with col1:
            st.write(data)
            st.image(generar_qr(data,kpis), width=150)

        with col2:
            st.dataframe(kpis)

            for _, row in kpis.iterrows():

                labels = ["Meta","Proyectado","Real"]
                valores = [row["meta"], row["proyectado"], row["real"]]

                fig = go.Figure()

                # BARRAS
                fig.add_trace(go.Bar(
                    x=labels,
                    y=valores,
                    marker=dict(color=["#A8D5BA","#7FB77E","#4CAF50"]),
                    text=valores,
                    textposition="outside"
                ))

                # POLÍGONO DE FRECUENCIA
                fig.add_trace(go.Scatter(
                    x=labels,
                    y=valores,
                    mode="lines+markers",
                    line=dict(color="darkgreen"),
                    name="Tendencia"
                ))

                fig.update_layout(
                    title=row["indicador"],
                    height=300
                )

                st.plotly_chart(fig, use_container_width=True)

# ---------------- CARGOS ----------------
elif menu == "Cargos":
    nombre = st.text_input("Cargo")
    inds = st.text_area("Indicadores")

    if st.button("Guardar"):
        for i in inds.split(","):
            c.execute("INSERT INTO cargos VALUES (?,?)",(nombre,i.strip()))
        conn.commit()

# ---------------- DASHBOARD ----------------
elif menu == "Dashboard":
    df = pd.read_sql("SELECT * FROM empleados", conn)
    st.dataframe(df)
