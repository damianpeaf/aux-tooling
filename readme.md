# PlagCheck

## Descripción

PlagCheck es una herramienta automatizada para extraer enlaces de repositorios desde archivos HTML, analizar y filtrar dichos enlaces, clonar los repositorios y filtrar archivos específicos en función de extensiones permitidas. También incluye integración con JPlag para la detección de similitudes en código.

## Características principales

- Extracción automática de enlaces desde archivos HTML.
- Identificación del nombre y carnet desde los enlaces.
- Clonación de repositorios con múltiples métodos de recuperación.
- Eliminación de archivos innecesarios según extensiones configurables.
- Generación de reportes de repositorios fallidos.
- Integración con JPlag para detección de similitudes en código.

## Requerimientos

- Python 3.8+
- Git
- Java instalado (para ejecutar JPlag)
- Librerías de Python necesarias (pueden instalarse con `pip install -r requirements.txt`):
  - `beautifulsoup4`
  - `questionary`

## Instalación

1. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Asegurar que `git` y `java` estén instalados y accesibles desde la terminal.

## Uso

1. Coloca los archivos HTML dentro de la carpeta `./entregas`.
2. Ejecuta el script principal:
   ```bash
   python index.py
   ```
3. Responde las preguntas interactivas sobre las extensiones de archivos permitidos.
4. Los resultados se guardarán en:
   - `links.csv`: Contiene la lista de repositorios detectados.
   - `repos/`: Carpeta donde se almacenan los repositorios clonados.
   - `failed_repos.txt`: Reporte de los repositorios que fallaron en la clonación.
   - `resultados.zip`: Salida del análisis de JPlag.

## Personalización

Puedes modificar las siguientes partes del código para adaptarlo a diferentes necesidades:

- **Extensiones permitidas**: Cambiar `default_extensions` en `main()` para filtrar otros tipos de archivos.
- **Expresión regular para carnet**: Ajustar `extract_carnet_from_link()` si el formato de los enlaces cambia.
- **Métodos de clonación**: Mejorar la estrategia en `clone_repo()` si se requieren métodos alternativos.
- **Parámetros de JPlag**: Modificar la línea de ejecución en `main()` si se usa otro lenguaje o configuración.

## Notas

- La herramienta intenta varias estrategias para clonar repositorios, pero si todos los intentos fallan, los detalles del error se almacenan en `failed_repos.txt`.
- Los repositorios clonados se almacenan en `repos/`, y se eliminan archivos no deseados automáticamente.
- Si se detectan archivos autogenerados, estos también se eliminan para evitar ruido en el análisis.
