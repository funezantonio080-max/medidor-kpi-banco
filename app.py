import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import qrcode
import json
import base64
from io import BytesIO

# =========================================================
# CONFIGURACION
# =========================================================

st.set_page_config(
    page_title="BANCO KPI PRO",
    layout="wide",
    page_icon="🏦"
)

# =========================================================
# FONDO EJECUTIVO
# =========================================================

def get_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

try:

    img = get_base64("fondo.png")

    st.markdown(f"""
    <style>

    [data-testid="stAppViewContainer"] {{

        background-image:
        linear-gradient(
        rgba(0,0,0,0.55),
        rgba(0,0,0,0.55)),
        url("data:image/png;base64,{img}");

        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}

    [data-testid="stHeader"] {{
        background: rgba(0,0,0,0);
    }}

    [data-testid="stSidebar"] {{
        background: rgba(0,0,0,0.85);
    }}

    h1,h2,h3,h4,h5,h6,p,label,div {{
        color:white !important;
    }}

    .stDataFrame {{
        background: rgba(0,0,0,0.5);
    }}

    </style>
    """, unsafe_allow_html=True)

except:
    st.warning("NO SE ENCONTRO fondo.png")

# =========================================================
# LOGIN
# =========================================================

USERS = {
    "ADMIN": "1234"
}

if "auth" not in st.session_state:
    st.session_state.auth = False

st.sidebar.title("🔐 LOGIN")

user = st.sidebar.text_input(
    "USUARIO"
).upper()

password = st.sidebar.text_input(
    "CONTRASEÑA",
    type="password"
)

if st.sidebar.button("INGRESAR"):

    if USERS.get(user) == password:

        st.session_state.auth = True

    else:

        st.sidebar.error("ACCESO INCORRECTO")

if not st.session_state.auth:

    st.markdown("""
    <h1 style='text-align:center;font-size:70px;'>
    🏦 GERENCIA DE BANCO KPI
    </h1>
    """, unsafe_allow_html=True)

    st.markdown("""
    <h2 style='text-align:center;'>
    CENTRO EJECUTIVO DE INDICADORES BANCARIOS
    </h2>
    """, unsafe_allow_html=True)

    st.stop()

# =========================================================
# BASE DE DATOS
# =========================================================

conn = sqlite3.connect(
    "bank.db",
    check_same_thread=False
)

c = conn.cursor()

# =========================================================
# TABLAS
# =========================================================

c.execute("""
CREATE TABLE IF NOT EXISTS empleados(
    id TEXT PRIMARY KEY,
    nombre TEXT,
    edad INTEGER,
    estado TEXT,
    profesion TEXT,
    cargo TEXT,
    foto BLOB
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS kpis(
    id TEXT,
    indicador TEXT,
    meta REAL,
    real REAL,
    proyectado REAL
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS cargos(
    nombre TEXT,
    indicador TEXT
)
""")

conn.commit()

# =========================================================
# CARGOS BASE
# =========================================================

if pd.read_sql(
    "SELECT * FROM cargos",
    conn
).empty:

    base = {

        "GERENTE FINANCIERO": [
            "RENTABILIDAD",
            "ROA",
            "ROE",
            "LIQUIDEZ"
        ],

        "RECURSOS HUMANOS": [
            "AUSENTISMO",
            "CLIMA",
            "ROTACION"
        ],

        "ANALISTA DE DATOS": [
            "PRECISION",
            "TIEMPO",
            "SISTEMAS"
        ]
    }

    for cargo, inds in base.items():

        for i in inds:

            c.execute(
                "INSERT INTO cargos VALUES (?,?)",
                (cargo, i)
            )

    conn.commit()

# =========================================================
# FUNCIONES
# =========================================================

def regenerar_kpis(emp_id, cargo):

    c.execute(
        "DELETE FROM kpis WHERE id=?",
        (emp_id,)
    )

    indicadores = pd.read_sql(
        "SELECT indicador FROM cargos WHERE nombre=?",
        conn,
        params=(cargo,)
    )

    for ind in indicadores["indicador"]:

        c.execute("""
        INSERT INTO kpis
        VALUES (?,?,?,?,?)
        """, (
            emp_id,
            ind,
            0,
            0,
            0
        ))

    conn.commit()

def generar_qr(data, kpis):

    contenido = {

        "id": data["id"],
        "nombre": data["nombre"],
        "cargo": data["cargo"],
        "kpis": kpis.to_dict(
            orient="records"
        )
    }

    img = qrcode.make(
        json.dumps(contenido)
    )

    buf = BytesIO()

    img.save(buf)

    return buf

def mayus(df):

    df = df.copy()

    for col in df.columns:

        df[col] = df[col].apply(
            lambda x:
            x.upper()
            if isinstance(x, str)
            else x
        )

    df.columns = [
        c.upper()
        for c in df.columns
    ]

    return df

