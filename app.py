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
        st.sidebar.error("ACCESO INCORRECTO")

if not st.session_state.auth:
    st.stop()

# ---------------- DB ----------------
conn = sqlite3.connect("bank.db", check_same_thread=False)
c = conn.cursor()

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

# ---------------- INIT CARGOS ----------------
if pd.read_sql("SELECT * FROM cargos", conn).empty:
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
    indicadores = pd.read_sql(
        "SELECT indicador FROM cargos WHERE nombre=?",
        conn, params=(cargo,)
    )
    for ind in indicadores["indicador"]:
        c.execute("INSERT INTO kpis VALUES (?,?,?,?,?)",
                  (emp_id, ind, 0, 0, 0))
    conn.commit()

def generar_qr(data, kpis):
    contenido = {
        "id": data["id"],
        "nombre": data["nombre"],
        "cargo": data["cargo"],
        "kpis": kpis.to_dict(orient="records")
    }
    img = qrcode.make(json.dumps(contenido))
    buf = BytesIO()
    img.save(buf)
    return buf

def mayus(df):
    df = df.copy()
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: x.upper() if isinstance(x, str) else x
        )
    df.columns = [c.upper() for c in df.columns]
    return df

# ---------------- MENU ----------------
menu = st.sidebar.radio("MENÚ", [
    "DASHBOARD",
    "REGISTRAR",
    "EDITAR",
    "KPIS",
    "ESCÁNER",
    "CARGOS"
])

# =========================================================
# DASHBOARD PREMIUM BANCO KPI V3
# =========================================================

if menu == "DASHBOARD":

    st.markdown("""
<style>

.card{

background:
linear-gradient(
180deg,
#071120,
#0D1C35
);

border-radius:22px;

padding:20px;

border:

1px solid
rgba(
57,
255,
20,
.15
);

box-shadow:

0 0 35px
rgba(
57,
255,
20,
.08
);

}

.top{

background:
linear-gradient(
145deg,
#071120,
#112347
);

padding:18px;

border-radius:18px;

border:
1px solid
rgba(
57,
255,
20,
.20
);

text-align:center;

}

.numero{

font-size:38px;

font-weight:800;

color:#39FF14;

}

.valor{

font-size:26px;

font-weight:700;

color:#39FF14;

}

</style>
""",
unsafe_allow_html=True)

    empleados = pd.read_sql(
        "SELECT * FROM empleados",
        conn
    )

    kpis = pd.read_sql(
        "SELECT * FROM kpis",
        conn
    )

    total_emp=len(
        empleados
    )

    total_kpi=len(
        kpis
    )

    cumplimiento=0

    if not kpis.empty:

        cumplimiento=round(

            (
                kpis["real"].sum()

                /

                (
                    kpis["meta"].sum()
                    +1
                )

            )

            *100,

            2

        )

    riesgo=0

    if not kpis.empty:

        riesgo=len(

            kpis[
                kpis["real"]
                <
                kpis["meta"]
            ]

        )

    objetivo=max(
        total_kpi-riesgo,
        0
    )

    st.markdown("""
<h1 style='text-align:center;color:white;'>

🏦 DASHBOARD EJECUTIVO

</h1>

<h2 style='
text-align:center;
color:#39FF14;
'>

GERENCIA DE BANCO KPI

</h2>

""",
unsafe_allow_html=True)

    c1,c2,c3,c4,c5=st.columns(5)

    tarjetas=[

("COLABORADORES",total_emp),

("KPIs",total_kpi),

("CUMPLIMIENTO",f"{cumplimiento}%"),

("OBJETIVO",objetivo),

("RIESGO",riesgo)

]

    for col,d in zip(
        [c1,c2,c3,c4,c5],
        tarjetas
    ):

        with col:

            st.markdown(f"""

<div class='top'>

<div class='numero'>

{d[1]}

</div>

{d[0]}

</div>

""",
unsafe_allow_html=True)

    st.markdown("---")

    if not kpis.empty:

        for x in range(

            0,

            len(kpis),

            2

        ):

            columnas=st.columns(2)

            for j,col in enumerate(columnas):

                if x+j<len(kpis):

                    row=kpis.iloc[
                        x+j
                    ]

                    with col:

                        st.markdown(
                            "<div class='card'>",
                            unsafe_allow_html=True
                        )

                        meta=max(
                            row["meta"],
                            1
                        )

                        proy=row[
                            "proyectado"
                        ]

                        real=row[
                            "real"
                        ]

                        porcentaje=round(

                            (
                                real
                                /
                                meta
                            )

                            *100,

                            2

                        )

                        fig=go.Figure()

                        fig.add_trace(

go.Pie(

values=[

real,

max(
meta-real,
1
)

],

hole=.62,

textinfo="none",

marker=dict(

colors=[

"#39FF14",

"#17304B"

]

)

)

)

                        fig.update_layout(

height=430,

paper_bgcolor=
"rgba(0,0,0,0)",

annotations=[

dict(

text=f"""

<b>

{porcentaje}%

</b>

<br>

Cumplimiento

""",

showarrow=False,

font=dict(

size=24,

color="white"

)

)

]

)

                        a,b=st.columns(
                            [1.5,1]
                        )

                        with a:

                            st.subheader(
                                row["indicador"]
                            )

                            st.plotly_chart(

fig,

use_container_width=True

)

                        with b:

                            st.markdown(
                                "<br>",
                                unsafe_allow_html=True
                            )

                            st.write(
                                "🔵 META"
                            )

                            st.markdown(

f"""
### {meta:,.2f}
"""

)

                            st.write(
                                "🟡 PROYECTADO"
                            )

                            st.markdown(

f"""
### {proy:,.2f}
"""

)

                            st.write(
                                "🟢 REAL"
                            )

                            st.markdown(

f"""
### {real:,.2f}
"""

)

                            st.markdown(
                                "---"
                            )

                            st.markdown(

f"""

<div class='valor'>

{porcentaje}%

</div>

"""

,

unsafe_allow_html=True

)

                            if porcentaje>=100:

                                st.success(
"▲ Por encima de la meta"
                                )

                            else:

                                st.warning(
"▼ Debajo meta"
                                )

                        st.markdown(
                            "</div>",
                            unsafe_allow_html=True
                        )
