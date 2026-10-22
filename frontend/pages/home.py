
import streamlit as st


def render_home():

    st.title("📊 TikTok Profile Scraper")

    st.write(
        "Sistema de extracción y estructuración "
        "de datos de perfiles de TikTok."
    )

    st.divider()

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

    return username, search_button
