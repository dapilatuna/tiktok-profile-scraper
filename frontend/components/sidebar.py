
import streamlit as st


def render_sidebar():

    if "active_page" not in st.session_state:
        st.session_state.active_page = "scraping"

    with st.sidebar:

        if st.button(
                "🔎  Scraping",
                key="nav_scraping",
                use_container_width=True,
                type=(
                        "primary"
                        if st.session_state.active_page == "scraping"
                        else "secondary"
                )
        ):
            st.session_state.active_page = "scraping"
            st.rerun()

        if st.button(
                "🧠  Embeddings",
                key="nav_embeddings",
                use_container_width=True,
                type=(
                        "primary"
                        if st.session_state.active_page == "embeddings"
                        else "secondary"
                )
        ):
            st.session_state.active_page = "embeddings"
            st.rerun()

    return st.session_state.active_page
