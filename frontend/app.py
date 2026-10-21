
import sys
import json

from pathlib import Path
from datetime import datetime, timezone

import streamlit as st


# ==========================================
# 1. PROJECT CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.validator import validate_username
from backend.profile_extractor import extract_profile
from backend.video_extractor import extract_videos


st.set_page_config(
    page_title="TikTok Profile Scraper",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ==========================================
# 2. LOAD CSS
# ==========================================

def load_css():

    css_path = Path(__file__).parent / "styles.css"

    if css_path.exists():

        with open(
                css_path,
                "r",
                encoding="utf-8"
        ) as file:

            st.markdown(
                f"<style>{file.read()}</style>",
                unsafe_allow_html=True
            )


load_css()


# ==========================================
# 3. FORMAT VIDEO DATE
# ==========================================

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


# ==========================================
# 4. FORMAT METRIC VALUES
# ==========================================

def format_metric(value):

    if value is None:
        return "N/D"

    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return str(value)


# ==========================================
# 5. APPLICATION HEADER
# ==========================================

st.title("📊 TikTok Profile Scraper")

st.write(
    "Sistema de extracción y estructuración "
    "de datos de perfiles de TikTok."
)

st.divider()


# ==========================================
# 6. SEARCH FORM
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
# 7. PROFILE AND VIDEO EXTRACTION
# ==========================================

if search_button:

    st.session_state.pop(
        "extraction_result",
        None
    )

    try:
        valid_username = validate_username(
            username
        )

        # --------------------------------------
        # 7.1 OPEN CHROME AND EXTRACT PROFILE
        # --------------------------------------

        with st.spinner(
                "Extrayendo información del perfil..."
        ):

            with extract_profile(valid_username) as (page, profile):

                # ----------------------------------
                # 7.2 EXTRACT VIDEOS AND COMMENTS
                # ----------------------------------

                try:
                    with st.spinner(
                            "Extrayendo videos y comentarios..."
                    ):

                        video_report = extract_videos(
                            page,
                            valid_username,
                            limit=10
                        )

                except Exception as error:
                    video_report = {
                        "videos": [],
                        "urls_discovered": 0,
                        "videos_parsed": 0,
                        "errors": [str(error)]
                    }

        # --------------------------------------
        # 7.3 STRUCTURE AND SAVE RESULTS
        # --------------------------------------

        extraction_result = {
            "extracted_at_utc": datetime.now(
                timezone.utc
            ).isoformat(),
            "profile": profile,
            "video_report": video_report,
            "videos": video_report.get(
                "videos",
                []
            )
        }

        st.session_state[
            "extraction_result"
        ] = extraction_result

    except ValueError as error:
        st.error(str(error))

    except Exception as error:
        st.error(
            "No se pudo completar la extracción: "
            f"{error}"
        )

# ==========================================
# 8. DISPLAY EXTRACTION RESULTS
# ==========================================

result = st.session_state.get(
    "extraction_result"
)

if result is not None:

    profile = result["profile"]

    videos = result["videos"]

    report = result["video_report"]

    st.success(
        f"Perfil consultado: @{profile['username']}"
    )

    # ======================================
    # 8.1 PROFILE INFORMATION
    # ======================================

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

    # ======================================
    # 8.2 VIDEO INFORMATION
    # ======================================

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

    # --------------------------------------
    # DISPLAY EACH VIDEO
    # --------------------------------------

    for index, video in enumerate(
            videos,
            start=1
    ):

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

            # ----------------------------------
            # VIDEO URL
            # ----------------------------------

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

            # ----------------------------------
            # PUBLICATION INFORMATION
            # ----------------------------------

            st.write(
                f"**Publicado:** {video_date}"
            )

            st.write(
                f"**Descripción:** {description}"
            )

            st.divider()

            # ----------------------------------
            # VIDEO STATISTICS
            # ----------------------------------

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

            # ----------------------------------
            # VIDEO DURATION
            # ----------------------------------

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

            # ----------------------------------
            # MUSIC INFORMATION
            # ----------------------------------

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

            # ----------------------------------
            # HASHTAGS
            # ----------------------------------

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

            # ==================================
            # 8.3 VIDEO COMMENTS
            # ==================================

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

            # ----------------------------------
            # STRUCTURED VIDEO DATA
            # ----------------------------------

            if st.checkbox(
                    "Ver datos estructurados completos",
                    key=f"video_json_{index}"
            ):

                st.json(video)

    # ======================================
    # 8.4 EXTRACTION WARNINGS
    # ======================================

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

    # ======================================
    # 8.5 EXPORT EXTRACTED DATA
    # ======================================

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


# ==========================================
# 9. FOOTER
# ==========================================

st.divider()

st.caption(
    "TikTok Profile Scraper | "
    "Proyecto académico desarrollado "
    "con Python y Streamlit"
)
