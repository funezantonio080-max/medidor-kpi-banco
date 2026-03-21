import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import qrcode
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
        "Gerente Financiero": ["Rentabilidad","ROA","ROE","Liquidez","Margen"],
        "Recursos Humanos": ["Ausentismo","Rotación","Clima Laboral","Capacitación"],
        "Analista de Datos": ["Precisión","Tiempo Respuesta","Uso Sistemas","Análisis"]
    }

    for cargo, inds in base.items():
        for i in inds:
            c.execute("INSERT INTO cargos VALUES (?,?)",(cargo,i))
    conn.commit()

# ---------------- MENU ----------------
menu = st.sidebar.radio("Menú",[
    "Registrar","KPIs","Escáner","Dashboard","Capacitaciones","Cargos"
])

# ---------------- REGISTRAR ----------------
if menu == "Registrar":
    st.header("➕ Registro de Empleado")

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
    st.header("📊 Gestión de KPIs")

    df = pd.read_sql("SELECT * FROM empleados", conn)

    if df.empty:
        st.warning("No hay empleados")
    else:
        emp_id = st.selectbox("Empleado",df["id"])

        kpis = pd.read_sql(f"SELECT * FROM kpis WHERE id='{emp_id}'", conn)

        nuevos = []

        for i,row in kpis.iterrows():
            st.subheader(row["indicador"])

            col1,col2,col3 = st.columns(3)

            with col1:
                m = st.number_input("Meta",value=float(row["meta"]),key=f"m{i}")
            with col2:
                r = st.number_input("Real",value=float(row["real"]),key=f"r{i}")
            with col3:
                p = st.number_input("Proyectado",value=float(row["proyectado"]),key=f"p{i}")

            nuevos.append((m,r,p,row["indicador"]))

        if st.button("💾 Guardar TODOS"):
            for m,r,p,ind in nuevos:
                c.execute("""UPDATE kpis 
                             SET meta=?, real=?, proyectado=? 
                             WHERE id=? AND indicador=?""",
                          (m,r,p,emp_id,ind))
            conn.commit()
            st.success("KPIs actualizados correctamente")

# ---------------- ESCÁNER ----------------
elif menu == "Escáner":
    st.header("🔍 Escaneo completo")

    search = st.text_input("Ingrese ID")

    emp = pd.read_sql(f"SELECT * FROM empleados WHERE id='{search}'", conn)

    if not emp.empty:
        data = emp.iloc[0]
        kpis = pd.read_sql(f"SELECT * FROM kpis WHERE id='{search}'", conn)

        kpis = kpis.dropna()

        col1,col2 = st.columns([1,2])

        # DATOS + QR
        with col1:
            st.subheader("📋 Datos Personales")
            st.write(data)

            qr = generar_qr_completo(data, kpis)
            st.image(qr, width=200)

        # KPIs + GRÁFICOS
        with col2:
            st.subheader("📊 KPIs Reales")
            st.dataframe(kpis)

            st.subheader("📈 Visualización por KPI")

            for i, row in kpis.iterrows():

                indicador = row["indicador"]
                meta = row["meta"]
                real = row["real"]
                proy = row["proyectado"]

                fig = go.Figure()

                fig.add_trace(go.Bar(x=["Meta"], y=[meta], name="Meta", width=0.3))
                fig.add_trace(go.Bar(x=["Real"], y=[real], name="Real", width=0.3))
                fig.add_trace(go.Bar(x=["Proyectado"], y=[proy], name="Proyectado", width=0.3))

                fig.update_layout(
                    title=f"KPI: {indicador}",
                    bargap=0.5,
                    height=300
                )

                st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("Empleado no encontrado")

# ---------------- DASHBOARD ----------------
elif menu == "Dashboard":
    st.header("📊 Dashboard")

    df = pd.read_sql("SELECT * FROM empleados", conn)

    if not df.empty:
        st.dataframe(df)
        st.bar_chart(df["cargo"].value_counts())

# ---------------- CAPACITACIONES ----------------
elif menu == "Capacitaciones":
    st.header("📚 Centro de Capacitación")

    cursos = pd.DataFrame({
        "Curso":[
            "Servicio al Cliente",
            "Análisis Financiero y Créditos",
            "Sistemas Bancarios",
            "Prevención de Fraude"
        ],
        "Área":[
            "Todos","Finanzas","Todos","Todos"
        ]
    })

    st.table(cursos)

# ---------------- CARGOS ----------------
elif menu == "Cargos":
    st.header("⚙️ Crear Cargo Nuevo")

    nombre = st.text_input("Nombre del Cargo")
    indicadores = st.text_area("Indicadores (separados por coma)")

    if st.button("Guardar Cargo"):
        for i in indicadores.split(","):
            c.execute("INSERT INTO cargos VALUES (?,?)",(nombre,i.strip()))
        conn.commit()
        st.success("Cargo creado correctamente")
