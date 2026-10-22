# TikTok Profile Scraper

Aplicación web desarrollada en **Python y Streamlit** para extraer, procesar, visualizar y exportar información pública de perfiles de TikTok. Incorpora dos módulos adicionales de análisis de contenido: **Big Five mediante inteligencia artificial generativa** y **similitud semántica mediante embeddings vectoriales**.

## 1. Descripción

El sistema permite consultar un perfil público de TikTok a partir de su nombre de usuario, recuperar información general del perfil y procesar publicaciones, métricas de interacción y comentarios disponibles.

La extracción se realiza mediante **Playwright y Google Chrome**, utilizando selectores del DOM y datos JSON incrustados en el HTML de TikTok, sin utilizar la API oficial de esta plataforma.

Los resultados pueden visualizarse en Streamlit y exportarse como un archivo JSON. Posteriormente, el usuario puede analizar el contenido extraído mediante los módulos Big Five y análisis semántico, utilizando la extracción de la sesión actual o un archivo JSON previamente generado.

Los módulos de inteligencia artificial utilizan la **API de Google Gemini**, independientemente del mecanismo empleado para extraer los datos de TikTok.

## 2. Funcionalidades

### 2.1. Extracción de información del perfil

El sistema recupera, cuando están disponibles:

- Nombre de usuario y nombre público.
- Biografía.
- Número de seguidores y cuentas seguidas.
- Total de me gusta y publicaciones.
- Estado de verificación.
- Estado de privacidad.
- Enlace del perfil.

La información se obtiene principalmente del JSON incrustado en el HTML del perfil.

### 2.2. Descubrimiento y procesamiento de publicaciones

- Identificación de publicaciones mediante selectores del DOM.
- Recuperación de enlaces e identificadores de videos.
- Desplazamiento vertical para descubrir publicaciones.
- Identificación de videos fijados.
- Apertura de publicaciones para recuperar información adicional.
- Extracción de descripciones, fechas y métricas disponibles.
- Recuperación de hashtags, información musical y duración cuando TikTok los proporciona.
- Selección de hasta 10 publicaciones, utilizando las fechas recuperadas cuando es posible verificarlas.

Si no se recuperan todas las fechas necesarias, el sistema conserva el orden de los videos normales y registra una advertencia.

### 2.3. Extracción de comentarios

- Apertura de la sección de comentarios cuando corresponde.
- Desplazamiento para recuperar comentarios visibles.
- Intento de expansión de respuestas.
- Recuperación de información disponible sobre comentarios y sus autores.
- Registro de la cantidad de comentarios efectivamente extraídos.

La cantidad recuperada puede ser inferior al total indicado por TikTok.

### 2.4. Visualización y exportación

- Interfaz web desarrollada con Streamlit.
- Presentación de información general del perfil.
- Visualización de publicaciones y sus métricas.
- Visualización de comentarios disponibles.
- Advertencias cuando una parte de la extracción no se completa.
- Exportación de resultados en formato JSON.

El archivo exportado contiene información del perfil, reporte de publicaciones, resultados seleccionados y fecha de extracción.

### 2.5. Análisis Big Five

El módulo utiliza el modelo `gemini-3.5-flash-lite` para buscar señales lingüísticas relacionadas con las cinco dimensiones del Big Five:

1. **Apertura a la experiencia:** curiosidad, creatividad, exploración de ideas y diversidad temática.
2. **Responsabilidad:** organización, planificación, disciplina y constancia.
3. **Extraversión:** interacción social, comunicación y participación.
4. **Amabilidad:** cooperación, cortesía, empatía y agradecimiento.
5. **Neuroticismo:** referencias textuales a preocupaciones, estrés, tensión y respuestas emocionales ante situaciones difíciles.

El análisis considera las descripciones, los hashtags y las respuestas identificadas como escritas por el titular del perfil.

Para cada dimensión, Gemini puede devolver un índice exploratorio entre 0 y 100 cuando considera que existe evidencia textual suficiente, o `null` cuando la información no permite asignarlo.

Los resultados se presentan mediante:

- Gráfico comparativo de las cinco dimensiones.
- Índices disponibles y dimensiones sin puntuación.
- Interpretaciones y evidencias textuales.
- Resumen del contenido.
- Conclusión y limitaciones.

