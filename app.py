import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import qrcode
from io import BytesIO

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Banco PRO", layout="wide")

# ---------------- LOGIN ----------------
USERS = {"admin": "1234"}

if "auth" not in st.session_state:
    st.session_state.auth = False

user = st.sidebar.text_input("Usuario")
password = st.sidebar.text_input("Contraseña", type="password")

if st.sidebar.button("Ingresar"):
    if USERS.get(user) == password:
        st.session_state.auth = True
    else:
        st.error("Error login")

if not st.session_state.auth:
    st.stop()

# ---------------- DB ----------------
conn = sqlite3.connect("bank.db", check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS empleados(
id TEXT PRIMARY KEY,
nombre TEXT, edad INT, estado TEXT, profesion TEXT, cargo TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS kpis(
id TEXT, indicador TEXT, meta REAL, real REAL, proyectado REAL)''')

c.execute('''CREATE TABLE IF NOT EXISTS cargos(
nombre TEXT, indicador TEXT)''')

conn.commit()

# ---------------- FUNCIONES ----------------

def generar_qr_completo(data, kpis):
    texto = f"""
ID: {data['id']}
Nombre: {data['nombre']}
Edad: {data['edad']}
Estado: {data['estado']}
Profesión: {data['profesion']}
Cargo: {data['cargo']}

--- KPIs ---
"""
    for _, row in kpis.iterrows():
        texto += f"{row['indicador']}: Meta={row['meta']}, Real={row['real']}, Proy={row['proyectado']}\n"

    img = qrcode.make(texto)
    buf = BytesIO()
    img.save(buf)
    return buf

def crear_kpis_unicos(emp_id, cargo):
    existentes = pd.read_sql(f"SELECT indicador FROM kpis WHERE id='{emp_id}'", conn)

    indicadores = pd.read_sql(f"SELECT indicador FROM cargos WHERE nombre='{cargo}'", conn)

    for ind in indicadores["indicador"]:
        if ind not in existentes["indicador"].values:
            c.execute("INSERT INTO kpis VALUES (?,?,?,?,?)",
                      (emp_id, ind, 0, 0, 0))

    conn.commit()

# ---------------- INIT CARGOS ----------------
if pd.read_sql("SELECT * FROM cargos", conn).empty:
    base = {
        "Gerente Financiero": ["Rentabilidad","ROA","ROE","Liquidez"],
        "Recursos Humanos": ["Ausentismo","Rotación","Clima"],
        "Analista de Datos": ["Precisión","Tiempo","Sistemas"]
    }

    for cargo, inds in base.items():
        for i in inds:
            c.execute("INSERT INTO cargos VALUES (?,?)",(cargo,i))
    conn.commit()

# ---------------- MENU ----------------
menu = st.sidebar.radio("Menú",[
    "Registrar","KPIs","Escáner","Dashboard","Cargos"
])

# ---------------- REGISTRAR ----------------
if menu == "Registrar":
    st.header("➕ Registro")

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

            crear_kpis_unicos(id,cargo)

            st.success("Empleado registrado correctamente")

# ---------------- KPIs ----------------
elif menu == "KPIs":
    st.header("📊 Gestión KPI")

    df = pd.read_sql("SELECT * FROM empleados", conn)

    emp_id = st.selectbox("Empleado",df["id"])

    kpis = pd.read_sql(f"SELECT * FROM kpis WHERE id='{emp_id}'", conn)

    nuevos = []

    for i,row in kpis.iterrows():
        st.subheader(row["indicador"])

        m = st.number_input("Meta",value=row["meta"],key=f"m{i}")
        r = st.number_input("Real",value=row["real"],key=f"r{i}")
        p = st.number_input("Proy",value=row["proyectado"],key=f"p{i}")

        nuevos.append((m,r,p,row["indicador"]))

    if st.button("Guardar KPIs"):
        for m,r,p,ind in nuevos:
            c.execute("UPDATE kpis SET meta=?, real=?, proyectado=? WHERE id=? AND indicador=?",
                      (m,r,p,emp_id,ind))
        conn.commit()
        st.success("KPIs guardados correctamente")

# ---------------- ESCÁNER ----------------
elif menu == "Escáner":
    st.header("🔍 Escaneo completo")

    search = st.text_input("Ingrese ID")

    emp = pd.read_sql(f"SELECT * FROM empleados WHERE id='{search}'", conn)

    if not emp.empty:
        data = emp.iloc[0]

        kpis = pd.read_sql(f"SELECT * FROM kpis WHERE id='{search}'", conn)

        st.subheader("📋 Datos")
        st.write(data)

        st.subheader("📊 KPIs")
        st.dataframe(kpis)

        qr = generar_qr_completo(data, kpis)
        st.image(qr, caption="QR completo del empleado")

        fig = go.Figure()
        fig.add_trace(go.Bar(x=kpis["indicador"], y=kpis["meta"], name="Meta"))
        fig.add_trace(go.Bar(x=kpis["indicador"], y=kpis["real"], name="Real"))
        fig.add_trace(go.Scatter(x=kpis["indicador"], y=kpis["proyectado"], mode="markers"))

        st.plotly_chart(fig)

# ---------------- DASHBOARD ----------------
elif menu == "Dashboard":
    df = pd.read_sql("SELECT * FROM empleados", conn)
    st.dataframe(df)

# ---------------- CARGOS ----------------
elif menu == "Cargos":
    st.header("⚙️ Crear cargos")

    nombre = st.text_input("Cargo")
    inds = st.text_area("Indicadores separados por coma")

    if st.button("Guardar Cargo"):
        for i in inds.split(","):
            c.execute("INSERT INTO cargos VALUES (?,?)",(nombre,i.strip()))
        conn.commit()
        st.success("Cargo creado")
