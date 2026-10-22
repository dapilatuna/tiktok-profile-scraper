
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
from frontend.services.semantic_service import (
    prepare_semantic_data,
    analyze_semantic_similarity,
)

# ==========================================
# BIG FIVE CHART
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

    # Keep all five dimensions in the chart.
    # Null scores are not converted into real scores.

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

    # Background scale from 0 to 100.
    background = base.mark_bar(
        color="#E9E2F1",
        cornerRadiusEnd=6,
        size=25,
    ).encode(
        x=alt.value(0),
        x2=alt.datum(100),
    )

    # Bars only for dimensions with scores.
    bars = (
        alt.Chart(
            df[df["Índice"].notna()]
        )
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

    # Numerical labels for evaluated dimensions.
    labels = (
        alt.Chart(
            df[df["Índice"].notna()]
        )
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

    # Missing values are displayed as text,
    # never interpreted as a score of zero.
    missing = (
        alt.Chart(
            df[df["Índice"].isna()]
        )
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
# BIG FIVE ANALYSIS PAGE
# ==========================================

def render_big_five():
    st.subheader("Análisis Big Five")

    st.caption(
        "Análisis exploratorio del contenido público "
        "mediante inteligencia artificial."
    )

    # ==========================================
    # 1. DATA SOURCE
    # ==========================================

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

    # ==========================================
    # 2. PREPARE PROFILE DATA
    # ==========================================

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

    # ==========================================
    # IDENTIFY CURRENT DATASET
    # ==========================================

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

    enough_data = (
            prepared["videos_with_content"] >= 3
    )

    if not enough_data:
        st.warning(
            "No hay suficiente contenido textual "
            "para ejecutar el análisis."
        )

    # ==========================================
    # 3. RUN ANALYSIS
    # ==========================================

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

            st.success(
                "Análisis completado correctamente."
            )

        except Exception as error:
            st.session_state.pop(
                "big_five_result",
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

    # ==========================================
    # 4. BIG FIVE RESULTS
    # ==========================================

    st.divider()

    st.markdown("### 4. Resultados Big Five")

    st.caption(
        "Los valores representan índices exploratorios "
        "de señales textuales, no porcentajes reales "
        "de personalidad. No tienen que sumar 100."
    )

    dimensions = result.get("dimensions", {})

    # First display the statistical chart.
    render_big_five_chart(dimensions)

    st.divider()

    # ==========================================
    # INTERPRETATION BY DIMENSION
    # ==========================================

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

    # ==========================================
    # 5. GENERAL INTERPRETATION
    # ==========================================

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


def render_semantic_analysis():
    st.subheader("Análisis semántico con embeddings")

    st.caption(
        "Comparación del significado de las publicaciones "
        "mediante vectores numéricos y similitud coseno."
    )

    st.markdown("### 1. Seleccionar información")

    source = st.radio(
        "¿De dónde deseas obtener los datos?",
        [
            "Usar datos del scraping actual",
            "Subir archivo JSON",
        ],
        horizontal=True,
        key="semantic_source",
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
            key="semantic_file",
        )

        if uploaded_file is not None:
            try:
                data = json.loads(
                    uploaded_file.getvalue().decode("utf-8")
                )
            except (ValueError, UnicodeDecodeError):
                st.error("No se pudo leer el archivo JSON.")
                return

    if data is None:
        return

    try:
        prepared = prepare_semantic_data(data)
    except ValueError as error:
        st.error(str(error))
        return

    st.markdown("### 2. Información disponible")

    st.write(
        f"**Perfil:** "
        f"@{prepared['username'] or 'No identificado'}"
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "Videos extraídos",
        prepared["videos_found"],
    )

    col2.metric(
        "Videos con texto",
        prepared["videos_with_text"],
    )

    with st.expander("¿Qué información se analiza?"):
        st.write(
            "Se utilizan descripciones, hashtags y "
            "respuestas escritas por el autor."
        )
        st.write(
            "Los textos se convierten en embeddings "
            "para comparar su significado."
        )
        st.caption(
            "Los seguidores, likes y visualizaciones "
            "no se utilizan para calcular "
            "la similitud semántica."
        )

    fingerprint = hashlib.sha256(
        json.dumps(
            prepared,
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        ).encode("utf-8")
    ).hexdigest()

    if (
            st.session_state.get("semantic_fingerprint")
            != fingerprint
    ):
        st.session_state["semantic_fingerprint"] = (
            fingerprint
        )
        st.session_state.pop(
            "semantic_result",
            None,
        )

    enough_data = (
            prepared["videos_with_text"] >= 2
    )

    if not enough_data:
        st.warning(
            "Se necesitan al menos dos videos "
            "con contenido textual."
        )

    st.markdown("### 3. Ejecutar análisis")

    if st.button(
            "🔎 Analizar similitud semántica",
            type="primary",
            use_container_width=True,
            disabled=not enough_data,
            key="run_semantic",
    ):
        try:
            with st.spinner(
                    "Generando embeddings y "
                    "comparando publicaciones..."
            ):
                result = analyze_semantic_similarity(data)

            st.session_state["semantic_result"] = result

            st.success(
                "Análisis semántico completado."
            )

        except Exception as error:
            st.session_state.pop(
                "semantic_result",
                None,
            )
            st.error(
                f"No se pudo completar el análisis: {error}"
            )

    result = st.session_state.get("semantic_result")

    if result is None:
        return

    st.divider()
    st.markdown("### 4. Resultados del análisis")

    col1, col2 = st.columns(2)

    col1.metric(
        "Videos analizados",
        result["videos_analyzed"],
    )

    col2.metric(
        "Dimensiones del vector",
        result["embedding_dimensions"],
    )

    st.caption(
        f"Modelo utilizado: {result['model']}"
    )

    pairs = result.get("pairs", [])

    if not pairs:
        st.info(
            "No se encontraron pares de videos "
            "para comparar."
        )
        return

    st.subheader("Similitud entre publicaciones")

    # Show the ten most similar pairs.
    top_pairs = pairs[:10]

    chart_data = pd.DataFrame([
        {
            "Comparación": (
                f"{pair['video_a']} y {pair['video_b']}"
            ),
            "Similitud": pair["similarity"],
        }
        for pair in top_pairs
    ])

    chart = (
        alt.Chart(chart_data)
        .mark_bar(
            color="#8B5CF6",
            cornerRadiusEnd=5,
        )
        .encode(
            x=alt.X(
                "Comparación:N",
                sort=None,
                title="Pares de publicaciones",
                axis=alt.Axis(
                    labelAngle=-35,
                    labelLimit=150,
                ),
            ),
            y=alt.Y(
                "Similitud:Q",
                scale=alt.Scale(
                    domain=[-100, 100],
                ),
                axis=alt.Axis(
                    title="Similitud coseno × 100",
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "Comparación:N",
                    title="Publicaciones",
                ),
                alt.Tooltip(
                    "Similitud:Q",
                    title="Similitud",
                    format=".2f",
                ),
            ],
        )
        .properties(
            height=360,
        )
    )

    st.altair_chart(
        chart,
        use_container_width=True,
    )

    st.caption(
        "El gráfico muestra hasta diez pares con "
        "mayor similitud coseno. Los valores van "
        "de -100 a 100; no son porcentajes "
        "de coincidencia literal."
    )

    st.divider()
    st.subheader("Publicaciones más similares")

    for index, pair in enumerate(pairs[:5], start=1):
        with st.expander(
                f"{index}. {pair['video_a']} ↔ "
                f"{pair['video_b']} — "
                f"{pair['similarity']:.2f}"
        ):
            st.markdown(
                f"**{pair['video_a']}**"
            )
            st.write(pair["text_a"])

            st.markdown(
                f"**{pair['video_b']}**"
            )
            st.write(pair["text_b"])

    st.divider()
    st.subheader("Interpretación general")

    highest = pairs[0]
    lowest = pairs[-1]

    st.write(
        f"Se analizaron {result['videos_analyzed']} "
        "publicaciones con contenido textual."
    )

    st.write(
        f"El par con mayor similitud fue "
        f"**{highest['video_a']} y "
        f"{highest['video_b']}**, "
        f"con un índice de "
        f"**{highest['similarity']:.2f}**."
    )

    st.write(
        f"El par con menor similitud fue "
        f"**{lowest['video_a']} y "
        f"{lowest['video_b']}**, "
        f"con un índice de "
        f"**{lowest['similarity']:.2f}**."
    )

    st.info(
        "La similitud semántica indica cercanía "
        "entre representaciones vectoriales del "
        "contenido. No demuestra que dos videos "
        "sean idénticos ni determina la "
        "personalidad de su autor."
    )


# ==========================================
# EMBEDDINGS MAIN PAGE
# ==========================================

def render_embeddings():
    st.title("Análisis inteligente del perfil")

    big_five_tab, semantic_tab = st.tabs(
        [
            "🧠 Big Five",
            "🔎 Análisis semántico",
        ]
    )

    with big_five_tab:
        render_big_five()

    with semantic_tab:
        render_semantic_analysis()