# =========================================================
# REGISTRAR
# =========================================================
elif menu == "REGISTRAR":
    st.title("➕ REGISTRO DE EMPLEADO")

    cargos = pd.read_sql("SELECT DISTINCT nombre FROM cargos", conn)

    with st.form("form_reg"):
        col1, col2, col3 = st.columns(3)

        with col1:
            id = st.text_input("ID").upper()
            nombre = st.text_input("NOMBRE").upper()

        with col2:
            edad = st.number_input("EDAD", 18, 70)
            estado = st.selectbox("ESTADO", ["SOLTERO","CASADO"])

        with col3:
            profesion = st.text_input("PROFESIÓN").upper()
            cargo = st.selectbox("CARGO", cargos["nombre"])

        foto = st.file_uploader("FOTO", type=["jpg","png"])

        if st.form_submit_button("GUARDAR"):
            img = foto.read() if foto else None

            c.execute("""
            INSERT OR REPLACE INTO empleados
            VALUES (?,?,?,?,?,?,?)
            """, (id,nombre,edad,estado,profesion,cargo,img))

            regenerar_kpis(id, cargo)
            st.success("EMPLEADO REGISTRADO")

# =========================================================
# EDITAR
# =========================================================
elif menu == "EDITAR":
    st.title("✏️ EDITAR EMPLEADO")

    df = pd.read_sql("SELECT * FROM empleados", conn)

    if df.empty:
        st.warning("NO HAY EMPLEADOS")
    else:
        emp_id = st.selectbox("EMPLEADO", df["id"])
        data = df[df["id"] == emp_id].iloc[0]

        nombre = st.text_input("NOMBRE", value=data["nombre"]).upper()
        edad = st.number_input("EDAD", value=int(data["edad"]))
        estado = st.selectbox("ESTADO", ["SOLTERO","CASADO"])

        cargos = pd.read_sql("SELECT DISTINCT nombre FROM cargos", conn)
        cargo = st.selectbox("CARGO", cargos["nombre"])

        foto = st.file_uploader("ACTUALIZAR FOTO", type=["jpg","png"])

        if st.button("ACTUALIZAR"):
            img = foto.read() if foto else data["foto"]

            c.execute("""
            UPDATE empleados
            SET nombre=?, edad=?, estado=?, cargo=?, foto=?
            WHERE id=?
            """, (nombre,edad,estado,cargo,img,emp_id))

            regenerar_kpis(emp_id, cargo)
            st.success("ACTUALIZADO")

