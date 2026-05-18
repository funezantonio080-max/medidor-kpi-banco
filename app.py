import streamlit as st
import base64
import os

# =====================================================
# CONFIGURACION
# =====================================================

st.set_page_config(
    page_title="GERENCIA DE BANCO KPI",
    page_icon="🏦",
    layout="wide"
)

# =====================================================
# RUTA REAL DE TU IMAGEN
# =====================================================

IMAGEN_FONDO = "/mnt/data/645488dc-027d-415b-b368-0dc0027a30ba.png"

# =====================================================
# FUNCION BASE64
# =====================================================

def get_base64(imagen):

    with open(imagen, "rb") as f:
        data = f.read()

    return base64.b64encode(data).decode()

img = get_base64(IMAGEN_FONDO)

# =====================================================
# CSS FONDO REAL
# =====================================================

st.markdown(f"""
<style>

[data-testid="stAppViewContainer"] {{
    background-image:
    linear-gradient(
        rgba(0,0,0,0.45),
        rgba(0,0,0,0.45)
    ),
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
    background: rgba(0,0,0,0.80);
}}

.block-container {{
    padding-top: 1rem;
}}

h1,h2,h3,h4,h5,h6,p,label {{
    color: white !important;
}}

.login-box {{
    background: rgba(5,15,35,0.88);
    padding: 35px;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.10);
    backdrop-filter: blur(10px);
}}

.stButton > button {{
    width: 100%;
    border: none;
    border-radius: 12px;
    height: 50px;
    background: linear-gradient(90deg,#0066ff,#00c6ff);
    color: white;
    font-weight: bold;
    font-size: 18px;
}}

.stTextInput input {{
    border-radius: 12px;
    height: 45px;
}}

</style>
""", unsafe_allow_html=True)

# =====================================================
# LOGIN
# =====================================================

if "login" not in st.session_state:
    st.session_state.login = False

USUARIO = "ADMIN"
CLAVE = "1234"

# =====================================================
# PANTALLA LOGIN
# =====================================================

if not st.session_state.login:

    st.markdown("""
    <h1 style='text-align:center;font-size:70px;font-weight:bold;'>
    🏦 GERENCIA DE BANCO KPI
    </h1>
    """, unsafe_allow_html=True)

    st.markdown("""
    <h2 style='text-align:center;'>
    CENTRO EJECUTIVO DE INDICADORES BANCARIOS
    </h2>
    """, unsafe_allow_html=True)

    st.markdown("<br><br><br>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1,1,1])

    with c2:

        st.markdown("""
        <div class="login-box">
        <h1 style='text-align:center;'>
        INICIAR SESION
        </h1>
        </div>
        """, unsafe_allow_html=True)

        usuario = st.text_input("USUARIO")
        clave = st.text_input(
            "CONTRASEÑA",
            type="password"
        )

        if st.button("INGRESAR"):

            if usuario == USUARIO and clave == CLAVE:

                st.session_state.login = True
                st.rerun()

            else:

                st.error(
                    "USUARIO O CONTRASEÑA INCORRECTA"
                )

    st.stop()

# =====================================================
# SISTEMA PRINCIPAL
# =====================================================

st.markdown("""
<h1 style='text-align:center;font-size:65px;'>
🏦 GERENCIA DE BANCO KPI
</h1>
""", unsafe_allow_html=True)

st.markdown("""
<h2 style='text-align:center;'>
DASHBOARD EJECUTIVO BANCARIO
</h2>
""", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("COLABORADORES", "18")

with c2:
    st.metric("KPIs", "33")

with c3:
    st.metric("EN OBJETIVO", "27")

with c4:
    st.metric("EN RIESGO", "4")
