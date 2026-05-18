import streamlit as st
import base64

# =====================================================
# CONFIGURACION
# =====================================================

st.set_page_config(
    page_title="GERENCIA DE BANCO KPI",
    page_icon="🏦",
    layout="wide"
)

# =====================================================
# CARGAR IMAGEN DE FONDO
# =====================================================

with open("24f7ec0f-f914-4e59-90d5-f0ad5533f500.png", "rb") as image_file:
    encoded = base64.b64encode(
        image_file.read()
    ).decode()

# =====================================================
# ESTILOS
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

.block-container {{
    padding-top: 1rem;
}}

h1,h2,h3,label {{
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

</style>
""", unsafe_allow_html=True)

# =====================================================
# LOGIN
# =====================================================

st.markdown("""
<h1 style='text-align:center;font-size:72px;font-weight:bold;'>
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

    st.button("INGRESAR")
