import streamlit as st
import base64

# =====================================================
# CONFIGURACION GENERAL
# =====================================================

st.set_page_config(
    page_title="GERENCIA DE BANCO KPI",
    page_icon="🏦",
    layout="wide"
)

# =====================================================
# CARGAR IMAGEN DE FONDO
# =====================================================

# ESTA ES LA IMAGEN NUEVA QUE SUBISTE
with open("cf28a163-8639-4681-8332-327545f58634.png", "rb") as image_file:

    encoded = base64.b64encode(
        image_file.read()
    ).decode()

# =====================================================
# ESTILOS CSS
# =====================================================

st.markdown(f"""
<style>

[data-testid="stAppViewContainer"] {{

    background-image:
    linear-gradient(
        rgba(0,0,0,0.45),
        rgba(0,0,0,0.45)
    ),
    url("data:image/png;base64,{encoded}");

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

h1,h2,h3,label,p {{
    color: white !important;
}}

.login-box {{

    background: rgba(0,0,0,0.60);

    padding: 40px;

    border-radius: 20px;

    border: 1px solid rgba(255,255,255,0.10);

    backdrop-filter: blur(8px);
}}

.stTextInput input {{

    height: 50px;

    border-radius: 12px;
}}

.stButton > button {{

    width: 100%;

    height: 52px;

    border-radius: 12px;

    border: none;

    background:
    linear-gradient(
        90deg,
        #0066ff,
        #00c6ff
    );

    color: white;

    font-size: 18px;

    font-weight: bold;
}}

.metric-card {{

    background: rgba(0,0,0,0.55);

    padding: 25px;

    border-radius: 18px;

    text-align: center;

    border: 1px solid rgba(255,255,255,0.10);
}}

.metric-title {{

    color: #ffffff;

    font-size: 22px;

    font-weight: bold;
}}

.metric-value {{

    color: #00c6ff;

    font-size: 40px;

    font-weight: bold;
}}

</style>
""", unsafe_allow_html=True)

# =====================================================
# VARIABLES LOGIN
# =====================================================

if "login" not in st.session_state:
    st.session_state.login = False

USUARIO = "ADMIN"
CLAVE = "1234"

# =====================================================
# LOGIN
# =====================================================

if not st.session_state.login:

    st.markdown("""
    <h1 style='text-align:center;
               font-size:72px;
               font-weight:bold;'>
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
# DASHBOARD PRINCIPAL
# =====================================================

st.markdown("""
<h1 style='text-align:center;
           font-size:65px;
           font-weight:bold;'>
🏦 GERENCIA DE BANCO KPI
</h1>
""", unsafe_allow_html=True)

st.markdown("""
<h2 style='text-align:center;'>
DASHBOARD EJECUTIVO BANCARIO
</h2>
""", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# =====================================================
# KPIs
# =====================================================

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.markdown("""
    <div class="metric-card">

    <div class="metric-title">
    COLABORADORES
    </div>

    <div class="metric-value">
    18
    </div>

    </div>
    """, unsafe_allow_html=True)

with c2:

    st.markdown("""
    <div class="metric-card">

    <div class="metric-title">
    KPIs
    </div>

    <div class="metric-value">
    33
    </div>

    </div>
    """, unsafe_allow_html=True)

with c3:

    st.markdown("""
    <div class="metric-card">

    <div class="metric-title">
    EN OBJETIVO
    </div>

    <div class="metric-value">
    27
    </div>

    </div>
    """, unsafe_allow_html=True)

with c4:

    st.markdown("""
    <div class="metric-card">

    <div class="metric-title">
    EN RIESGO
    </div>

    <div class="metric-value">
    4
    </div>

    </div>
    """, unsafe_allow_html=True)
