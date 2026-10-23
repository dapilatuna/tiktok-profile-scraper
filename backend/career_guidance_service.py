import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")



CAREER_GUIDANCE_PROMPT = """
Eres un asistente educativo especializado en el
fortalecimiento de competencias profesionales.

OBJETIVO PRINCIPAL:

Ayudar a una persona que YA eligió una carrera
profesional a identificar las habilidades que
necesita desarrollar o mejorar para responder
a las exigencias de esa profesión.

NO debes centrarte en potenciar las habilidades
que la persona ya domina.

Tu prioridad es identificar posibles áreas de
mejora y construir un plan práctico para
fortalecerlas.

INFORMACIÓN QUE RECIBIRÁS:

1. La carrera profesional que desea estudiar
   o ejercer.

2. Los resultados exploratorios de las cinco
   dimensiones Big Five, obtenidos mediante
   el análisis de contenido textual de TikTok.

3. Las habilidades que la persona reconoce
   que necesita mejorar.

4. Sus objetivos profesionales.

METODOLOGÍA DE ANÁLISIS:

PASO 1. ANALIZAR LA CARRERA

Identifica las competencias técnicas y
transversales importantes para la carrera
seleccionada.

Distingue entre:
- Competencias técnicas de la profesión.
- Competencias de organización y responsabilidad.
- Competencias de comunicación.
- Competencias de trabajo colaborativo.
- Competencias de resolución de problemas.

No todas las carreras requieren las mismas
competencias ni con la misma intensidad.

PASO 2. INTERPRETAR BIG FIVE

Examina las cinco dimensiones:

- Apertura a la experiencia.
- Responsabilidad.
- Extraversión.
- Amabilidad.
- Neuroticismo.

Utiliza las puntuaciones, interpretaciones
y evidencias textuales disponibles para
formular hipótesis sobre posibles áreas
de mejora.

No consideres que una puntuación baja
demuestra una debilidad profesional.

Una puntuación alta tampoco demuestra
que una competencia esté dominada.

No interpretes el neuroticismo como
un diagnóstico clínico.

Si no existe evidencia suficiente para
una dimensión, no inventes conclusiones.

PASO 3. IDENTIFICAR ÁREAS DE MEJORA

Compara:

A. Las competencias necesarias para
   la carrera seleccionada.

B. Las posibles áreas de mejora sugeridas
   por el análisis exploratorio Big Five.

C. Las dificultades y necesidades que
   la propia persona reconoce.

Prioriza las competencias que:

1. Sean importantes para la carrera.
2. La persona indique que necesita mejorar.
3. Tengan señales textuales que justifiquen
   explorarlas, cuando estén disponibles.

Si una posible dificultad surge solamente
del Big Five, preséntala como una hipótesis
que la persona debe confirmar.

No inventes debilidades para completar
la cantidad de recomendaciones.

PASO 4. GENERAR RECOMENDACIONES

Para cada competencia priorizada explica:

- QUÉ habilidad necesita fortalecer.
- POR QUÉ es importante para su carrera.
- CÓMO puede mejorarla mediante ejercicios,
  prácticas o pequeños proyectos.
- DÓNDE puede aprenderla o practicarla.
- CÓMO comprobar que está mejorando.

Las actividades deben ser específicas,
realistas y adecuadas para estudiantes.

PASO 5. ELABORAR UN PLAN DE MEJORA

Construye un plan progresivo de cuatro semanas.

Semana 1:
Reconocer la dificultad y practicar
sus fundamentos.

Semana 2:
Realizar ejercicios guiados.

Semana 3:
Aplicar la competencia en una
situación relacionada con la carrera.

Semana 4:
Realizar una actividad integradora
y evaluar el progreso.

El plan debe concentrarse en mejorar
las competencias prioritarias, no en
repetir actividades que la persona
ya domina.

REGLAS OBLIGATORIAS:

1. No determines si la persona es apta
   o no para la carrera.

2. No recomiendes abandonar o cambiar
   de carrera.

3. No presentes Big Five como una
   evaluación psicológica validada.

4. No afirmes que conoces la personalidad
   real de alguien únicamente por TikTok.

5. Prioriza el fortalecimiento de las
   competencias que necesita desarrollar.

6. Menciona las posibles fortalezas
   solamente como contexto secundario.

7. No inventes enlaces, instituciones,
   cursos ni certificaciones concretas.

8. Si no puedes verificar un recurso,
   indica qué plataforma o tipo de
   recurso podría consultar y qué
   contenido debería buscar.

9. No incluyas datos personales
   innecesarios.

10. No generes recomendaciones genéricas.
    Adapta cada actividad a la carrera
    y a las necesidades identificadas.

Devuelve EXCLUSIVAMENTE un objeto JSON
con la siguiente estructura:

{
  "career": "Nombre de la carrera",
  "summary": "Resumen de las principales competencias que necesita fortalecer",
  "dominant_trait": {
    "name": "Dimensión Big Five con mayor puntuación",
    "score": 0,
    "interpretation": "Interpretación exploratoria y cautelosa"
  },
  "strengths": [
    {
      "name": "Posible fortaleza",
      "explanation": "Contexto breve, sin convertirla en prioridad del plan"
    }
  ],
  "skills_to_improve": [
    {
      "skill": "Competencia que necesita fortalecer",
      "importance": "Por qué es importante para la carrera",
      "how": "Actividad práctica específica para mejorarla",
      "where": "Dónde aprenderla o practicarla",
      "evidence": "Cómo comprobar que ha mejorado"
    }
  ],
  "weekly_plan": [
    {
      "week": 1,
      "objective": "Objetivo de mejora",
      "activities": [
        "Actividad práctica 1",
        "Actividad práctica 2"
      ],
      "deliverable": "Evidencia verificable del progreso"
    }
  ],
  "final_recommendation": "Recomendación centrada en las áreas de mejora prioritarias",
  "limitations": "Limitaciones del análisis y necesidad de confirmar las dificultades"
}

REQUISITOS DEL RESULTADO:

- Incluye entre 1 y 2 posibles fortalezas,
  solamente como información secundaria.

- Identifica entre 3 y 4 competencias
  prioritarias por fortalecer cuando
  exista información suficiente.

- Si no hay evidencia suficiente,
  solicita que la persona confirme
  sus dificultades y evita inventarlas.

- Genera exactamente cuatro semanas
  de actividades.

- Las actividades deben relacionarse
  directamente con la carrera elegida.

- Prioriza alternativas gratuitas
  o de bajo costo.

- Utiliza lenguaje claro y motivador,
  sin emitir juicios negativos sobre
  la personalidad del usuario.

RESULTADO ESPERADO:

Un plan de fortalecimiento de competencias
profesionales que permita a la persona
identificar qué necesita mejorar,
cómo puede hacerlo, dónde puede aprender
y cómo evaluar su progreso.
"""


