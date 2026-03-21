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

# ---------------- EDITAR EMPLEADO ----------------
elif menu == "Editar Empleado":
    st.header("✏️ Editar Empleado")

    df = pd.read_sql("SELECT * FROM empleados", conn)

    if not df.empty:
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

            st.success("Empleado actualizado")

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
            r = st.number_input("Real",value=row["real"],key=f"r{i}")
        with col3:
            p = st.number_input("Proy",value=row["proyectado"],key=f"p{i}")

        if st.button(f"Guardar {row['indicador']}"):
            c.execute("""UPDATE kpis SET meta=?, real=?, proyectado=? 
                         WHERE id=? AND indicador=?""",
                      (m,r,p,emp_id,row["indicador"]))
            conn.commit()

# ---------------- ESCÁNER ----------------
elif menu == "Escáner":
    st.header("🔍 Escáner")

    search = st.text_input("ID")

    emp = pd.read_sql("SELECT * FROM empleados WHERE id=?", conn, params=(search,))

    if not emp.empty:
        data = emp.iloc[0]
        kpis = pd.read_sql("SELECT * FROM kpis WHERE id=?", conn, params=(search,))

        st.write(data)
        st.image(generar_qr(data,kpis), width=150)

        for _, row in kpis.iterrows():
            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=["Meta","Real","Proyectado"],
                y=[row["meta"],row["real"],row["proyectado"]],
                marker=dict(color=["#A8D5BA","#4CAF50","#7FB77E"]),
                text=[row["meta"],row["real"],row["proyectado"]],
                textposition="outside",
                width=0.4
            ))

            fig.update_layout(title=row["indicador"], height=300)
            st.plotly_chart(fig)

# ---------------- CARGOS ----------------
elif menu == "Cargos":
    st.header("⚙️ Gestión de Cargos")

    cargos = pd.read_sql("SELECT DISTINCT nombre FROM cargos", conn)
    cargo_sel = st.selectbox("Seleccionar Cargo", cargos["nombre"])

    kpis = pd.read_sql("SELECT * FROM cargos WHERE nombre=?", conn, params=(cargo_sel,))
    st.write("KPIs actuales:", kpis["indicador"].tolist())

    nuevo = st.text_input("Nuevo KPI")

    if st.button("Agregar KPI"):
        c.execute("INSERT INTO cargos VALUES (?,?)",(cargo_sel,nuevo))
        conn.commit()
        st.success("KPI agregado")

    eliminar = st.selectbox("Eliminar KPI", kpis["indicador"])

    if st.button("Eliminar KPI"):
        c.execute("DELETE FROM cargos WHERE nombre=? AND indicador=?", (cargo_sel, eliminar))
        conn.commit()
        st.success("KPI eliminado")

    sobrescribir = st.text_area("Sobrescribir KPIs (separados por coma)")

    if st.button("Sobrescribir TODO"):
        c.execute("DELETE FROM cargos WHERE nombre=?", (cargo_sel,))
        for i in sobrescribir.split(","):
            c.execute("INSERT INTO cargos VALUES (?,?)",(cargo_sel,i.strip()))
        conn.commit()
        st.success("KPIs actualizados completamente")

# ---------------- DASHBOARD ----------------
elif menu == "Dashboard":
    df = pd.read_sql("SELECT * FROM empleados", conn)
    st.dataframe(df)
