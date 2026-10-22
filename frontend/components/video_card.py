
from datetime import datetime, timezone

import streamlit as st

from frontend.components.profile_card import format_metric
from frontend.pages.comments import render_comments


def format_video_date(video: dict) -> str:

    timestamp = video.get("create_time")

    if timestamp:

        try:
            return datetime.fromtimestamp(
                int(timestamp),
                tz=timezone.utc
            ).strftime("%d/%m/%Y %H:%M UTC")

        except (ValueError, TypeError, OverflowError):
            pass

    return (
            video.get("created_at_utc")
            or "Fecha no disponible"
    )


def render_video_card(video, index):

    description = (
            video.get("description")
            or "Sin descripción"
    )

    video_date = format_video_date(
        video
    )

    with st.expander(
            f"🎬 Video {index}"
    ):

        # VIDEO URL

        video_url = video.get("url")

        if video_url:

            st.link_button(
                f"🔗 Ver video {index} en TikTok",
                video_url,
                use_container_width=True
            )

        else:

            st.warning(
                "Enlace no disponible."
            )

        # PUBLICATION INFORMATION

        st.write(
            f"**Publicado:** {video_date}"
        )

        st.write(
            f"**Descripción:** {description}"
        )

        st.divider()

        # VIDEO STATISTICS

        st.markdown(
            "#### 📊 Estadísticas"
        )

        metric_columns = st.columns(5)

        metric_items = [
            ("Vistas", "views"),
            ("Me gusta", "likes"),
            ("Comentarios", "comment_count"),
            ("Compartidos", "shares"),
            ("Guardados", "save_count")
        ]

        for column, (label, key) in zip(
                metric_columns,
                metric_items
        ):

            value = video.get(key)

            column.metric(
                label,
                format_metric(value)
            )

        st.divider()

        # VIDEO DURATION

        duration = video.get("duration")

        if duration is not None:

            duration_text = (
                f"{duration} segundos"
            )

        else:

            duration_text = (
                "No disponible"
            )

        st.write(
            "**Duración:**",
            duration_text
        )

        # MUSIC INFORMATION

        music_title = (
                video.get("music_title")
                or "No disponible"
        )

        music_author = (
                video.get("music_author")
                or "No disponible"
        )

        st.write(
            "**Música:**",
            music_title
        )

        st.write(
            "**Artista:**",
            music_author
        )

        # HASHTAGS

        hashtags = (
                video.get("hashtags")
                or []
        )

        if hashtags:

            hashtags_text = ", ".join(
                f"#{tag}"
                for tag in hashtags
            )

        else:

            hashtags_text = (
                "No disponibles"
            )

        st.write(
            "**Hashtags:**",
            hashtags_text
        )

        st.divider()

        # VIDEO COMMENTS

        render_comments(video)

        # STRUCTURED VIDEO DATA

        if st.checkbox(
                "Ver datos estructurados completos",
                key=f"video_json_{index}"
        ):

            st.json(video)
