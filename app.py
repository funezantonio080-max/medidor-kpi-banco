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

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

import streamlit as st
import pandas as pd
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# =========================================================
# DASHBOARD EJECUTIVO PERFECCIONADO (VERSION CLON REAL V14)
# =========================================================

if menu == "DASHBOARD":

    # 1. ESTILOS GENERALES CSS (Contenedores oscuros y textos limpios)
    st.markdown("""
    <style>
    /* Fondo oscuro de la app */
    [data-testid="stAppViewContainer"] {
        background-color: #060b13 !important;
    }
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        max-width: 96% !important;
    }
    
    /* Forzar diseño de tarjetas oscuras usando los contenedores de Streamlit */
    div[data-testid="stVerticalBlock"] > div:has(div.kpi-contenedor-tarjeta) {
        background: #09101a !important;
        border: 1px solid #142334 !important;
        border-radius: 14px !important;
        padding: 22px !important;
        margin-bottom: 12px !important;
    }

    /* ENCABEZADO */
    .hdr-clon-box {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        margin-bottom: 15px;
    }
    .hdr-logo-box {
        background: #09101a;
        border: 1px solid #00E676;
        box-shadow: 0px 0px 12px rgba(0, 230, 118, 0.3);
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 24px;
    }
    .hdr-title-center { text-align: center; flex-grow: 1; }
    .hdr-title-main { font-size: 30px; font-weight: 800; color: white; margin: 0; letter-spacing: 0.5px; }
    .hdr-title-sub { color: #00E676; font-size: 13px; font-weight: 700; letter-spacing: 1.5px; margin-top: 2px; }
    .hdr-date-badge { background-color: #0b131c; border: 1px solid #142334; border-radius: 8px; padding: 8px 16px; text-align: right; }

    /* TARJETAS SUPERIORES DE MÉTRICAS */
    .top-metric-frame {
        background: #0b131c;
        border-radius: 10px;
        padding: 12px;
        border: 1px solid #142334;
        display: flex;
        align-items: center;
        gap: 12px;
        height: 68px;
    }
    .top-icon-circle {
        font-size: 18px;
        background: rgba(0, 230, 118, 0.06);
        padding: 8px;
        border-radius: 6px;
        border: 1px solid rgba(0, 230, 118, 0.2);
        display: flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
    }
    .top-lbl { color: #7a8b9e; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    .top-val { color: white; font-size: 20px; font-weight: 700; line-height: 1.1; }
    .top-dsc { color: #4f6174; font-size: 10px; }

    /* DETALLES DE LAS TARJETAS GRANDES */
    .kpi-card-header-row { display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 12px; }
    .kpi-card-header-left { display: flex; align-items: center; }
    .badge-sym-frame { background: rgba(0, 230, 118, 0.12); color: #00E676; padding: 3px 9px; border-radius: 6px; font-weight: 800; font-size: 14px; margin-right: 12px; border: 1px solid rgba(0, 230, 118, 0.25); }
    .kpi-title-text { color: white; font-size: 16px; font-weight: 700; }

    /* FILAS DE LEYENDA (DERECHA) */
    .row-data-align { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-size: 13px; width: 100%; }
    .bullet-circle { height: 8px; width: 8px; border-radius: 50%; display: inline-block; margin-right: 8px; }
    .b-meta { background-color: #2196F3; }
    .b-proy { background-color: #FFC107; }
    .b-real { background-color: #00E676; }
    .lbl-style { color: #7a8b9e; font-weight: 600; text-transform: uppercase; }
    .val-style { color: white; font-weight: 700; font-family: monospace; font-size: 13.5px; }

    /* CAJA DE CUMPLIMIENTO GRIS OSCURO */
    .box-comp-clon { background: #0e1926; border: 1px solid #1a2d42; border-radius: 10px; padding: 12px; text-align: center; margin-top: 15px; width: 100%; }
    .box-comp-lbl { color: #7a8b9e; font-size: 11px; font-weight: 500; }
    .box-comp-val { color: #00E676; font-size: 22px; font-weight: 700; margin: 2px 0; }
    .box-comp-status { color: #00E676; font-size: 11px; font-weight: 600; }

    /* NOTAS Y PIE DE PÁGINA */
    .card-footer-note { text-align: center; color: #00E676; font-size: 11px; opacity: 0.6; margin-top: 15px; font-weight: 500; width: 100%; }
    .footer-bar-clon { display: flex; justify-content: space-between; padding-top: 12px; border-top: 1px solid #142334; color: #4f6174; font-size: 11px; margin-top: 30px; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

    # Lectura de datos SQL relacionales
    empleados = pd.read_sql("SELECT * FROM empleados", conn)
    kpis = pd.read_sql("SELECT * FROM kpis", conn)

    total_emp = len(empleados)
    total_kp = len(kpis)
    prom_cump = round((kpis["real"].sum() / (kpis["meta"].sum() + 1)) * 100, 2) if not kpis.empty else 0
    kpis_riesgo = len(kpis[kpis["real"] < kpis["meta"]]) if not kpis.empty else 0
    kpis_ok = max(total_kp - kpis_riesgo, 0)
    fecha_badge = datetime.now().strftime("%d/%m/%Y")

    # 1. RENDERIZADO DEL ENCABEZADO SUPERIOR
    st.markdown(f"""
    <div class='hdr-clon-box'>
        <div class='hdr-logo-box'>🏦</div>
        <div class='hdr-title-center'>
            <h1 class='hdr-title-main'>DASHBOARD EJECUTIVO</h1>
            <div class='hdr-title-sub'>GERENCIA DE BANCO KPI</div>
        </div>
        <div class='hdr-date-badge'>
            <span style='color:#7a8b9e; font-size:9px; display:block; font-weight:600;'>FECHA ACTUAL</span>
            <span style='color:white; font-size:12px; font-weight:700;'>📅 {fecha_badge}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. CINTA DE LAS 5 TARJETAS INFORMATIVAS SUPERIORES
    t1, t2, t3, t4, t5 = st.columns(5)
    with t1:
        st.markdown(f"<div class='top-metric-frame'><div class='top-icon-circle' style='color:#00E676;'>👥</div><div><div class='top-lbl'>Colaboradores</div><div class='top-val'>{total_emp}</div><div class='top-dsc'>Total Personal</div></div></div>", unsafe_allow_html=True)
    with t2:
        st.markdown(f"<div class='top-metric-frame'><div class='top-icon-circle' style='color:#2196F3;'>📈</div><div><div class='top-lbl'>KPIs Activos</div><div class='top-val'>{total_kp}</div><div class='top-dsc'>Indicadores</div></div></div>", unsafe_allow_html=True)
    with t3:
        st.markdown(f"<div class='top-metric-frame'><div class='top-icon-circle' style='color:#00E676;'>🎯</div><div><div class='top-lbl'>Cumplimiento</div><div class='top-val'>{prom_cump}%</div><div class='top-dsc'>Promedio General</div></div></div>", unsafe_allow_html=True)
    with t4:
        st.markdown(f"<div class='top-metric-frame'><div class='top-icon-circle' style='color:#00E676;'>✅</div><div><div class='top-lbl'>En Objetivo</div><div class='top-val'>{kpis_ok}</div><div class='top-dsc'>Sin Riesgo</div></div></div>", unsafe_allow_html=True)
    with t5:
        c_alert = "#FFC107" if kpis_riesgo > 0 else "#7a8b9e"
        st.markdown(f"<div class='top-metric-frame'><div class='top-icon-circle' style='color:{c_alert};'>⚠️</div><div><div class='top-lbl'>En Riesgo</div><div class='top-val' style='color:{c_alert};'>{kpis_riesgo}</div><div class='top-dsc'>Atención</div></div></div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

    # 3. GENERACIÓN EN REJILLA DE LAS TARJETAS DE INDICADORES (Mapeo de 2 en 2)
    for index in range(0, len(kpis), 2):
        par_kpis = kpis.iloc[index:index+2]
        bloque_columnas = st.columns(2)

        for col_pos, (_, row) in enumerate(par_kpis.iterrows()):
            m_val = max(row["meta"], 1)
            r_val = row["real"]
            p_val = row["proyectado"]
            pct_cump = round((r_val / m_val) * 100, 2)

            # Estructuración de labels de monedas y medidas exactas
            badge_txt = "$"
            ind_title = f"{row['indicador']}"
            txt_footer = "Valores expresados en CÓRDOBAS (C$)"

            if row["indicador"] == "RENTABILIDAD":
                ind_title = "RENTABILIDAD (Utilidad Generada)"
            elif row["indicador"] == "ROA":
                badge_txt = "%"
                ind_title = "ROA (Rendimiento sobre Activos)"
                txt_footer = "Valores expresados en PORCENTAJE (%)"
            elif row["indicador"] == "ROE":
                badge_txt = "%"
                ind_title = "ROE (Rendimiento sobre Patrimonio)"
                txt_footer = "Valores expresados en PORCENTAJE (%)"
            elif row["indicador"] == "LIQUIDEZ":
                ind_title = "LIQUIDEZ (Disponibilidad de Efectivo)"

            with bloque_columnas[col_pos]:
                with st.container():
                    # Clave de anclaje CSS para dibujar los contenedores grises
                    st.markdown(f"<div class='kpi-contenedor-tarjeta'></div>", unsafe_allow_html=True)
                    
                    # Fila superior (Título del KPI + Menú decorativo de tres puntos)
                    st.markdown(f"""
                    <div class='kpi-card-header-row'>
                        <div class='kpi-card-header-left'>
                            <span class='badge-sym-frame'>{badge_txt}</span>
                            <span class='kpi-title-text'>{ind_title}</span>
                        </div>
                        <div style='color:#4f6174; font-weight:bold; font-size:14px;'>•••</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Sub-layout interno ordenado nativamente
                    c_grafico, c_datos = st.columns([1.1, 1.2])

                    with c_grafico:
                        # CONFIGURACIÓN DONA ANCHA: hole=0.52 y colores vivos idénticos a la foto
                        val_graf_cump = r_val if r_val <= m_val else m_val
                        val_graf_rest = max(m_val - r_val, 0)
                        
                        fig_donut = go.Figure()
                        fig_donut.add_trace(go.Pie(
                            values=[val_graf_cump, val_graf_rest],
                            hole=0.52,  # Ajustado de 0.74 a 0.52 para engrosar el cuerpo significativamente
                            textinfo="none",
                            hoverinfo="none",
                            marker=dict(colors=["#00E676", "#142c1b"]), # Tonos verde claro y verde oscuro originales
                            direction="clockwise",
                            sort=False
                        ))

                        fig_donut.update_layout(
                            height=180,
                            margin=dict(t=0, b=0, l=0, r=0),
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            showlegend=False,
                            annotations=[dict(
                                text=f"<b style='font-size:22px;color:white;'>{pct_cump}%</b><br><span style='font-size:10px;color:#7a8b9e;font-weight:600;'>Cumplimiento</span>",
                                showarrow=False,
                                font=dict(color="white")
                            )]
                        )
                        st.plotly_chart(fig_donut, use_container_width=True, key=f"clon_v14_{row['indicador']}", config={'displayModeBar': False})

                    with c_datos:
                        # Formateadores numéricos de precisión string
                        f_str = ",.2f"
                        s_str = "%" if badge_txt == "%" else ""
                        p_str = "C$ " if badge_txt == "$" else ""

                        # SOLUCIÓN CRÍTICA ANTI-ROTURAS: Concatenación controlada en una variable lineal sin saltos
                        bloque_datos_html = (
                            f"<div style='padding-top:5px; width:100%;'>"
                            f"  <div class='row-data-align'>"
                            f"      <div><span class='bullet-circle b-meta'></span><span class='lbl-style'>META</span></div>"
                            f"      <div class='val-style'>{p_str}{m_val:{f_str}}{s_str}</div>"
                            f"  </div>"
                            f"  <div class='row-data-align'>"
                            f"      <div><span class='bullet-circle b-proy'></span><span class='lbl-style'>PROYECTADO</span></div>"
                            f"      <div class='val-style'>{p_str}{p_val:{f_str}}{s_str}</div>"
                            f"  </div>"
                            f"  <div class='row-data-align'>"
                            f"      <div><span class='bullet-circle b-real'></span><span class='lbl-style'>REAL</span></div>"
                            f"      <div class='val-style'>{p_str}{r_val:{f_str}}{s_str}</div>"
                            f"  </div>"
                            f"  <div class='box-comp-clon'>"
                            f"      <div class='box-comp-lbl'>Cumplimiento</div>"
                            f"      <div class='box-comp-val'>{pct_cump}%</div>"
                            f"      <div class='box-comp-status'>▲ Por encima de la meta</div>"
                            f"  </div>"
                            f"</div>"
                        )
                        
                        # Renderizado único absoluto de la columna de métricas + cajita de cumplimiento
                        st.markdown(bloque_datos_html, unsafe_allow_html=True)

                    # Nota aclaratoria base del KPI
                    st.markdown(f"<div class='card-footer-note'>{txt_footer}</div>", unsafe_allow_html=True)

    # 4. PIE DE PÁGINA GLOBAL DEL PANEL REPLICA V14
    st.markdown("""
    <div class='footer-bar-clon'>
        <div>⚙️ Sistema de Gestión KPI - Banco &nbsp;|&nbsp; Información actualizada en tiempo real</div>
        <div style='color:#00E676;'>Datos confiables para decisiones inteligentes 📈</div>
    </div>
    """, unsafe_allow_html=True)
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


    import streamlit as st
    import pandas as pd
    import os

    st.title("📄 ESCÁNER DE EMPLEADO")

    try:

        empleados = pd.read_sql(
            "SELECT * FROM empleados",
            conn
        )

    except Exception as e:

        st.error(
            f"Error empleados: {e}"
        )

        st.stop()

    if empleados.empty:

        st.warning(
            "No existen empleados"
        )

        st.stop()

    columna_id = empleados.columns[0]

    empleados["vista"] = (

        empleados[columna_id]
        .astype(str)

        +

        " - "

        +

        empleados.iloc[:,1]
        .astype(str)

    )

    seleccionado = st.selectbox(

        "👤 Seleccionar empleado",

        empleados["vista"]

    )

    id_emp = seleccionado.split(
        " - "
    )[0]

    empleado = empleados[

        empleados[
            columna_id
        ]
        .astype(str)

        ==

        str(
            id_emp
        )

    ].iloc[0]

    st.markdown("---")

    foto, datos = st.columns([1,2])

    with foto:

        st.subheader(
            "📷 FOTO"
        )

        os.makedirs(
            "fotos",
            exist_ok=True
        )

        ruta = (
            "fotos/"
            +
            str(id_emp)
            +
            ".png"
        )

        archivo = st.file_uploader(

            "Subir foto",

            type=[

                "png",
                "jpg",
                "jpeg"

            ]

        )

        if archivo:

            with open(
                ruta,
                "wb"
            ) as f:

                f.write(
                    archivo.read()
                )

            st.success(
                "Foto guardada"
            )

        if os.path.exists(
            ruta
        ):

            st.image(

                ruta,

                use_container_width=True

            )

    with datos:

        st.subheader(
            "👤 PERFIL"
        )

        for col in empleados.columns:

            if col != "vista":

                valor = empleado[col]

                st.write(

                    f"**{col.upper()}**"

                )

                st.write(
                    valor
                )

    st.markdown("---")

    st.subheader(
        "💼 INFORMACIÓN DEL CARGO"
    )

    try:

        cargos = pd.read_sql(
            "SELECT * FROM cargos",
            conn
        )

        if "cargo" in empleados.columns:

            cargo = str(
                empleado[
                    "cargo"
                ]
            )

            cargo_data = cargos[

                cargos.astype(
                    str
                )

                .apply(

                    lambda x:

                    x.str.contains(

                        cargo,

                        case=False,

                        na=False

                    )

                )

                .any(
                    axis=1
                )

            ]

            if not cargo_data.empty:

                st.dataframe(

                    cargo_data,

                    use_container_width=True

                )

            else:

                st.info(
                    "Sin información del cargo"
                )

    except Exception as e:

        st.warning(
            f"Cargo: {e}"
        )

    st.markdown("---")

    st.subheader(
        "📈 KPI"
    )

    try:

        kpis = pd.read_sql(

            "SELECT * FROM kpis",

            conn

        )

        if "id" in kpis.columns:

            datos_kpi = kpis[

                kpis[
                    "id"
                ]
                .astype(str)

                ==

                str(
                    id_emp
                )

            ]

        else:

            datos_kpi = kpis

        if not datos_kpi.empty:

            st.dataframe(

                datos_kpi,

                use_container_width=True

            )

            if (

                "meta"
                in datos_kpi.columns

                and

                "real"
                in datos_kpi.columns

            ):

                cumplimiento = round(

                    (

                        datos_kpi[
                            "real"
                        ]
                        .sum()

                        /

                        max(

                            datos_kpi[
                                "meta"
                            ]
                            .sum(),

                            1

                        )

                    )

                    *100,

                    2

                )

                st.metric(

                    "Cumplimiento",

                    f"{cumplimiento}%"

                )

        else:

            st.info(
                "Sin KPI"
            )

    except Exception as e:

        st.warning(
            f"KPI: {e}"
        )

    st.success(
        "Información cargada correctamente"
    )
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