# =========================================================
# MENU
# =========================================================

menu = st.sidebar.radio(
    "MENÚ",
    [
        "DASHBOARD",
        "REGISTRAR",
        "EDITAR",
        "KPIS",
        "ESCÁNER",
        "CARGOS"
    ]
)

# =========================================================
# DASHBOARD
# =========================================================

if menu == "DASHBOARD":

    st.title("📊 DASHBOARD GENERAL")

    empleados = pd.read_sql(
        "SELECT * FROM empleados",
        conn
    )

    kpis = pd.read_sql(
        "SELECT * FROM kpis",
        conn
    )

    total_empleados = len(empleados)

    total_kpis = len(kpis)

    cumplimiento = 0

    if not kpis.empty:

        cumplimiento = round(
            (kpis["real"].sum() /
            (kpis["meta"].sum() + 1)) * 100,
            1
        )

    riesgo = len(
        kpis[kpis["real"] < kpis["meta"]]
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "👥 EMPLEADOS",
            total_empleados
        )

    with c2:
        st.metric(
            "📈 KPIs",
            total_kpis
        )

    with c3:
        st.metric(
            "✅ CUMPLIMIENTO",
            f"{cumplimiento}%"
        )

    with c4:
        st.metric(
            "⚠️ EN RIESGO",
            riesgo
        )

    st.markdown("---")

    if not empleados.empty:

        empleados_view = empleados.drop(
            columns=["foto"],
            errors="ignore"
        )

        st.dataframe(
            mayus(empleados_view)
        )

    if not kpis.empty:

        resumen = kpis.groupby(
            "indicador"
        )["real"].sum()

        st.subheader(
            "📊 RENDIMIENTO KPI"
        )

        st.bar_chart(resumen)

# =========================================================
# REGISTRAR
# =========================================================

elif menu == "REGISTRAR":

    st.title("➕ REGISTRO DE EMPLEADO")

    cargos = pd.read_sql(
        "SELECT DISTINCT nombre FROM cargos",
        conn
    )

    with st.form("form_reg"):

        col1, col2, col3 = st.columns(3)

        with col1:

            id = st.text_input(
                "ID"
            ).upper()

            nombre = st.text_input(
                "NOMBRE"
            ).upper()

        with col2:

            edad = st.number_input(
                "EDAD",
                18,
                70
            )

            estado = st.selectbox(
                "ESTADO",
                ["SOLTERO","CASADO"]
            )

        with col3:

            profesion = st.text_input(
                "PROFESIÓN"
            ).upper()

            cargo = st.selectbox(
                "CARGO",
                cargos["nombre"]
            )

        foto = st.file_uploader(
            "FOTO",
            type=["jpg","png"]
        )

        if st.form_submit_button(
            "GUARDAR"
        ):

            img = foto.read() if foto else None

            c.execute("""
            INSERT OR REPLACE INTO empleados
            VALUES (?,?,?,?,?,?,?)
            """, (
                id,
                nombre,
                edad,
                estado,
                profesion,
                cargo,
                img
            ))

            regenerar_kpis(id, cargo)

            st.success(
                "EMPLEADO REGISTRADO"
            )

# =========================================================
# EDITAR
# =========================================================

elif menu == "EDITAR":

    st.title("✏️ EDITAR EMPLEADO")

    df = pd.read_sql(
        "SELECT * FROM empleados",
        conn
    )

    if df.empty:

        st.warning(
            "NO HAY EMPLEADOS"
        )

    else:

        emp_id = st.selectbox(
            "EMPLEADO",
            df["id"]
        )

        data = df[
            df["id"] == emp_id
        ].iloc[0]

        nombre = st.text_input(
            "NOMBRE",
            value=data["nombre"]
        ).upper()

        edad = st.number_input(
            "EDAD",
            value=int(data["edad"])
        )

        estado = st.selectbox(
            "ESTADO",
            ["SOLTERO","CASADO"]
        )

        cargos = pd.read_sql(
            "SELECT DISTINCT nombre FROM cargos",
            conn
        )

        cargo = st.selectbox(
            "CARGO",
            cargos["nombre"]
        )

        foto = st.file_uploader(
            "ACTUALIZAR FOTO",
            type=["jpg","png"]
        )

        if st.button(
            "ACTUALIZAR"
        ):

            img = foto.read() if foto else data["foto"]

            c.execute("""
            UPDATE empleados
            SET nombre=?,
                edad=?,
                estado=?,
                cargo=?,
                foto=?
            WHERE id=?
            """, (
                nombre,
                edad,
                estado,
                cargo,
                img,
                emp_id
            ))

            regenerar_kpis(
                emp_id,
                cargo
            )

            conn.commit()

            st.success(
                "ACTUALIZADO"
            )

