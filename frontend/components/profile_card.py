
import streamlit as st


def format_metric(value):

    if value is None:
        return "N/D"

    try:
        return f"{int(value):,}"

    except (ValueError, TypeError):
        return str(value)


def render_profile_card(profile):

    st.subheader(
        "👤 Información del perfil"
    )

    st.write(
        "**Nombre:** "
        f"{profile.get('name') or 'No disponible'}"
    )

    st.write(
        "**Biografía:** "
        f"{profile.get('biography') or 'Sin biografía'}"
    )

    profile_columns = st.columns(4)

    profile_columns[0].metric(
        "Seguidores",
        format_metric(
            profile.get("followers")
        )
    )

    profile_columns[1].metric(
        "Seguidos",
        format_metric(
            profile.get("following")
        )
    )

    profile_columns[2].metric(
        "Me gusta",
        format_metric(
            profile.get("likes")
        )
    )

    profile_columns[3].metric(
        "Publicaciones",
        format_metric(
            profile.get("video_count")
        )
    )

    st.divider()
