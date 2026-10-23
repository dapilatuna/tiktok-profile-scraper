
import hashlib
import json

import altair as alt
import pandas as pd
import streamlit as st

from frontend.services.big_five_service import (
    TRAITS,
    analyze_big_five,
    prepare_profile_data,
)

from frontend.utils.session_manager import (
    get_extraction_result,
)

from backend.career_guidance_service import (
    generate_career_guidance,
)

from frontend.pages.career_guidance import (
    render_career_guidance,
)

# ==========================================
# 1. BIG FIVE CHART
# ==========================================

def render_big_five_chart(dimensions):
    st.subheader("Gráfico comparativo Big Five")

    chart_data = []

    for key, label in TRAITS.items():
        item = dimensions.get(key, {})
        score = item.get("score")

        chart_data.append({
            "Dimensión": label,
            "Índice": (
                float(score)
                if score is not None
                else None
            ),
            "Estado": (
                "Evaluado"
                if score is not None
                else "Sin datos"
            ),
        })

    df = pd.DataFrame(chart_data)

    dimension_order = list(TRAITS.values())

    base = alt.Chart(df).encode(
        y=alt.Y(
            "Dimensión:N",
            sort=dimension_order,
            title=None,
            axis=alt.Axis(
                labelLimit=230,
                labelFontSize=12,
            ),
        ),
    )

    background = base.mark_bar(
        color="#E9E2F1",
        cornerRadiusEnd=6,
        size=25,
    ).encode(
        x=alt.value(0),
        x2=alt.datum(100),
    )

    bars = (
        alt.Chart(df[df["Índice"].notna()])
        .mark_bar(
            color="#8B5CF6",
            cornerRadiusEnd=6,
            size=25,
        )
        .encode(
            y=alt.Y(
                "Dimensión:N",
                sort=dimension_order,
                title=None,
            ),
            x=alt.X(
                "Índice:Q",
                scale=alt.Scale(
                    domain=[0, 100],
                ),
                axis=alt.Axis(
                    title="Índice exploratorio (0–100)",
                    values=[0, 20, 40, 60, 80, 100],
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "Dimensión:N",
                    title="Dimensión",
                ),
                alt.Tooltip(
                    "Índice:Q",
                    title="Índice",
                    format=".0f",
                ),
            ],
        )
    )

    labels = (
        alt.Chart(df[df["Índice"].notna()])
        .mark_text(
            align="left",
            baseline="middle",
            dx=8,
            fontSize=12,
            color="#604D73",
        )
        .encode(
            y=alt.Y(
                "Dimensión:N",
                sort=dimension_order,
            ),
            x=alt.X(
                "Índice:Q",
                scale=alt.Scale(
                    domain=[0, 100],
                ),
            ),
            text=alt.Text(
                "Índice:Q",
                format=".0f",
            ),
        )
    )

    missing = (
        alt.Chart(df[df["Índice"].isna()])
        .mark_text(
            align="left",
            baseline="middle",
            dx=8,
            fontSize=12,
            color="#806D8D",
        )
        .encode(
            y=alt.Y(
                "Dimensión:N",
                sort=dimension_order,
            ),
            x=alt.datum(0),
            text=alt.value("Sin datos"),
        )
    )

    chart = (
            background + bars + labels + missing
    ).properties(
        height=300,
    ).configure_view(
        strokeWidth=0,
    )

    st.altair_chart(
        chart,
        use_container_width=True,
    )

    st.caption(
        "Se muestran las cinco dimensiones del Big Five. "
        "Los índices representan señales textuales "
        "exploratorias. 'Sin datos' indica que no se "
        "asignó una puntuación; no equivale a cero."
    )


# ==========================================
# 2. BIG FIVE ANALYSIS
# ==========================================

