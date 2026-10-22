
import streamlit as st

from frontend.components.profile_card import (
    render_profile_card
)


def render_profile(result):

    profile = result["profile"]

    st.success(
        f"Perfil consultado: @{profile['username']}"
    )

    render_profile_card(profile)