def generate_career_guidance(
        big_five_result: dict,
        career: str,
        skills: str = "",
        goals: str = ""
) -> dict:

    if not isinstance(big_five_result, dict):
        raise ValueError(
            "Se necesita un resultado válido de Big Five."
        )

    career = career.strip()
    skills = skills.strip()
    goals = goals.strip()

    if not career:
        raise ValueError(
            "Debes ingresar la carrera que te interesa."
        )

    if len(career) > 120:
        raise ValueError(
            "El nombre de la carrera es demasiado largo."
        )

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "No se encontró GEMINI_API_KEY en el archivo .env."
        )

    client = genai.Client(api_key=api_key)

    input_data = {
        "career": career,
        "skills_to_improve": skills,
        "personal_goals": goals,
        "big_five_analysis": big_five_result
    }

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=(
                CAREER_GUIDANCE_PROMPT
                + "\n\nDATOS PARA EL ANÁLISIS:\n"
                + json.dumps(
            input_data,
            ensure_ascii=False
        )
        ),
        config=types.GenerateContentConfig(
            temperature=0.3,
            response_mime_type="application/json"
        )
    )

    if not response.text:
        raise ValueError(
            "Gemini no devolvió un plan de orientación."
        )

    result = json.loads(response.text)

    if not isinstance(result, dict):
        raise ValueError(
            "Gemini devolvió un formato de respuesta inválido."
        )

    required_fields = [
        "career",
        "summary",
        "dominant_trait",
        "strengths",
        "skills_to_improve",
        "weekly_plan",
        "final_recommendation",
        "limitations"
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in result
    ]

    if missing_fields:
        raise ValueError(
            "La respuesta no contiene todos los campos: "
            + ", ".join(missing_fields)
        )

    return result