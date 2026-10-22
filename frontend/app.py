
import sys
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from frontend.styles.theme import load_css
from frontend.pages.home import render_home
from frontend.pages.profile import render_profile
from frontend.pages.videos import render_videos
from frontend.services.scraper_service import run_extraction
from frontend.utils.session_manager import (
    clear_extraction_result,
    get_extraction_result,
    save_extraction_result
)


st.set_page_config(
    page_title="TikTok Profile Scraper",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.navigation(
    [st.Page(lambda: None, title="Inicio")],
    position="hidden"
)

load_css()

username, search_button = render_home()

if search_button:

    clear_extraction_result()

    try:
        with st.spinner(
                "Extrayendo información del perfil..."
        ):
            extraction_result = run_extraction(username)

        save_extraction_result(extraction_result)

    except ValueError as error:
        st.error(str(error))

    except Exception as error:
        st.error(
            "No se pudo completar la extracción: "
            f"{error}"
        )

result = get_extraction_result()

if result is not None:
    render_profile(result)
    render_videos(result)

st.divider()

st.caption(
    "TikTok Profile Scraper | "
    "Proyecto académico desarrollado "
    "con Python y Streamlit"
)
