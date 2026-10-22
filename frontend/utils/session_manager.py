
import streamlit as st


def clear_extraction_result():
    st.session_state.pop(
        "extraction_result",
        None
    )


def save_extraction_result(result):
    st.session_state[
        "extraction_result"
    ] = result


def get_extraction_result():
    return st.session_state.get(
        "extraction_result"
    )
