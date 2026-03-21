import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import qrcode
from io import BytesIO

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Banco Empresarial PRO", layout="wide")

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

# NUEVA TABLA DE CARGOS
c.execute('''CREATE TABLE IF NOT EXISTS cargos(
nombre TEXT,
indicador TEXT
)''')

conn.commit()

# ---------------- FUNCIONES ----------------
def generar_qr(data):
    img = qrcode.make(data)
    buf = BytesIO()
    img.save(buf)
    return buf

# ---------------- INICIALIZAR CARGOS ----------------
def init_cargos():
    cargos_base = {
        "Gerente Financiero": ["Rentabilidad","ROA","ROE","Margen","Liquidez"],
        "Recursos Humanos": ["Ausentismo","Rotación","Clima Laboral"],
        "Analista de Datos": ["Precisión","Tiempo","Sistemas"]
    }

    for cargo, indicadores in cargos_base.items():
        for ind in indicadores:
            c.execute("INSERT INTO cargos VALUES (?,?)", (cargo, ind))
    conn.commit()

if pd.read_sql("SELECT * FROM cargos", conn).empty:
    init_cargos()

# ---------------- MENU ----------------
st.sidebar.title("🏦 Banco PRO")
menu = st.sidebar.radio("Menú", [
    "Dashboard",
    "Registrar",
    "KPIs",
    "Escáner",
    "Capacitaciones",
    "Gestión de Cargos"
])

# ---------------- GESTIÓN DE CARGOS ----------------
if menu == "Gestión de Cargos":
    st.header("⚙️ Crear Nuevo Cargo")

    nuevo_cargo = st.text_input("Nombre del cargo")
    indicadores = st.text_area("Indicadores (separados por coma)")

    if st.button("Crear Cargo"):
        lista = indicadores.split(",")

        for ind in lista:
            c.execute("INSERT INTO cargos VALUES (?,?)",
                      (nuevo_cargo, ind.strip()))

        conn.commit()
        st.success("Cargo creado con KPIs")

# ---------------- REGISTRAR ----------------
elif menu == "Registrar":
    st.header("➕ Registrar Empleado")

    cargos = pd.read_sql("SELECT DISTINCT nombre FROM cargos", conn)

    with st.form("form"):
        id = st.text_input("ID")
        nombre = st.text_input("Nombre")
        edad = st.number_input("Edad",18,70)
        estado = st.selectbox("Estado Civil",["Soltero","Casado"])
        profesion = st.text_input("Profesión")
        cargo = st.selectbox("Cargo", cargos["nombre"])

        if st.form_submit_button("Guardar"):
            c.execute("INSERT OR REPLACE INTO empleados VALUES (?,?,?,?,?,?)",
                      (id,nombre,edad,estado,profesion,cargo))

            # crear KPIs automáticamente
            indicadores = pd.read_sql(f"SELECT indicador FROM cargos WHERE nombre='{cargo}'", conn)

            for ind in indicadores["indicador"]:
                c.execute("INSERT INTO kpis VALUES (?,?,?,?,?)",
                          (id,ind,0,0,0))

            conn.commit()
            st.success("Empleado creado")

# ---------------- KPIs ----------------
elif menu == "KPIs":
    st.header("📊 KPIs Gerenciales")

    df = pd.read_sql("SELECT * FROM empleados", conn)

    emp_id = st.selectbox("Empleado", df["id"])

    kpis = pd.read_sql(f"SELECT * FROM kpis WHERE id='{emp_id}'", conn)

    nuevos = []

    for i,row in kpis.iterrows():
        st.subheader(row["indicador"])

        m = st.number_input("Meta", value=row["meta"], key=f"m{i}")
        r = st.number_input("Real", value=row["real"], key=f"r{i}")
        p = st.number_input("Proyectado", value=row["proyectado"], key=f"p{i}")

        nuevos.append((m,r,p,emp_id,row["indicador"]))

    if st.button("Guardar KPIs"):
        for m,r,p,e,i in nuevos:
            c.execute("UPDATE kpis SET meta=?, real=?, proyectado=? WHERE id=? AND indicador=?",
                      (m,r,p,e,i))
        conn.commit()
        st.success("KPIs actualizados")

# ---------------- ESCÁNER ----------------
elif menu == "Escáner":
    st.header("🔍 Escaneo")

    search = st.text_input("ID")

    emp = pd.read_sql(f"SELECT * FROM empleados WHERE id='{search}'", conn)

    if not emp.empty:
        data = emp.iloc[0]

        st.write(data)
        st.image(generar_qr(data["id"]))

        kpis = pd.read_sql(f"SELECT * FROM kpis WHERE id='{search}'", conn)

        fig = go.Figure()
        fig.add_trace(go.Bar(x=kpis["indicador"], y=kpis["meta"], name="Meta"))
        fig.add_trace(go.Bar(x=kpis["indicador"], y=kpis["real"], name="Real"))
        fig.add_trace(go.Scatter(x=kpis["indicador"], y=kpis["proyectado"], mode="markers"))

        st.plotly_chart(fig)

# ---------------- DASHBOARD ----------------
elif menu == "Dashboard":
    df = pd.read_sql("SELECT * FROM empleados", conn)
    st.dataframe(df)
    if not df.empty:
        st.bar_chart(df["cargo"].value_counts())

# ---------------- CAPACITACIONES ----------------
elif menu == "Capacitaciones":
    st.header("📚 Capacitaciones")

    cursos = pd.DataFrame({
        "Curso":["Servicio Cliente","Análisis Financiero","Sistemas","Fraude"],
        "Área":["Todos","Finanzas","Todos","Todos"]
    })

    st.table(cursos)