# =========================================================
# KPIS
# =========================================================

elif menu == "KPIS":

    st.title("📊 KPIs")

    df = pd.read_sql(
        "SELECT * FROM empleados",
        conn
    )

    if not df.empty:

        emp_id = st.selectbox(
            "EMPLEADO",
            df["id"]
        )

        kpis = pd.read_sql(
            "SELECT * FROM kpis WHERE id=?",
            conn,
            params=(emp_id,)
        )

        for i, row in kpis.iterrows():

            st.subheader(
                row["indicador"]
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                m = st.number_input(
                    "META",
                    value=float(row["meta"]),
                    key=f"m{i}"
                )

            with col2:

                p = st.number_input(
                    "PROYECTADO",
                    value=float(row["proyectado"]),
                    key=f"p{i}"
                )

            with col3:

                r = st.number_input(
                    "REAL",
                    value=float(row["real"]),
                    key=f"r{i}"
                )

            if st.button(
                f"GUARDAR {row['indicador']}"
            ):

                c.execute("""
                UPDATE kpis
                SET meta=?,
                    real=?,
                    proyectado=?
                WHERE id=?
                AND indicador=?
                """, (
                    m,
                    r,
                    p,
                    emp_id,
                    row["indicador"]
                ))

                conn.commit()

                st.success(
                    "KPI ACTUALIZADO"
                )

# =========================================================
# ESCANER
# =========================================================

elif menu == "ESCÁNER":

    st.title("🔍 ESCÁNER")

    df = pd.read_sql(
        "SELECT * FROM empleados",
        conn
    )

    if not df.empty:

        df["display"] = (
            df["id"]
            + " - "
            + df["nombre"]
            + " - "
            + df["cargo"]
        )

        sel = st.selectbox(
            "SELECCIONAR",
            df["display"]
        )

        emp_id = df[
            df["display"] == sel
        ]["id"].values[0]

        data = df[
            df["id"] == emp_id
        ].iloc[0]

        kpis = pd.read_sql(
            "SELECT * FROM kpis WHERE id=?",
            conn,
            params=(emp_id,)
        )

        col1, col2 = st.columns([1,2])

        with col1:

            st.dataframe(
                mayus(
                    pd.DataFrame([data]).drop(
                        columns=["foto"],
                        errors="ignore"
                    )
                )
            )

            if data["foto"]:

                st.image(
                    data["foto"],
                    width=140
                )

            st.image(
                generar_qr(data, kpis),
                width=140
            )

        with col2:

            st.dataframe(
                mayus(kpis)
            )

            for i, row in kpis.iterrows():

                labels = [
                    "META",
                    "PROYECTADO",
                    "REAL"
                ]

                valores = [
                    row["meta"],
                    row["proyectado"],
                    row["real"]
                ]

                fig = go.Figure()

                fig.add_trace(go.Bar(
                    x=labels,
                    y=valores,
                    marker=dict(
                        color=[
                            "#A8D5BA",
                            "#7FB77E",
                            "#4CAF50"
                        ]
                    ),
                    width=0.25
                ))

                fig.add_trace(go.Scatter(
                    x=labels,
                    y=valores,
                    mode="lines+markers",
                    showlegend=False
                ))

                st.plotly_chart(
                    fig,
                    key=f"graf_{i}"
                )

# =========================================================
# CARGOS
# =========================================================

elif menu == "CARGOS":

    st.title("⚙️ CARGOS")

    cargos = pd.read_sql(
        "SELECT DISTINCT nombre FROM cargos",
        conn
    )

    cargo_sel = st.selectbox(
        "CARGO",
        cargos["nombre"]
    )

    kpis = pd.read_sql(
        "SELECT indicador FROM cargos WHERE nombre=?",
        conn,
        params=(cargo_sel,)
    )

    st.write(
        "KPIs:",
        kpis["indicador"].tolist()
    )

    nuevo = st.text_input(
        "NUEVO KPI"
    )

    if st.button(
        "AGREGAR KPI"
    ):

        c.execute(
            "INSERT INTO cargos VALUES (?,?)",
            (
                cargo_sel,
                nuevo.upper()
            )
        )

        conn.commit()

        st.success(
            "KPI AGREGADO"
        )

    eliminar = st.selectbox(
        "ELIMINAR KPI",
        kpis["indicador"]
    )

    if st.button(
        "ELIMINAR KPI"
    ):

        c.execute("""
        DELETE FROM cargos
        WHERE nombre=?
        AND indicador=?
        """, (
            cargo_sel,
            eliminar
        ))

        conn.commit()

        st.success(
            "KPI ELIMINADO"
        )
