@echo off
REM Script para activar un entorno virtual y ejecutar un script de Python usando rutas relativas.

REM --- CONFIGURACIÓN ---
REM Cambia "venv" por el nombre real de la carpeta de tu entorno virtual si es diferente.
set VENV_FOLDER_NAME=venv

REM --- EJECUCIÓN ---
REM Construye la ruta completa al script de activación del entorno virtual.
REM %~dp0 se expande a la ruta de la carpeta donde está este archivo .bat
set VENV_ACTIVATE_SCRIPT="%~dp0%VENV_FOLDER_NAME%\Scripts\activate.bat"

REM Verifica si el script de activación existe antes de intentar llamarlo.
if not exist %VENV_ACTIVATE_SCRIPT% (
    echo.
    echo ERROR: No se encuentra el script de activacion del entorno virtual.
    echo Se esperaba en: %VENV_ACTIVATE_SCRIPT%
    echo.
    echo Asegurate de que:
    echo  1. La carpeta del entorno virtual se llama '%VENV_FOLDER_NAME%'. Si no, modifica esta variable en el script.
    echo  2. Este archivo .bat esta en la carpeta raiz de tu proyecto.
    echo.
    pause
    exit /b
)

REM Activa el entorno virtual. 'call' es crucial para que el control vuelva a este script.
call %VENV_ACTIVATE_SCRIPT%

echo.
echo Entorno virtual activado.
echo Ejecutando menu.py...
echo.

REM Ejecuta tu script de Python. El sistema esperará a que se cierre para continuar.
python menu.py

echo.
echo La ejecucion de menu.py ha finalizado.

REM Sale de la ventana de comandos.
exit