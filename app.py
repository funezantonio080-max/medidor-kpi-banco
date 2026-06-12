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
# ESCÁNER VISTA EJECUTIVA (CON GENERADOR DE CÓDIGO QR)
# =========================================================
elif menu == "ESCÁNER":

    import os
    import io
    import qrcode  # Requieres instalarlo: pip install qrcode
    import plotly.graph_objects as go

    # Inyección de estilos CSS modificados para incluir el área del QR
    st.markdown("""
    <style>
    /* Fondo global oscuro */
    .stApp {
        background-color: #050814 !important;
    }
    
    /* Tarjetas principales */
    .card {
        background: #090e1d;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid #141b2d;
    }
    
    /* Título principal */
    .tt {
        font-size: 38px;
        font-weight: 700;
        color: white;
        letter-spacing: 0.5px;
    }
    
    /* Subtítulo */
    .sub {
        font-size: 16px; 
        color: #7b52ff;
        font-weight: 600;
        margin-top: 6px;
    }
    
    /* Subtítulos de secciones */
    .section-title {
        color: white;
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Cajas de datos de la columna izquierda */
    .box {
        background: #0b1326;
        padding: 16px;
        border-radius: 10px;
        margin-bottom: 14px;
        border: 1px solid #172033;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    
    .lbl {
        font-size: 14px;
        color: #637393;
        font-weight: 700;
        text-transform: uppercase;
    }
    
    .val {
        font-size: 22px;
        font-weight: 700;
        color: white;
    }
    
    /* Bloque de Perfil (Área y Cargo) */
    .profile-container {
        display: flex;
        gap: 30px;
        align-items: center;
        background: #0b1326;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #172033;
    }
    
    .profile-item {
        display: flex;
        align-items: center;
        gap: 15px;
        flex: 1;
    }
    
    .profile-icon {
        background: rgba(123, 82, 255, 0.15);
        color: #7b52ff;
        padding: 12px;
        border-radius: 50px;
        font-size: 26px;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 55px;
        height: 55px;
    }
    
    .lbl-profile {
        font-size: 18px;
        color: #7b52ff;
        font-weight: 700;
    }
    
    .val-profile {
        font-size: 24px;
        font-weight: 700;
        color: white;
    }
    
    /* Texto inferior de Cumplimiento Total */
    .kpi-total-box {
        text-align: center;
        margin-top: -10px;
        margin-bottom: 15px;
    }
    
    .kpi-total-val {
        font-size: 38px;
        font-weight: 800;
        color: #1aff74;
    }
    
    .kpi-total-lbl {
        font-size: 14px;
        color: white;
        font-weight: 700;
        text-transform: uppercase;
    }

    /* Caja contenedora para el QR */
    .qr-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: #0b1326;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #172033;
        margin-top: 20px;
    }
    
    /* CSS PARA LA TABLA A 24PX */
    .stDataFrame td, 
    .stDataFrame div[data-testid="stTableDataCell"] p,
    .stDataFrame data-grid-canvas,
    div[data-role="grid"] cell {
        font-size: 24px !important;
        font-weight: 700 !important;
        color: white !important;
    }

    .stDataFrame th, 
    .stDataFrame div[data-testid="stHeaderCell"] p,
    .stDataFrame div[data-testid="stHeaderCell"] span,
    .stDataFrame div[data-grid-header-cell] {
        font-size: 26px !important;
        font-weight: 900 !important;
        color: #8e6eff !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }

    .stDataFrame div[data-testid="stDataFrame"] {
        line-height: 2.2 !important;
    }

    div[data-baseweb="select"] {
        background-color: #0b1326 !important;
        border: 1px solid #172033 !important;
        border-radius: 8px !important;
    }
    
    div[data-baseweb="select"] div {
        color: white !important;
        font-size: 20px !important;
        font-weight: 600 !important;
    }
    
    .stDataFrame {
        border: 1px solid #172033 !important;
        border-radius: 8px !important;
        overflow: hidden;
    }
    </style>
    """, unsafe_allow_html=True)

    # Lectura de la base de datos
    empleados = pd.read_sql("SELECT * FROM empleados", conn)

    if empleados.empty:
        st.warning("Sin empleados")
        st.stop()

    empleados["vista"] = empleados["id"].astype(str) + " - " + empleados["nombre"]

    # --- 🛠️ LÓGICA DE ESCANEO QR (LEER PARÁMETRO DE LA URL) ---
    # Si la URL contiene un ID válido, pre-seleccionamos ese empleado automáticamente
    parametros_url = st.query_params
    indice_por_defecto = 0
    
    if "emp_id" in parametros_url:
        id_buscado = str(parametros_url["emp_id"])
        coincidencias = empleados[empleados["id"].astype(str) == id_buscado].index
        if not coincidencias.empty:
            indice_por_defecto = int(coincidencias[0])

    # --- ENCABEZADO SUPERIOR ---
    c1, c2 = st.columns([3.8, 2.2])
    
    with c1:
        st.markdown("""
        <div class='card' style='margin-bottom: 15px;'>
            <div style='display: flex; align-items: center; gap: 15px;'>
                <span style='font-size: 32px;'>📄</span>
                <div>
                    <div class='tt'>ESCÁNER EMPLEADO</div>
                    <div class='sub'>Perfil • Cargo • KPIs</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("<p style='color:#637393; font-size:16px; font-weight:700; margin-bottom:4px; margin-top:5px;'>Empleado</p>", unsafe_allow_html=True)
        # Añadido index=indice_por_defecto para responder dinámicamente al QR
        emp = st.selectbox("Empleado", empleados["vista"], index=indice_por_defecto, label_visibility="collapsed")

    id_emp = emp.split(" - ")[0]
    empleado = empleados[empleados["id"].astype(str) == id_emp].iloc[0]

    # --- DISTRIBUCIÓN PRINCIPAL ---
    izq, der = st.columns([1.3, 3])

    # ================= COLUMNA IZQUIERDA =================
    with izq:
        # Contenedor de la Foto
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>📷 FOTO</div>", unsafe_allow_html=True)

        os.makedirs("fotos", exist_ok=True)
        ruta = f"fotos/{id_emp}.png"

        foto = st.file_uploader("", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

        if foto:
            with open(ruta, "wb") as f:
                f.write(foto.read())
            st.rerun()

        if os.path.exists(ruta):
            st.image(ruta, use_container_width=True)
        else:
            st.markdown("""
            <div style='border: 2px dashed #242f4d; border-radius: 10px; padding: 30px; text-align: center; background: #070c18;'>
                <div style='font-size: 30px; color: #7b52ff; margin-bottom: 8px;'>📥</div>
                <div style='color: white; font-weight: 700; font-size: 14px;'>SUBIR FOTO</div>
                <div style='color: #4f5e7b; font-size: 11px; margin-top: 4px;'>PNG, JPG - Hasta 10MB</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)

        # Contenedor de Datos Personales
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        for x in ["nombre", "edad", "estado", "profesion"]:
            st.markdown(f"""
            <div class='box'>
                <div class='lbl'>{x}</div>
                <div class='val'>{empleado[x]}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


    # ================= COLUMNA DERECHA =================
    with der:
        # Tarjeta superior de Perfil Profesional
        st.markdown(f"""
        <div class='card'>
            <div class='section-title'>👤 PERFIL</div>
            <div class='profile-container'>
                <div class='profile-item'>
                    <div class='profile-icon'>🏢</div>
                    <div>
                        <div class='lbl-profile'>ÁREA</div>
                        <div class='val-profile'>FINANZAS</div>
                    </div>
                </div>
                <div style='width: 1px; height: 45px; background: #1c263c;'></div>
                <div class='profile-item'>
                    <div class='profile-icon'>💼</div>
                    <div>
                        <div class='lbl-profile'>CARGO</div>
                        <div class='val-profile'>{empleado['cargo'].upper()}</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Tarjeta inferior de KPIs y Gráfico de Dona
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>📈 KPI DEL PUESTO</div>", unsafe_allow_html=True)

        datos_kpi = pd.read_sql("SELECT * FROM kpis WHERE id=?", conn, params=(id_emp,))

        if not datos_kpi.empty:
            k1, k2 = st.columns([1.8, 1.2])

            with k1:
                tabla = datos_kpi[["indicador", "meta", "proyectado", "real"]]
                st.dataframe(tabla, use_container_width=True, hide_index=True)

            with k2:
                meta = max(datos_kpi["meta"].sum(), 1)
                real = datos_kpi["real"].sum()
                pct = round((real / meta) * 100, 2)

                fig = go.Figure()
                fig.add_trace(go.Pie(
                    values=[100, 0], 
                    hole=0.72,
                    marker=dict(colors=["#1aff74", "#090e1d"]),
                    textinfo="none",
                    hoverinfo="skip"
                ))

                fig.update_layout(
                    height=240,
                    margin=dict(t=0, b=0, l=0, r=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False,
                    annotations=[dict(
                        text=f"<span style='font-size:34px; font-weight:800; color:#1aff74;'>{pct}%</span><br><span style='font-size:13px; font-weight:700; color:white; letter-spacing:0.5px;'>CUMPLIMIENTO</span>",
                        showarrow=False,
                        align="center"
                    )]
                )

                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                
                st.markdown(f"""
                <div class='kpi-total-box'>
                    <div class='kpi-total-val'>{pct}%</div>
                    <div class='kpi-total-lbl'>Cumplimiento Total</div>
                </div>
                """, unsafe_allow_html=True)
                
                # --- 📱 GENERACIÓN E INYECCIÓN DEL CÓDIGO QR ---
                # Reemplaza 'http://localhost:8501' con el link real si lo subes a la nube (ej. Streamlit Community Cloud)
                url_base = "http://localhost:8501" 
                url_compartible = f"{url_base}/?emp_id={id_emp}"
                
                # Crear la matriz del QR acoplada estéticamente (Fondo oscuro, QR blanco)
                qr = qrcode.QRCode(version=1, box_size=10, border=1)
                qr.add_data(url_compartible)
                qr.make(fit=True)
                
                img_qr = qr.make_image(fill_color="#ffffff", back_color="#0b1326")
                
                # Convertir a bytes para que Streamlit lo pueda renderizar sin guardarlo físicamente
                buf = io.BytesIO()
                img_qr.save(buf, format="PNG")
                byte_im = buf.getvalue()
                
                # Renderizado del QR en la UI
                st.markdown("""
                <div class='qr-container'>
                    <div style='color:#637393; font-size:12px; font-weight:700; text-transform:uppercase; margin-bottom:10px; letter-spacing:0.5px;'>🔗 ACCESO MÓVIL DIRECTO</div>
                """, unsafe_allow_html=True)
                
                st.image(byte_im, width=160)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
        else:
            st.info("Sin registros de KPIs vinculados a este ID.")

        st.markdown("</div>", unsafe_allow_html=True)

    # Notificación inferior
    st.markdown("""
    <div style='background: #061f14; border: 1px solid #0d4d2a; padding: 10px 20px; border-radius: 6px; color: #1aff74; font-size: 14px; display: flex; align-items: center; gap: 10px; margin-top: 10px;'>
        <span>✔️</span> Escáner actualizado con éxito
    </div>
    """, unsafe_allow_html=True)
# =========================================================
# CARGOS
# =========================================================
elif menu == "CARGOS":
    st.title("⚙️ CARGOS")

    st.subheader("➕ CREAR NUEVO CARGO")

    nuevo_cargo = st.text_input("NOMBRE DEL CARGO")

    if st.button("CREAR CARGO"):
        if nuevo_cargo.strip() != "":
            c.execute(
                "INSERT INTO cargos VALUES (?, ?)",
                (nuevo_cargo.upper(), "SIN KPI")
            )
            conn.commit()
            st.success("CARGO CREADO CORRECTAMENTE")
            st.rerun()
        else:
            st.warning("INGRESE UN NOMBRE DE CARGO")

    cargos = pd.read_sql("SELECT DISTINCT nombre FROM cargos", conn)

    cargo_sel = st.selectbox("CARGO", cargos["nombre"])
