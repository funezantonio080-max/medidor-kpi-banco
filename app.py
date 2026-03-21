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

def generar_qr_completo(data, kpis):
    contenido = {
        "id": data["id"],
        "nombre": data["nombre"],
        "edad": int(data["edad"]),
        "estado": data["estado"],
        "profesion": data["profesion"],
        "cargo": data["cargo"],
        "kpis": kpis.to_dict(orient="records")
    }

    data_json = json.dumps(contenido, separators=(",", ":"))

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=6,
        border=2
    )

    qr.add_data(data_json)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf)
    return buf

# 🔥 CORREGIDO
def crear_kpis_por_cargo(emp_id, cargo):
    # BORRAR KPIs anteriores (evita mezcla)
    c.execute("DELETE FROM kpis WHERE id=?", (emp_id,))

    indicadores = pd.read_sql(
        "SELECT indicador FROM cargos WHERE nombre=?", conn, params=(cargo,)
    )

    for ind in indicadores["indicador"]:
        c.execute(
            "INSERT INTO kpis VALUES (?,?,?,?,?)",
            (emp_id, ind, 0, 0, 0)
        )

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
            c.execute(
                "INSERT OR REPLACE INTO empleados VALUES (?,?,?,?,?,?)",
                (id,nombre,edad,estado,profesion,cargo)
            )

            crear_kpis_por_cargo(id, cargo)

            st.success("Empleado registrado correctamente")

# ---------------- KPIs ----------------
elif menu == "KPIs":
    st.header("📊 Gestión de KPIs")

    df = pd.read_sql("SELECT * FROM empleados", conn)

    if not df.empty:
        emp_id = st.selectbox("Empleado",df["id"])

        kpis = pd.read_sql(
            "SELECT * FROM kpis WHERE id=?", conn, params=(emp_id,)
        )

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

        if st.button("💾 Guardar KPIs"):
            for m,r,p,ind in nuevos:
                c.execute(
                    "UPDATE kpis SET meta=?, real=?, proyectado=? WHERE id=? AND indicador=?",
                    (m,r,p,emp_id,ind)
                )
            conn.commit()
            st.success("KPIs actualizados")

# ---------------- ESCÁNER ----------------
elif menu == "Escáner":
    st.header("🔍 Escaneo")

    search = st.text_input("Ingrese ID")

    emp = pd.read_sql(
        "SELECT * FROM empleados WHERE id=?", conn, params=(search,)
    )

    if not emp.empty:
        data = emp.iloc[0]
        kpis = pd.read_sql(
            "SELECT * FROM kpis WHERE id=?", conn, params=(search,)
        )

        col1,col2 = st.columns([1,2])

        with col1:
            st.write(data)
            qr = generar_qr_completo(data, kpis)
            st.image(qr, width=180)

        with col2:
            st.dataframe(kpis)

            for _, row in kpis.iterrows():

                fig = go.Figure()

                # COLORES SUAVES CORRECTOS
                colors = ["#A8D5BA", "#4CAF50", "#7FB77E"]

                values = [row["meta"], row["real"], row["proyectado"]]
                labels = ["Meta","Real","Proyectado"]

                fig.add_trace(go.Bar(
                    x=labels,
                    y=values,
                    marker=dict(color=colors),
                    text=values,
                    textposition='outside',
                    width=0.4
                ))

                fig.update_layout(
                    title=f"KPI: {row['indicador']}",
                    showlegend=False,
                    plot_bgcolor="white",
                    height=300
                )

                st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("Empleado no encontrado")

# ---------------- DASHBOARD ----------------
elif menu == "Dashboard":
    df = pd.read_sql("SELECT * FROM empleados", conn)
    st.dataframe(df)

# ---------------- CAPACITACIONES ----------------
elif menu == "Capacitaciones":
    st.table(pd.DataFrame({
        "Curso":["Servicio Cliente","Finanzas","Sistemas","Fraude"]
    }))

# ---------------- CARGOS ----------------
elif menu == "Cargos":
    nombre = st.text_input("Cargo")
    inds = st.text_area("Indicadores")

    if st.button("Guardar"):
        for i in inds.split(","):
            c.execute("INSERT INTO cargos VALUES (?,?)",(nombre,i.strip()))
        conn.commit()