# =========================================================
# KPIS
# =========================================================
elif menu == "KPIS":
    st.title("📊 KPIs")

    df = pd.read_sql("SELECT * FROM empleados", conn)

    if not df.empty:
        emp_id = st.selectbox("EMPLEADO", df["id"])
        kpis = pd.read_sql("SELECT * FROM kpis WHERE id=?", conn, params=(emp_id,))

        for i, row in kpis.iterrows():
            st.subheader(row["indicador"])

            col1, col2, col3 = st.columns(3)

            with col1:
                m = st.number_input("META", value=row["meta"], key=f"m{i}")
            with col2:
                p = st.number_input("PROYECTADO", value=row["proyectado"], key=f"p{i}")
            with col3:
                r = st.number_input("REAL", value=row["real"], key=f"r{i}")

            if st.button(f"GUARDAR {row['indicador']}"):
                c.execute("""
                UPDATE kpis SET meta=?, real=?, proyectado=?
                WHERE id=? AND indicador=?
                """, (m,r,p,emp_id,row["indicador"]))
                conn.commit()

# =========================================================
# ESCÁNER (CON GRÁFICOS)
# =========================================================
elif menu == "ESCÁNER":
    st.title("🔍 ESCÁNER")

    df = pd.read_sql("SELECT * FROM empleados", conn)

    if not df.empty:
        df["display"] = df["id"] + " - " + df["nombre"] + " - " + df["cargo"]

        sel = st.selectbox("SELECCIONAR", df["display"])
        emp_id = df[df["display"] == sel]["id"].values[0]

        data = df[df["id"] == emp_id].iloc[0]
        kpis = pd.read_sql("SELECT * FROM kpis WHERE id=?", conn, params=(emp_id,))

        col1, col2 = st.columns([1,2])

        with col1:
            st.dataframe(mayus(pd.DataFrame([data]).drop(columns=["foto"], errors="ignore")))

            if data["foto"]:
                st.image(data["foto"], width=140)

            st.image(generar_qr(data,kpis), width=140)

        with col2:
            st.dataframe(mayus(kpis))

            for i, row in kpis.iterrows():

                labels = ["META","PROYECTADO","REAL"]
                valores = [row["meta"], row["proyectado"], row["real"]]

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

                st.plotly_chart(fig, key=f"graf_{i}")

# =========================================================
# CARGOS
# =========================================================
elif menu == "CARGOS":
    st.title("⚙️ CARGOS")

    cargos = pd.read_sql("SELECT DISTINCT nombre FROM cargos", conn)
    cargo_sel = st.selectbox("CARGO", cargos["nombre"])

    kpis = pd.read_sql("SELECT indicador FROM cargos WHERE nombre=?", conn, params=(cargo_sel,))
    st.write("KPIs:", kpis["indicador"].tolist())

    nuevo = st.text_input("NUEVO KPI")

    if st.button("AGREGAR"):
        c.execute("INSERT INTO cargos VALUES (?,?)",(cargo_sel,nuevo.upper()))
        conn.commit()

    eliminar = st.selectbox("ELIMINAR KPI", kpis["indicador"])

    if st.button("ELIMINAR"):
        c.execute("DELETE FROM cargos WHERE nombre=? AND indicador=?",(cargo_sel,eliminar))
        conn.commit()
