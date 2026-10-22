
import streamlit as st

from frontend.components.profile_card import format_metric


def render_comment_table(video):

    st.markdown(
        "#### 💬 Comentarios"
    )

    comments = (
            video.get("comments")
            or []
    )

    comment_count = video.get(
        "comment_count"
    )

    comments_extracted = video.get(
        "comments_extracted",
        0
    )

    st.write(
        "**Comentarios indicados "
        "por TikTok:**",
        format_metric(comment_count)
    )

    st.write(
        "**Comentarios y respuestas "
        "recuperados:**",
        comments_extracted
    )

    if comments:

        comment_rows = []

        for comment in comments:

            comment_rows.append({
                "Usuario": comment.get(
                    "username"
                ),
                "Nombre": comment.get(
                    "author_name"
                ),
                "Comentario": comment.get(
                    "text"
                ),
                "Me gusta": comment.get(
                    "like_count"
                ),
                "Fecha": comment.get(
                    "created_at_utc"
                ),
                "Responde a": comment.get(
                    "parent_comment_id"
                )
            })

        st.dataframe(
            comment_rows,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No se recuperaron textos "
            "de comentarios durante "
            "esta consulta."
        )

    if video.get(
            "more_comments_indicated"
    ):

        st.caption(
            "TikTok indicó que existen "
            "más comentarios que los "
            "recuperados en esta consulta."
        )

    if video.get(
            "comments_error"
    ):

        st.warning(
            "Error al recuperar comentarios: "
            f"{video['comments_error']}"
        )