def render_big_five():
    st.subheader("Análisis Big Five")

    st.caption(
        "Análisis exploratorio del contenido público "
        "mediante inteligencia artificial."
    )

    st.markdown("### 1. Seleccionar información")

    source = st.radio(
        "¿De dónde deseas obtener los datos?",
        [
            "Usar datos del scraping actual",
            "Subir archivo JSON",
        ],
        horizontal=True,
        key="big_five_source",
    )

    data = None

    if source == "Usar datos del scraping actual":
        data = get_extraction_result()

        if data is None:
            st.info(
                "Primero realiza una extracción "
                "desde la sección Scraping."
            )

    else:
        uploaded_file = st.file_uploader(
            "Selecciona un archivo JSON",
            type=["json"],
            key="big_five_file",
        )

        if uploaded_file is not None:
            try:
                data = json.loads(
                    uploaded_file.getvalue().decode("utf-8")
                )

            except (ValueError, UnicodeDecodeError):
                st.error(
                    "No se pudo leer el archivo JSON."
                )
                return

    if data is None:
        return

    try:
        prepared = prepare_profile_data(data)

    except ValueError as error:
        st.error(str(error))
        return

    st.markdown("### 2. Información disponible")

    st.write(
        f"**Perfil:** "
        f"@{prepared['username'] or 'No identificado'}"
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Videos extraídos",
        prepared["videos_found"],
    )

    col2.metric(
        "Videos con contenido",
        prepared["videos_with_content"],
    )

    col3.metric(
        "Respuestas del autor",
        prepared["author_replies"],
    )

    with st.expander("Ver variables del análisis"):
        st.write(
            "**Descripciones:** lenguaje y temas "
            "de las publicaciones."
        )

        st.write(
            "**Hashtags:** categorías temáticas."
        )

        st.write(
            "**Respuestas del autor:** expresiones "
            "de comunicación escritas por el titular."
        )

        st.caption(
            "No se utilizan seguidores, likes, "
            "vistas ni comentarios de terceros "
            "para calcular los índices."
        )

    # Identify the current dataset.
    fingerprint = hashlib.sha256(
        json.dumps(
            prepared,
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()

    if (
            st.session_state.get("big_five_fingerprint")
            != fingerprint
    ):
        st.session_state["big_five_fingerprint"] = (
            fingerprint
        )

        st.session_state.pop(
            "big_five_result",
            None,
        )

        st.session_state.pop(
            "career_guidance_result",
            None,
        )

        st.session_state.pop(
            "career_guidance_fingerprint",
            None,
        )

    enough_data = (
            prepared["videos_with_content"] >= 3
    )

    if not enough_data:
        st.warning(
            "No hay suficiente contenido textual "
            "para ejecutar el análisis."
        )

    st.markdown("### 3. Ejecutar análisis")

    if st.button(
            "🧠 Analizar Big Five",
            type="primary",
            use_container_width=True,
            disabled=not enough_data,
            key="run_big_five",
    ):
        try:
            with st.spinner(
                    "Analizando el contenido con Gemini..."
            ):
                result = analyze_big_five(data)

            st.session_state["big_five_result"] = (
                result
            )

            # A new Big Five result invalidates the
            # previous professional guidance.
            st.session_state.pop(
                "career_guidance_result",
                None,
            )

            st.session_state.pop(
                "career_guidance_fingerprint",
                None,
            )

            st.success(
                "Análisis completado correctamente."
            )

        except Exception as error:
            st.session_state.pop(
                "big_five_result",
                None,
            )

            st.session_state.pop(
                "career_guidance_result",
                None,
            )

            st.error(
                f"No se pudo completar el análisis: {error}"
            )

    result = st.session_state.get(
        "big_five_result"
    )

    if result is None:
        return

    st.divider()

    st.markdown("### 4. Resultados Big Five")

    st.caption(
        "Los valores representan índices exploratorios "
        "de señales textuales, no porcentajes reales "
        "de personalidad. No tienen que sumar 100."
    )

    dimensions = result.get("dimensions", {})

    render_big_five_chart(dimensions)

    st.divider()

    st.subheader("Interpretación por dimensión")

    for key, label in TRAITS.items():
        item = dimensions.get(key, {})
        score = item.get("score")

        st.markdown(f"#### {label}")

        if score is None:
            st.info(
                "Sin puntuación: evidencia insuficiente "
                "o dimensión no evaluable."
            )

        else:
            st.progress(
                int(round(score)),
                text=f"Índice: {score:.0f} / 100",
            )

        interpretation = item.get(
            "interpretation", ""
        )

        if interpretation:
            st.write(interpretation)

        evidence = item.get("evidence", [])

        if evidence:
            with st.expander(
                    f"Ver evidencias de {label}"
            ):
                for evidence_text in evidence:
                    st.write(f"• {evidence_text}")

        st.divider()

    st.markdown("### 5. Interpretación general")

    st.markdown("**Resumen del contenido**")

    st.write(
        result.get(
            "content_summary",
            "No disponible.",
        )
    )

    st.markdown("**Conclusión**")

    st.write(
        result.get(
            "conclusion",
            "No disponible.",
        )
    )

    st.markdown("**Limitaciones**")

    st.write(
        result.get(
            "limitations",
            "Los resultados no constituyen "
            "una evaluación psicométrica.",
        )
    )


# ==========================================
# 3. PROFESSIONAL GUIDANCE
# ==========================================

def render_career_guidance():

    st.subheader("🎓 Orientación Profesional")

    st.write(
        "¿Ya sabes qué carrera te gustaría estudiar "
        "o ejercer? Descubre qué competencias puedes "
        "fortalecer, cómo desarrollarlas y dónde "
        "encontrar oportunidades de aprendizaje."
    )

    st.info(
        "Este módulo utiliza resultados exploratorios "
        "del análisis Big Five. No determina la "
        "personalidad real ni la aptitud profesional."
    )

    big_five_result = st.session_state.get(
        "big_five_result"
    )

    if big_five_result is None:
        st.warning(
            "Primero realiza el análisis Big Five "
            "en la pestaña anterior."
        )
        return

    dimensions = big_five_result.get(
        "dimensions", {}
    )

    # Find the highest available score.
    evaluated = []

    for key, label in TRAITS.items():
        item = dimensions.get(key, {})
        score = item.get("score")

        if isinstance(score, (int, float)):
            evaluated.append(
                (label, float(score))
            )

    st.markdown("### 1. Resultado destacado del perfil")

    if evaluated:
        dominant_name, dominant_score = max(
            evaluated,
            key=lambda item: item[1]
        )

        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(
                f"**Dimensión destacada: {dominant_name}**"
            )

            st.caption(
                "Es el índice exploratorio más alto "
                "entre las dimensiones evaluadas."
            )

        with col2:
            st.metric(
                "Índice",
                f"{dominant_score:.0f}/100"
            )

        st.progress(
            min(
                max(int(round(dominant_score)), 0),
                100,
            )
        )

    else:
        st.warning(
            "No hay dimensiones con puntuaciones "
            "disponibles para destacar."
        )

    with st.expander(
            "Ver las cinco dimensiones del perfil"
    ):
        for key, label in TRAITS.items():
            item = dimensions.get(key, {})
            score = item.get("score")

            if score is None:
                st.write(f"**{label}:** Sin datos")
            else:
                st.write(
                    f"**{label}:** {score:.0f}/100"
                )

    st.divider()

    st.markdown("### 2. Tu carrera y tus objetivos")

    with st.form("career_guidance_form"):

        career = st.text_input(
            "¿Qué carrera deseas estudiar o ejercer?",
            placeholder="Ejemplo: Ingeniería en Sistemas",
            max_chars=120,
        )

        skills = st.text_area(
            "¿Qué habilidades quisieras fortalecer?",
            placeholder=(
                "Ejemplo: organización, comunicación, "
                "programación, trabajo en equipo..."
            ),
            max_chars=1000,
        )

        goals = st.text_area(
            "¿Qué te gustaría conseguir en esa carrera?",
            placeholder=(
                "Ejemplo: diseñar sistemas, participar "
                "en proyectos y adquirir experiencia."
            ),
            max_chars=1000,
        )

        consent = st.checkbox(
            "Confirmo que el perfil analizado es mío "
            "o cuento con autorización de su titular "
            "para utilizar los resultados y enviarlos "
            "a Gemini con fines de orientación."
        )

        generate_button = st.form_submit_button(
            "✨ Generar mi plan de desarrollo",
            type="primary",
            use_container_width=True,
        )

    if generate_button:

        if not career.strip():
            st.warning(
                "Ingresa primero la carrera "
                "que te interesa."
            )

        elif not consent:
            st.warning(
                "Debes confirmar la autorización "
                "para continuar."
            )

        else:
            try:
                with st.spinner(
                        "Gemini está elaborando tu plan "
                        "de desarrollo profesional..."
                ):
                    guidance = generate_career_guidance(
                        big_five_result=big_five_result,
                        career=career,
                        skills=skills,
                        goals=goals,
                    )

                st.session_state[
                    "career_guidance_result"
                ] = guidance

                st.session_state[
                    "career_guidance_fingerprint"
                ] = st.session_state.get(
                    "big_five_fingerprint"
                )

                st.success(
                    "Plan de desarrollo generado."
                )

            except Exception as error:
                st.session_state.pop(
                    "career_guidance_result",
                    None,
                )

                st.error(
                    f"No se pudo generar el plan: {error}"
                )

    # Prevent displaying results from a different profile.
    if (
            st.session_state.get(
                "career_guidance_fingerprint"
            )
            != st.session_state.get(
        "big_five_fingerprint"
    )
    ):
        st.session_state.pop(
            "career_guidance_result",
            None,
        )

    guidance = st.session_state.get(
        "career_guidance_result"
    )

    if guidance is None:
        return

    st.divider()

    st.markdown(
        "## 📋 Tu plan de desarrollo profesional"
    )

    st.markdown(
        f"### 🎯 {guidance.get('career', career)}"
    )

    st.write(
        guidance.get("summary", "")
    )

    st.markdown("### 💪 Posibles fortalezas")

    strengths = guidance.get("strengths", [])

    for item in strengths:

        if not isinstance(item, dict):
            continue

        with st.container(border=True):
            st.markdown(
                f"**{item.get('name', '')}**"
            )

            st.write(
                item.get("explanation", "")
            )

    st.markdown(
        "### 🚀 Competencias que puedes fortalecer"
    )

    skills_to_improve = guidance.get(
        "skills_to_improve", []
    )

    for index, item in enumerate(
            skills_to_improve,
            start=1,
    ):

        if not isinstance(item, dict):
            continue

        skill_name = item.get(
            "skill", "Competencia"
        )

        with st.expander(
                f"{index}. {skill_name}",
                expanded=True,
        ):
            st.markdown(
                "**¿Por qué es importante "
                "para tu carrera?**"
            )

            st.write(
                item.get("importance", "")
            )

            st.markdown("**¿Cómo desarrollarla?**")

            st.write(
                item.get("how", "")
            )

            st.markdown(
                "**¿Dónde aprender o practicar?**"
            )

            st.write(
                item.get("where", "")
            )

            st.markdown(
                "**¿Cómo comprobar tu progreso?**"
            )

            st.write(
                item.get("evidence", "")
            )

    st.divider()

    st.markdown(
        "### 📅 Plan de mejora de cuatro semanas"
    )

    weekly_plan = guidance.get(
        "weekly_plan", []
    )

    for week in weekly_plan:

        if not isinstance(week, dict):
            continue

        with st.container(border=True):

            st.markdown(
                f"#### Semana {week.get('week', '')}"
            )

            st.write(
                f"**Objetivo:** "
                f"{week.get('objective', '')}"
            )

            st.markdown("**Actividades:**")

            for activity in week.get(
                    "activities", []
            ):
                st.write(f"• {activity}")

            st.write(
                f"**Evidencia de aprendizaje:** "
                f"{week.get('deliverable', '')}"
            )

    st.divider()

    st.markdown("### ⭐ Recomendación final")

    st.write(
        guidance.get(
            "final_recommendation", ""
        )
    )

    st.caption(
        guidance.get(
            "limitations",
            "Este plan es orientativo y no constituye "
            "una evaluación psicológica o profesional.",
        )
    )


# ==========================================
# 4. MAIN PAGE
# ==========================================

def render_embeddings():

    st.title("Análisis inteligente del perfil")

    big_five_tab, career_tab = st.tabs([
        "🧠 Big Five",
        "🎓 Orientación Profesional",
    ])

    with big_five_tab:
        render_big_five()

    with career_tab:
        render_career_guidance()
