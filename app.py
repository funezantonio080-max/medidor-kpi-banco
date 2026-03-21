import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import qrcode
from io import BytesIO

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Banco Empresarial KPI", layout="wide")

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
    st.warning("Debe iniciar sesión")
    st.stop()

# ---------------- BASE DE DATOS ----------------
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

conn.commit()

# ---------------- FUNCIONES ----------------
def generar_qr(data):
    img = qrcode.make(data)
    buf = BytesIO()
    img.save(buf)
    return buf

def indicadores_por_cargo(cargo):
    if cargo == "Gerente Financiero":
        return ["Rentabilidad Financiera","ROA","ROE","Margen Financiero",
                "Crecimiento Ingresos","Gestión de Riesgo","Liquidez"]

    elif cargo == "Recursos Humanos":
        return ["Ausentismo","Tiempo Contratación","Productividad",
                "Capacitación","Clima Laboral","Retención"]

    elif cargo == "Analista de Datos":
        return ["Atención Cliente","Análisis Financiero",
                "Uso Sistemas","Precisión","Tiempo Respuesta"]

    return ["Indicador General"]

# ---------------- MENU ----------------
st.sidebar.title("🏦 Banco Empresarial")
menu = st.sidebar.radio("Menú", [
    "Dashboard",
    "Registrar",
    "KPIs",
    "Escáner",
    "Capacitaciones"
])

# ---------------- REGISTRAR ----------------
if menu == "Registrar":
    st.header("➕ Registrar Empleado")

    with st.form("form_emp"):
        id = st.text_input("ID (Ej: GER-001)")
        nombre = st.text_input("Nombre")
        edad = st.number_input("Edad",18,70)
        estado = st.selectbox("Estado Civil",["Soltero","Casado"])
        profesion = st.text_input("Profesión")
        cargo = st.selectbox("Cargo",[
            "Gerente Financiero","Recursos Humanos","Analista de Datos"
        ])

        if st.form_submit_button("Guardar"):
            c.execute("INSERT OR REPLACE INTO empleados VALUES (?,?,?,?,?,?)",
                      (id,nombre,edad,estado,profesion,cargo))

            # Crear KPIs si no existen
            for ind in indicadores_por_cargo(cargo):
                c.execute("INSERT INTO kpis VALUES (?,?,?,?,?)",
                          (id,ind,0,0,0))

            conn.commit()
            st.success("Empleado registrado correctamente")

# ---------------- KPIs (MEJORADO) ----------------
elif menu == "KPIs":
    st.header("📊 Gestión de KPIs (Gerente)")

    df = pd.read_sql("SELECT * FROM empleados", conn)

    if df.empty:
        st.warning("Primero debes registrar empleados")
    else:
        emp_id = st.selectbox("Seleccionar Empleado", df["id"])

        kpis = pd.read_sql(f"SELECT * FROM kpis WHERE id='{emp_id}'", conn)

        nuevos_datos = []

        for i, row in kpis.iterrows():
            st.subheader(row["indicador"])

            col1, col2, col3 = st.columns(3)

            with col1:
                meta = st.number_input("Meta", value=row["meta"], key=f"m{i}")
            with col2:
                real = st.number_input("Real", value=row["real"], key=f"r{i}")
            with col3:
                proy = st.number_input("Proyectado", value=row["proyectado"], key=f"p{i}")

            nuevos_datos.append((meta, real, proy, emp_id, row["indicador"]))

        if st.button("💾 Guardar TODOS los KPIs"):
            for meta, real, proy, emp_id, indicador in nuevos_datos:
                c.execute("""UPDATE kpis
                             SET meta=?, real=?, proyectado=?
                             WHERE id=? AND indicador=?""",
                          (meta, real, proy, emp_id, indicador))

            conn.commit()
            st.success("Todos los KPIs actualizados correctamente")

# ---------------- ESCÁNER ----------------
elif menu == "Escáner":
    st.header("🔍 Escaneo QR / ID")

    search = st.text_input("Ingrese ID")

    emp = pd.read_sql(f"SELECT * FROM empleados WHERE id='{search}'", conn)

    if not emp.empty:
        data = emp.iloc[0]

        col1,col2 = st.columns([1,2])

        with col1:
            st.subheader("📋 Información Personal")
            st.write(data)

            qr = generar_qr(data["id"])
            st.image(qr, caption="Código QR")

        with col2:
            st.subheader("📄 CV KPI (REAL)")

            kpis = pd.read_sql(f"SELECT * FROM kpis WHERE id='{search}'", conn)

            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=kpis["indicador"], y=kpis["meta"], name="Meta"))

            fig.add_trace(go.Bar(
                x=kpis["indicador"], y=kpis["real"], name="Real"))

            fig.add_trace(go.Scatter(
                x=kpis["indicador"], y=kpis["proyectado"],
                mode="markers", name="Proyectado"))

            st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("Empleado no encontrado")

# ---------------- DASHBOARD ----------------
elif menu == "Dashboard":
    st.header("📊 Panel Gerencial")

    df = pd.read_sql("SELECT * FROM empleados", conn)

    if not df.empty:
        st.dataframe(df)
        st.bar_chart(df["cargo"].value_counts())
    else:
        st.info("No hay empleados registrados")

# ---------------- CAPACITACIONES ----------------
elif menu == "Capacitaciones":
    st.header("📚 Centro de Capacitación")

    cursos = pd.DataFrame({
        "Curso":[
            "Servicio al Cliente",
            "Análisis Financiero y Créditos",
            "Sistemas Bancarios",
            "Prevención de Fraude y Lavado de Dinero"
        ],
        "Aplica a":[
            "Todos",
            "Gerentes y Analistas",
            "Todo el personal",
            "Todo el personal"
        ],
        "Estado":[
            "Activo",
            "Obligatorio",
            "Activo",
            "Crítico"
        ]
    })

    st.table(cursos)
