# Aux Tools

Herramienta para descargar y filtrar entregas (repositorios) de estudiantes desde UEDI.

## Instalación

Antes de ejecutar la herramienta, es necesario configurar un entorno virtual de Python y asegurarse de que todas las dependencias estén instaladas.

### 1. Crear y activar un entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

## Uso de la herramienta

### 1. Descargar las entregas

Las entregas deben descargarse desde UEDI y colocarse en la carpeta `entregas/`. Cada entrega es un archivo HTML que contiene enlaces a los repositorios de los estudiantes.

### 2. Ejecutar la herramienta

Para procesar las entregas y clonar los repositorios, ejecutar el siguiente comando:

```bash
python index.py
```

Este proceso:

- Extraerá los enlaces de los repositorios desde los archivos HTML en `entregas/`.
- Generará un archivo `repositorios.csv` con la información de los estudiantes.
- Clonará los repositorios en la carpeta `repos/`.
- Filtrará los archivos descargados dejando solo los que tienen extensiones permitidas.
- Generará un reporte de errores si algunos repositorios no pudieron ser clonados.

### 3. Revisar resultados

- Los repositorios clonados estarán en la carpeta `repos/`.
- En caso de errores, se generará un archivo de reporte con detalles sobre los repositorios que no se pudieron clonar.

## Notas adicionales

- Si la clonación de un repositorio falla, el sistema intentará varios métodos alternativos.
- Eliminar y recrear la carpeta `repos/` en cada ejecución garantiza que siempre se descarguen versiones actualizadas.
- Si un archivo `repositorios.csv` está en uso, se intentará guardar con un nombre alternativo.
