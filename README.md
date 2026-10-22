# TikTok Profile Scraper

Aplicación web desarrollada en **Python y Streamlit** para extraer, procesar, visualizar y exportar información pública de perfiles de TikTok.

## 1. Descripción

El sistema permite consultar un perfil público de TikTok mediante su nombre de usuario y obtener información general, publicaciones recientes, estadísticas de interacción y comentarios disponibles.

La extracción se realiza con **Playwright y Google Chrome**, mediante la lectura de elementos del DOM y datos JSON incrustados en el HTML, **sin utilizar APIs**.

## 2. Funcionalidades

**Información del perfil**
- Nombre de usuario, nombre público y biografía.
- Seguidores, seguidos, me gusta y número de publicaciones.
- Estado de verificación y privacidad.

**Publicaciones**
- Identificación de videos mediante sus enlaces HTML.
- Detección de publicaciones fijadas.
- Selección de hasta 10 publicaciones recientes según las fechas disponibles.
- Extracción de descripción, fecha, visualizaciones, me gusta, comentarios, compartidos, guardados, duración, música y hashtags.

**Comentarios**
- Recuperación de comentarios y respuestas visibles.
- Extracción del texto, autor, fecha y me gusta cuando están disponibles.
- Desplazamiento por los comentarios e intento de expansión de respuestas.

**Visualización y exportación**
- Consulta de perfiles mediante una interfaz Streamlit.
- Visualización de estadísticas y comentarios.
- Exportación de los resultados en formato JSON.

## 3. Tecnologías

| Tecnología | Función |
|---|---|
| Python | Lógica y procesamiento de datos |
| Playwright | Automatización del navegador y lectura del DOM |
| Google Chrome | Acceso al contenido de TikTok |
| Streamlit | Interfaz web |
| HTML y JSON | Fuentes de información de la página |
| CSS | Diseño visual |
| Git y GitHub | Control de versiones |

## 4. Estructura del proyecto

```text
tiktok-profile-scraper/
├── backend/
│   ├── extractors/
│   │   ├── profile_extractor.py
│   │   ├── video_extractor.py
│   │   ├── metadata_extractor.py
│   │   └── comment_extractor.py
│   ├── parsers/
│   │   ├── html_parser.py
│   │   ├── json_parser.py
│   │   └── metric_parser.py
│   ├── models/
│   │   └── schemas.py
│   ├── browser_manager.py
│   ├── scraper.py
│   └── validator.py
├── frontend/
│   ├── components/
│   ├── pages/
│   ├── services/
│   ├── styles/
│   ├── utils/
│   ├── app.py
│   └── styles.css
├── data/
├── tests/
├── .gitignore
├── README.md
└── requirements.txt
```

**Backend:** contiene la validación, automatización de Chrome, extracción de perfiles, videos y comentarios, procesamiento de datos y coordinación de la consulta.

**Frontend:** contiene el formulario de búsqueda, componentes de visualización, presentación de resultados, estilos y exportación JSON.

## 5. Funcionamiento

1. El usuario ingresa el nombre de un perfil público.
2. El sistema valida el nombre y abre TikTok mediante Playwright y Chrome.
3. Extrae los datos del perfil desde el JSON incrustado en el HTML.
4. Identifica publicaciones mediante selectores del DOM y desplazamiento vertical.
5. Accede a las publicaciones para recuperar metadatos y comentarios disponibles.
6. Organiza y selecciona hasta 10 videos según la información de fechas obtenida.
7. Presenta los resultados en Streamlit y permite exportarlos en JSON.

## 6. Instalación y ejecución

**Requisitos:** Python 3.10 o superior, Google Chrome y conexión a Internet.

Clonar el repositorio:

```powershell
git clone https://github.com/dapilatuna/tiktok-profile-scraper.git
cd tiktok-profile-scraper
```

Crear y activar el entorno virtual:

```powershell
python -m venv .venv-scraper
.\.venv-scraper\Scripts\Activate.ps1
```

Instalar dependencias:

```powershell
python -m pip install -r requirements.txt
```

Ejecutar la aplicación:

```powershell
python -m streamlit run frontend/app.py
```

Abrir `http://localhost:8501` en el navegador.

## 7. Limitaciones

- La extracción depende de la información que TikTok muestre en el navegador.
- Los cambios en el HTML o las restricciones de acceso pueden afectar el funcionamiento.
- No siempre se recuperan todas las estadísticas, fechas, comentarios o respuestas.
- El sistema utiliza desplazamiento vertical para descubrir publicaciones; no implementa paginación.
- No utiliza APIs ni sesiones persistentes de Chrome.

## 8. Estado del proyecto

**Prototipo académico funcional en fase de pruebas.**

El proyecto implementa extracción web mediante automatización de navegador, procesamiento de datos, arquitectura modular e integración entre backend y frontend.

Su finalidad es aplicar conocimientos de Ingeniería en Sistemas mediante el desarrollo de una solución informática para consultar y estructurar información pública.
