
import json

import streamlit as st

from frontend.components.video_card import (
    render_video_card
)


def render_videos(result):

    profile = result["profile"]
    videos = result["videos"]
    report = result["video_report"]

    st.subheader("🎬 Videos recientes")

    st.caption(
        f"Enlaces detectados: "
        f"{report.get('urls_discovered', 0)} | "
        f"Videos procesados: "
        f"{report.get('videos_parsed', 0)} | "
        f"Videos seleccionados: {len(videos)}"
    )

    if not videos:

        st.warning(
            "No se pudieron recuperar datos "
            "de videos. Esto no significa "
            "que el perfil no tenga publicaciones."
        )

    # DISPLAY EACH VIDEO

    for index, video in enumerate(
            videos,
            start=1
    ):

        render_video_card(
            video,
            index
        )

    # EXTRACTION WARNINGS

    if report.get("errors"):

        st.warning(
            "Algunas publicaciones "
            "no pudieron procesarse."
        )

        with st.expander(
                "Ver errores de extracción"
        ):

            for error in report["errors"]:

                st.write(error)

    st.divider()

    # EXPORT EXTRACTED DATA

    st.subheader(
        "📥 Exportar resultados"
    )

    json_content = json.dumps(
        result,
        indent=4,
        ensure_ascii=False
    )

    st.download_button(
        label="Descargar resultados en JSON",
        data=json_content.encode("utf-8"),
        file_name=(
            f"tiktok_{profile['username']}.json"
        ),
        mime="application/json",
        use_container_width=True
    )
