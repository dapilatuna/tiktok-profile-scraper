#  TikTok Profile Scraper

**Aplicación web para la extracción, procesamiento, visualización y exportación de información pública de perfiles de TikTok.**

Proyecto académico desarrollado en Python que permite consultar perfiles públicos de TikTok y recopilar información de sus publicaciones recientes, estadísticas de interacción y comentarios disponibles, mediante automatización de navegador y procesamiento de datos.

## Descripción del proyecto

TikTok Profile Scraper es una aplicación que integra la extracción de datos web con una interfaz interactiva para presentar información estructurada de cuentas públicas de TikTok.

El sistema permite consultar un perfil a partir de su nombre de usuario, recuperar sus datos generales, identificar publicaciones recientes y obtener sus estadísticas de interacción. También incorpora la recopilación de comentarios y respuestas cuando la plataforma permite acceder a esta información.

Los resultados se presentan en una aplicación desarrollada con Streamlit y pueden exportarse en formato JSON.

## Funcionalidades

### Información del perfil

- Nombre de usuario y nombre público.
- Biografía.
- Número de seguidores y cuentas seguidas.
- Cantidad de me gusta acumulados.
- Número de publicaciones.
- Estado de verificación y privacidad.
- Enlace al perfil consultado.

### Extracción de publicaciones

- Identificación de publicaciones del perfil.
- Selección de hasta diez videos recientes entre los detectados.
- Identificador y enlace de cada video.
- Descripción y fecha de publicación.
- Visualizaciones, me gusta, comentarios, compartidos y guardados.
- Duración, música y artista.
- Hashtags disponibles.

### Comentarios e interacciones

- Recuperación del texto de comentarios disponibles.
- Identificación del autor de cada comentario.
- Fecha de publicación y cantidad de me gusta.
- Procesamiento de respuestas cuando están incluidas en los datos recibidos.
- Asociación de cada comentario con su publicación correspondiente.

### Visualización y exportación

- Interfaz web desarrollada con Streamlit.
- Presentación organizada de perfiles y publicaciones.
- Indicadores de interacción.
- Visualización tabular de comentarios recuperados.
- Consulta de datos estructurados.
- Exportación de resultados en formato JSON.

## Tecnologías utilizadas

| Tecnología | Aplicación en el proyecto |
|---|---|
| **Python** | Lenguaje principal de desarrollo y procesamiento de datos. |
| **Streamlit** | Construcción de la interfaz web interactiva. |
| **Playwright** | Automatización de Chrome y observación de las respuestas de red. |
| **Google Chrome** | Navegador utilizado para consultar el contenido web. |
| **JSON** | Interpretación, estructuración e intercambio de datos. |
| **CSS** | Personalización de la apariencia visual de la aplicación. |
| **Git** | Control de versiones del código fuente. |
| **GitHub** | Almacenamiento y gestión del repositorio. |

## Estructura del proyecto

**`backend/` — Lógica de extracción y procesamiento**

- `validator.py`: validación del nombre de usuario ingresado.
- `profile_extractor.py`: extracción de información del perfil público.
- `video_extractor.py`: identificación, selección y procesamiento de publicaciones.
- `video_content_extractor.py`: procesamiento de información de videos, comentarios y respuestas.

**`frontend/` — Interfaz de usuario**

- `app.py`: aplicación principal desarrollada con Streamlit.
- `styles.css`: estilos personalizados de la interfaz.

**Otros elementos**

- `data/`: directorio para archivos y datos locales utilizados durante la ejecución.
- `requirements.txt`: dependencias de Python.
- `.gitignore`: exclusión de archivos temporales, entornos virtuales y datos de sesión.
- `README.md`: documentación del proyecto.

## Requisitos

Antes de ejecutar la aplicación, se necesita:

- Python 3.10 o superior.
- Google Chrome instalado.
- Git, si se desea clonar y gestionar el repositorio.
- Acceso a Internet.
- Las dependencias indicadas en `requirements.txt`.

## Instalación y ejecución

Los siguientes pasos están orientados a Windows con PowerShell.

**1. Obtener el proyecto**

Clonar el repositorio desde GitHub o descargar su código fuente y abrir la carpeta `tiktok-profile-scraper`.

**2. Crear un entorno virtual**

Ejecutar:

`python -m venv .venv-scraper`

**3. Activar el entorno virtual**

Ejecutar:

`.\.venv-scraper\Scripts\Activate.ps1`

**4. Instalar las dependencias**

Ejecutar:

`python -m pip install -r requirements.txt`

**5. Iniciar la aplicación**

Ejecutar:

`streamlit run frontend/app.py`

La aplicación estará disponible normalmente en:

`http://localhost:8501`

## Funcionamiento del sistema

1. El usuario ingresa el nombre de una cuenta pública de TikTok.
2. El sistema valida el identificador y consulta la información del perfil.
3. Playwright abre Google Chrome y observa las respuestas generadas durante la navegación.
4. La aplicación identifica las publicaciones disponibles y procesa sus metadatos.
5. Se seleccionan hasta diez publicaciones recientes según sus fechas.
6. Se intenta recuperar los comentarios disponibles utilizando el contexto de navegación.
7. La información obtenida se organiza y presenta en Streamlit.
8. El usuario puede revisar y exportar los resultados en formato JSON.

## Gestión de sesiones

La aplicación utiliza un contexto persistente de Chrome mediante Playwright para conservar cookies y datos de navegación entre ejecuciones.

Estos datos se almacenan localmente en `data/chrome_session/` y se excluyen del control de versiones mediante `.gitignore`.

Las cookies y los datos de sesión no deben compartirse ni publicarse en el repositorio.

## Limitaciones y consideraciones

- El sistema está orientado a consultar información de perfiles públicos.
- La disponibilidad de datos depende de las respuestas proporcionadas por TikTok.
- La plataforma puede solicitar verificaciones de seguridad o restringir determinadas consultas.
- Mantener cookies persistentes no garantiza evitar estas verificaciones.
- No siempre es posible recuperar todos los comentarios o respuestas de una publicación.
- Las estadísticas representan los valores disponibles en el momento de la extracción.
- La identificación de las publicaciones más recientes depende de los registros que hayan podido recuperarse.
- El sistema no utiliza la API oficial de TikTok.

## Estado del desarrollo

**Versión académica funcional, en fase de pruebas y validación.**

Se ha verificado la recuperación de información de perfiles, publicaciones, estadísticas y comentarios disponibles mediante consultas reales.

Como mejoras futuras se contempla ampliar las pruebas de comentarios y respuestas, fortalecer el manejo de restricciones de acceso y continuar incorporando verificaciones para evaluar la consistencia de los resultados.

## Finalidad académica

Este proyecto fue desarrollado con fines de aprendizaje y aplicación práctica de conceptos de programación, automatización web, procesamiento de datos, integración de componentes e interfaces de usuario.

Su desarrollo busca fortalecer competencias relacionadas con el diseño e implementación de soluciones informáticas, la organización de datos y la validación de resultados.

El uso de la aplicación debe respetar la privacidad de los usuarios y las condiciones aplicables al acceso a la información de la plataforma.