**Alcance metodológico:** el análisis identifica patrones lingüísticos en publicaciones. No aplica un test psicométrico, no determina la personalidad real del usuario y no constituye una evaluación clínica. Las puntuaciones son índices exploratorios generados por IA, no medidas psicométricas validadas.

### 2.6. Análisis semántico mediante embeddings

El módulo transforma el contenido textual de las publicaciones en representaciones vectoriales mediante el modelo `gemini-embedding-001`.

Utiliza embeddings de **768 dimensiones** con la tarea `SEMANTIC_SIMILARITY`.

El procedimiento comprende:

1. Preparación del contenido textual disponible.
2. Generación de un embedding por publicación analizada.
3. Cálculo de similitud coseno entre pares de vectores.
4. Conversión del resultado a una escala de -100 a 100.
5. Ordenamiento de los pares según su similitud.
6. Visualización gráfica y consulta de los textos comparados.

El módulo presenta:

- Número de publicaciones analizadas.
- Modelo utilizado y dimensionalidad de los vectores.
- Gráfico de los pares de publicaciones más similares.
- Textos correspondientes a los pares comparados.
- Resultados de mayor y menor similitud.

La similitud semántica compara la cercanía entre representaciones vectoriales de textos. No mide personalidad ni utiliza la popularidad de los videos como criterio de comparación.

### 2.7. Fuentes de información para los análisis

Los módulos Big Five y análisis semántico permiten:

- **Usar el scraping actual:** reutilizar los datos disponibles en la sesión de Streamlit.
- **Subir un archivo JSON:** analizar resultados extraídos previamente.

Cada módulo ejecuta su análisis cuando el usuario presiona el botón correspondiente.

## 3. Tecnologías

| Tecnología | Función |
|---|---|
| Python | Lógica de extracción, procesamiento y análisis |
| Playwright | Automatización del navegador y lectura del DOM |
| Google Chrome | Navegación por TikTok |
| Streamlit | Interfaz web y presentación de resultados |
| Beautiful Soup | Dependencia incluida en el proyecto para procesamiento HTML |
| JSON | Lectura, estructuración y exportación de información |
| CSS | Personalización visual |
| Google Gen AI SDK | Comunicación con los modelos Gemini |
| Gemini Flash Lite | Análisis lingüístico Big Five |
| Gemini Embedding | Generación de vectores semánticos |
| python-dotenv | Carga de variables de entorno |
| Pandas | Organización de datos para gráficos |
| Altair | Visualización de gráficos |
| Git y GitHub | Control de versiones |

## 4. Estructura del proyecto

```text
tiktok-profile-scraper/
├── backend/
│   ├── extractors/
│   │   ├── comment_extractor.py
│   │   ├── metadata_extractor.py
│   │   ├── profile_extractor.py
│   │   └── video_extractor.py
│   ├── parsers/
│   │   ├── html_parser.py
│   │   ├── json_parser.py
│   │   └── metric_parser.py
│   ├── big_five_service.py
│   ├── browser_manager.py
│   ├── scraper.py
│   ├── semantic_service.py
│   └── validator.py
├── frontend/
│   ├── components/
│   │   ├── comment_table.py
│   │   ├── profile_card.py
│   │   ├── sidebar.py
│   │   └── video_card.py
│   ├── pages/
│   │   ├── comments.py
│   │   ├── embeddings.py
│   │   ├── home.py
│   │   ├── profile.py
│   │   └── videos.py
│   ├── services/
│   │   ├── big_five_service.py
│   │   ├── scraper_service.py
│   │   └── semantic_service.py
│   ├── styles/
│   │   └── theme.py
│   ├── utils/
│   │   └── session_manager.py
│   ├── app.py
│   └── styles.css
├── data/
├── tests/
├── .gitignore
├── README.md
└── requirements.txt
```

El archivo `.env` se utiliza localmente para la clave de Gemini y debe permanecer excluido del repositorio.

**Backend:** implementa validación, navegación, extracción, procesamiento de información, análisis Big Five y cálculo de similitud semántica.

**Frontend:** implementa navegación, formularios, componentes visuales, gráficos, exportación JSON y gestión de resultados en la sesión.

Los servicios del frontend se comunican directamente con las funciones Python del backend. No se utiliza FastAPI ni un servidor HTTP independiente para esta comunicación.

