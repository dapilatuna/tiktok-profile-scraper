
from pathlib import Path

import streamlit as st

from backend.validator import validate_username


# ==========================================
# 1. CONFIGURACIÓN DE LA APLICACIÓN
# ==========================================

st.set_page_config(
    page_title="TikTok Profile Scraper",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ==========================================
# 2. CARGA DE ESTILOS CSS
# ==========================================

def load_css():
    css_path = Path(__file__).parent / "styles.css"

    with open(css_path, "r", encoding="utf-8") as file:
        st.markdown(
            f"<style>{file.read()}</style>",
            unsafe_allow_html=True
        )


load_css()


# ==========================================
# 3. ENCABEZADO PRINCIPAL
# ==========================================

st.title("📊 TikTok Profile Scraper")

st.write(
    "Sistema de extracción y estructuración "
    "de datos de perfiles de TikTok."
)

st.divider()


# ==========================================
# 4. FORMULARIO DE CONSULTA
# ==========================================

st.subheader("🔎 Consultar perfil")

st.write(
    "Ingresa el nombre de usuario de TikTok "
    "para iniciar la consulta."
)

with st.form("profile_form"):

    username = st.text_input(
        "Nombre de usuario",
        placeholder="@username"
    )

    search_button = st.form_submit_button(
        "Buscar perfil",
        use_container_width=True
    )


# ==========================================
# 5. VALIDACIÓN DEL USERNAME
# ==========================================

if search_button:

    try:
        valid_username = validate_username(username)

        st.success(
            f"Nombre de usuario válido: @{valid_username}"
        )

        st.info(
            "La validación se realizó correctamente. "
            "El módulo de extracción de datos "
            "se implementará posteriormente."
        )

    except ValueError as error:
        st.error(str(error))


# ==========================================
# 6. PIE DE PÁGINA
# ==========================================

st.divider()

st.caption(
    "TikTok Profile Scraper | "
    "Proyecto académico desarrollado con Python y Streamlit"
)
