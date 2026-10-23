
import hashlib
import json
import math

import streamlit as st

from backend.career_guidance_service import (
    generate_career_guidance,
)


TRAIT_LABELS = {
    "openness": "Apertura a la experiencia",
    "conscientiousness": "Responsabilidad",
    "extraversion": "Extraversión",
    "agreeableness": "Amabilidad",
    "neuroticism": "Neuroticismo",
}


# ==========================================
# 1. HELPERS
# ==========================================

def get_fingerprint(data: dict) -> str:
    serialized = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()


def get_valid_score(value):
    if isinstance(value, bool):
        return None

    if not isinstance(value, (int, float)):
        return None

    if not math.isfinite(value):
        return None

    if not 0 <= value <= 100:
        return None

    return float(value)


# ==========================================
# 2. CAREER GUIDANCE PAGE
# ==========================================

def render_career_guidance(data: dict):

    st.header("🎓 Orientación Profesional")

    st.write(
        "Conoce las competencias importantes para "
        "la carrera que deseas estudiar o ejercer "
        "y descubre cómo puedes fortalecerlas."
    )

    st.caption(
        "Las recomendaciones combinan información "
        "sobre la carrera con señales exploratorias "
        "del análisis Big Five. No constituyen "
        "una evaluación psicológica ni una medición "
        "directa de habilidades profesionales."
    )

    # ==========================================
    # 3. VALIDATE PROFILE
    # ==========================================

    if not isinstance(data, dict) or not data:
        st.warning(
            "Primero realiza una extracción "
            "del perfil de TikTok."
        )
        return

    profile = data.get("profile", {})

    if not isinstance(profile, dict):
        profile = {}

    username = profile.get(
        "username"
    ) or "No identificado"

    profile_fingerprint = get_fingerprint(data)

    if (
            st.session_state.get(
                "career_profile_fingerprint"
            )
            != profile_fingerprint
    ):
        st.session_state[
            "career_profile_fingerprint"
        ] = profile_fingerprint

        st.session_state.pop(
            "career_guidance_result",
            None,
        )

        st.session_state.pop(
            "career_guidance_request",
            None,
        )

    # ==========================================
    # 4. REUSE BIG FIVE RESULTS
    # ==========================================

    big_five_result = st.session_state.get(
        "big_five_result"
    )

    if not isinstance(big_five_result, dict):
        st.warning(
            "Primero ejecuta el análisis Big Five "
            "en la pestaña anterior."
        )
        return

    dimensions = big_five_result.get(
        "dimensions", {}
    )

    if not isinstance(dimensions, dict):
        st.error(
            "El resultado Big Five no contiene "
            "dimensiones válidas."
        )
        return

    evaluated_traits = []

    for key, label in TRAIT_LABELS.items():
        item = dimensions.get(key, {})

        if not isinstance(item, dict):
            continue

        score = get_valid_score(
            item.get("score")
        )

        if score is not None:
            evaluated_traits.append({
                "name": label,
                "score": score,
            })

    if not evaluated_traits:
        st.warning(
            "No existen puntuaciones Big Five "
            "disponibles para elaborar el análisis."
        )
        return

    # Use a fingerprint of the actual result,
    # not only the profile username.
    big_five_fingerprint = get_fingerprint(
        big_five_result
    )

    st.success(
        f"Perfil @{username}: "
        "análisis Big Five disponible."
    )

    with st.expander(
            "🧠 Consultar resultados Big Five"
    ):
        dominant_trait = max(
            evaluated_traits,
            key=lambda item: item["score"],
        )

        st.markdown(
            "**Dimensión con mayor índice:** "
            f"{dominant_trait['name']}"
        )

        st.metric(
            "Índice exploratorio",
            f"{dominant_trait['score']:.0f}/100",
        )

        for key, label in TRAIT_LABELS.items():
            item = dimensions.get(key, {})

            if not isinstance(item, dict):
                continue

            score = get_valid_score(
                item.get("score")
            )

            if score is None:
                st.write(
                    f"**{label}:** Sin datos"
                )
            else:
                st.progress(
                    int(round(score)),
                    text=(
                        f"{label}: "
                        f"{score:.0f}/100"
                    ),
                )

    # ==========================================
    # 5. CAREER INPUT
    # ==========================================

    st.divider()

    st.subheader(
        "2. Selecciona tu carrera profesional"
    )

    with st.form("career_guidance_form"):

        career = st.text_input(
            "¿Qué carrera deseas estudiar o ejercer?",
            placeholder="Ejemplo: Psicología",
            max_chars=120,
        )

        generate_button = st.form_submit_button(
            "✨ Generar análisis y plan de fortalecimiento",
            type="primary",
            use_container_width=True,
        )

    # ==========================================
    # 6. GENERATE PLAN WITH GEMINI
    # ==========================================

    if generate_button:

        career = career.strip()

        if not career:
            st.warning(
                "Ingresa una carrera profesional."
            )

        else:
            # Clear the previous plan before
            # requesting a new one.
            st.session_state.pop(
                "career_guidance_result",
                None,
            )

            st.session_state.pop(
                "career_guidance_request",
                None,
            )

            try:
                with st.spinner(
                        "Gemini está analizando las "
                        "competencias de la carrera "
                        "y elaborando tu plan..."
                ):

                    guidance = generate_career_guidance(
                        big_five_result=big_five_result,
                        career=career,
                    )

                if not isinstance(guidance, dict):
                    raise ValueError(
                        "Gemini no devolvió "
                        "un resultado válido."
                    )

                st.session_state[
                    "career_guidance_result"
                ] = guidance

                st.session_state[
                    "career_guidance_request"
                ] = {
                    "profile_fingerprint": (
                        profile_fingerprint
                    ),
                    "big_five_fingerprint": (
                        big_five_fingerprint
                    ),
                    "career": career,
                }

                st.success(
                    "Análisis y plan de "
                    "fortalecimiento generados."
                )

            except Exception as error:
                st.error(
                    "No se pudo generar el plan: "
                    f"{error}"
                )

    # ==========================================
    # 7. VALIDATE CURRENT PLAN
    # ==========================================

    request = st.session_state.get(
        "career_guidance_request"
    )

    if not isinstance(request, dict):
        request = {}

    if (
            request.get("profile_fingerprint")
            != profile_fingerprint
            or request.get("big_five_fingerprint")
            != big_five_fingerprint
    ):
        st.session_state.pop(
            "career_guidance_result",
            None,
        )

        st.session_state.pop(
            "career_guidance_request",
            None,
        )

    guidance = st.session_state.get(
        "career_guidance_result"
    )

    if not isinstance(guidance, dict):
        return

    # ==========================================
    # 8. PROFESSIONAL ANALYSIS
    # ==========================================

    st.divider()

    st.header(
        "📋 Análisis y plan de fortalecimiento"
    )

    selected_career = request.get(
        "career", ""
    )

    st.subheader(
        f"🎯 {selected_career}"
    )

    st.write(
        guidance.get("summary", "")
    )

    # ==========================================
    # 9. COMPETENCIES TO STRENGTHEN
    # ==========================================

    st.subheader(
        "🚀 Competencias recomendadas para fortalecer"
    )

    st.caption(
        "Estas recomendaciones consideran las "
        "competencias de la carrera y las señales "
        "exploratorias del perfil. No demuestran "
        "que la persona tenga deficiencias."
    )

    skills_to_improve = guidance.get(
        "skills_to_improve", []
    )

    if not skills_to_improve:
        st.info(
            "No se encontraron competencias "
            "para recomendar con la información "
            "disponible."
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
                "para esta carrera?**"
            )

            st.write(
                item.get("importance", "")
            )

            st.markdown(
                "**¿Cómo puedes fortalecerla?**"
            )

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

    # ==========================================
    # 10. FOUR-WEEK PLAN
    # ==========================================

    st.divider()

    st.subheader(
        "📅 Plan de fortalecimiento de 4 semanas"
    )

    weekly_plan = guidance.get(
        "weekly_plan", []
    )

    if not weekly_plan:
        st.info(
            "No se generó un plan semanal."
        )

    for week in weekly_plan:

        if not isinstance(week, dict):
            continue

        week_number = week.get(
            "week", ""
        )

        with st.container(border=True):

            st.markdown(
                f"### Semana {week_number}"
            )

            st.write(
                "**Objetivo:** "
                f"{week.get('objective', '')}"
            )

            st.markdown(
                "**Actividades prácticas:**"
            )

            activities = week.get(
                "activities", []
            )

            if isinstance(activities, list):
                for activity in activities:
                    st.write(
                        f"• {activity}"
                    )

            st.markdown(
                "**Resultado esperado:**"
            )

            st.write(
                week.get(
                    "deliverable", ""
                )
            )

    # ==========================================
    # 11. FINAL RECOMMENDATION
    # ==========================================

    st.divider()

    st.subheader(
        "⭐ Recomendación final"
    )

    st.write(
        guidance.get(
            "final_recommendation", ""
        )
    )

    st.caption(
        guidance.get(
            "limitations",
            "El análisis es exploratorio "
            "y no representa una evaluación "
            "psicológica ni profesional.",
        )
    )

    # ==========================================
    # 12. EXPORT PLAN
    # ==========================================

    st.download_button(
        "📄 Descargar plan en JSON",
        data=json.dumps(
            guidance,
            ensure_ascii=False,
            indent=2,
        ),
        file_name="career_guidance.json",
        mime="application/json",
        use_container_width=True,
    )
