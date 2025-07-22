# Generador de Cuadro de Columnas para ETABS

Esta herramienta de escritorio extrae datos de columnas de un modelo de ETABS, permitiendo a los ingenieros y dibujantes visualizar, agrupar y exportar cuadros de columnas a formatos de Excel y DXF de manera eficiente.

## Características Principales

-   **Conexión Directa con ETABS**: Se conecta a una instancia activa de ETABS para extraer en tiempo real la geometría de las columnas, niveles, materiales y datos de refuerzo.
-   **Visualización de Datos de Columnas**: Muestra todas las propiedades de las columnas extraídas en una tabla interactiva que permite ordenar y filtrar la información.
-   **Gestión de Ejes (Gridlines)**:
    -   Visualiza la ubicación de las columnas en una vista 2D renderizada con OpenGL.
    -   **Agrupa automáticamente** los ejes que son estructuralmente idénticos a través de todos los niveles, simplificando el cuadro de columnas.
    -   Permite la creación, modificación y asignación manual de grupos de ejes.
-   **Exportación a Excel**: Genera un "Cuadro de Columnas" formateado en un archivo `.xlsx`, respetando los grupos de ejes y los niveles para un resumen claro y conciso.
-   **Exportación a DXF**: Crea archivos `.dxf` con los detalles de las secciones transversales para cada tipo de columna única, incluyendo el armado de refuerzo.
-   **Diseñador de Secciones**: Incluye un visor de secciones 2D interactivo para diseñar y visualizar los detalles de refuerzo de columnas rectangulares.

---

## Cómo Ejecutar la Aplicación

### Prerrequisitos

-   **Python**: Se recomienda tener instalada una versión de Python 3.8 o superior.
-   **ETABS**: Se requiere una instancia de ETABS en ejecución con un modelo abierto.
-   **Dependencias**: Es necesario instalar los paquetes de Python listados en `requirements.txt`.

### Instalación

1.  **Clonar el repositorio**:
    ```bash
    git clone <URL_DE_TU_REPOSITORIO>
    cd <CARPETA_DEL_REPOSITORIO>
    ```

2.  **Crear un entorno virtual** (recomendado):
    ```bash
    python -m venv venv
    ```

3.  **Activar el entorno virtual**:
    -   **Windows**:
        ```bash
        .\venv\Scripts\activate
        ```
    -   **macOS/Linux**:
        ```bash
        source venv/bin/activate
        ```

4.  **Instalar las dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

### Ejecución de la Aplicación

Puedes ejecutar la aplicación usando el archivo `.bat` incluido o directamente desde la línea de comandos.

-   **Usando el archivo batch (Windows)**:
    Simplemente haz doble clic en el archivo **`app.bat`**. Este script activará el entorno virtual e iniciará la aplicación automáticamente.

-   **Usando Python (multiplataforma)**:
    Asegúrate de que tu entorno virtual esté activado y luego ejecuta:
    ```bash
    python menu.py
    ```

---

## Estructura del Proyecto


/
├── core/                 # Lógica principal para la conexión con ETABS y procesamiento de datos
│   ├── etabs.py          # Funciones para interactuar con la API de ETABS
│   └── export_excel.py   # Lógica para generar el cuadro de columnas en Excel
├── dxf_drawer/           # Módulos para la creación de archivos DXF
│   ├── column.py         # Define la clase para la columna rectangular
│   ├── detail.py         # Define un área de detalle para el dibujo
│   └── drawing.py        # Clase principal para la creación de los DXF
├── screens/              # Contiene todas las ventanas de la GUI (hechas con PyQt5)
│   ├── main_menu.py      # Ventana principal de la aplicación
│   ├── column_data.py    # Pantalla principal para ver y gestionar los datos de columnas
│   └── info_gridlines_2.py # Pantalla para la visualización y agrupamiento de ejes
├── utils/                # Scripts de utilidades
│   └── extractions.py    # Funciones de ayuda para la extracción de datos
├── app.bat               # Script para ejecutar la aplicación en Windows
├── menu.py               # Punto de entrada principal de la aplicación
└── requirements.txt      # Lista de dependencias de Python


---

## Dependencias

Las librerías clave utilizadas en este proyecto son:

-   **PyQt5**: Para la interfaz gráfica de usuario.
-   **pandas**: Para la manipulación y el análisis de datos.
-   **openpyxl**: Para la creación y edición de archivos de Excel (`.xlsx`).
-   **comtypes**: Para interactuar con la API COM de ETABS.
-   **ezdxf**: Para la creación de dibujos en formato DXF.
-   **PyOpenGL**: Para la visualización 2D de los ejes de las columnas.

La lista completa de dependencias se encuentra en el archivo `requirements.txt`.