## 5. Funcionamiento

### 5.1. Extracción web

1. El usuario introduce el nombre del perfil.
2. `validate_username()` valida el identificador.
3. `extract_profile()` abre el perfil mediante Chrome y Playwright.
4. `read_embedded_json()` recupera y convierte los datos JSON incrustados.
5. `discover_videos()` identifica las publicaciones desde el DOM.
6. `enrich_videos_with_comments()` abre publicaciones y recupera metadatos y comentarios.
7. `extract_videos()` selecciona las publicaciones que formarán parte del resultado.
8. `run_extraction()` organiza los resultados del perfil y las publicaciones.
9. Streamlit muestra la información y permite exportarla en JSON.

### 5.2. Big Five

1. El usuario selecciona la fuente de datos.
2. `prepare_profile_data()` identifica y organiza el contenido textual.
3. `analyze_big_five()` comprueba la información disponible.
4. El backend envía las instrucciones y los textos a Gemini.
5. Gemini devuelve una respuesta estructurada en JSON.
6. El backend valida las cinco dimensiones.
7. Streamlit muestra los resultados, el gráfico y las interpretaciones.

### 5.3. Análisis semántico

1. El usuario selecciona la fuente de datos.
2. `prepare_semantic_data()` organiza los textos de las publicaciones.
3. `analyze_semantic_similarity()` solicita los embeddings a Gemini.
4. `cosine_similarity()` calcula la similitud entre dos vectores.
5. El sistema compara los pares de publicaciones y ordena los resultados.
6. Streamlit muestra el gráfico y los textos asociados.

## 6. Instalación y ejecución

### Requisitos

- Python 3.10 o superior.
- Google Chrome.
- Conexión a Internet.
- Clave de Gemini para utilizar los módulos de inteligencia artificial.

### 6.1. Clonar el repositorio

```powershell
git clone https://github.com/dapilatuna/tiktok-profile-scraper.git
cd tiktok-profile-scraper
```

### 6.2. Crear y activar el entorno virtual

```powershell
python -m venv .venv-scraper
.\.venv-scraper\Scripts\Activate.ps1
```

### 6.3. Instalar dependencias

```powershell
python -m pip install -r requirements.txt
```

### 6.4. Configurar Gemini

Crear un archivo `.env` en la raíz del proyecto:

```dotenv
GEMINI_API_KEY=TU_CLAVE_DE_GEMINI
```

La clave debe mantenerse privada y no debe incluirse en GitHub.

### 6.5. Ejecutar la aplicación

```powershell
python -m streamlit run frontend/app.py
```

Abrir `http://localhost:8501` en el navegador.

## 7. Limitaciones

### Extracción

- Depende del contenido que TikTok presenta en el navegador.
- Los cambios del DOM o del JSON incrustado pueden afectar la extracción.
- Algunas métricas, fechas, publicaciones o respuestas pueden no estar disponibles.
- Las verificaciones de seguridad y restricciones de acceso pueden impedir la consulta.
- El descubrimiento de publicaciones utiliza desplazamiento vertical, no paginación.
- Chrome se abre en modo visible y no utiliza sesiones persistentes.

### Big Five

- Requiere contenido textual suficiente; el código exige al menos tres publicaciones con contenido.
- Las dimensiones pueden quedar sin puntuación.
- Los resultados dependen de los textos disponibles y de la respuesta del modelo.
- No constituye una evaluación psicométrica validada.
- No permite diagnosticar condiciones psicológicas ni determinar rasgos reales de personalidad.

### Análisis semántico

- Requiere al menos dos publicaciones con contenido textual.
- Compara textos, no imágenes, audio ni video directamente.
- Depende de la disponibilidad del modelo de embeddings y de la API de Gemini.
- La similitud vectorial no implica que dos publicaciones tengan exactamente el mismo significado.

## 8. Estado del proyecto

**Prototipo académico funcional en fase de pruebas.**

El proyecto integra extracción web, procesamiento de datos, visualización interactiva, análisis lingüístico asistido por inteligencia artificial y comparación semántica mediante embeddings.

Su finalidad es aplicar conocimientos de Ingeniería en Sistemas en una solución modular que conecta la adquisición, organización, análisis y presentación de información pública.