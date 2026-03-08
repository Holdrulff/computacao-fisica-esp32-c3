@echo off
REM ESP32 Deploy Script - Windows Batch Version
REM Uso: deploy.bat [PORT]

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"

echo ===================================
echo ESP32 Deployment Script
echo ===================================
echo.

REM Check if venv exists
if not exist "%VENV_DIR%" (
    echo Warning: Virtual environment not found at: %VENV_DIR%
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
    echo Virtual environment created
    echo.
)

REM Activate venv
echo Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

REM Check if mpremote is installed
where mpremote >nul 2>nul
if errorlevel 1 (
    echo Warning: mpremote not found. Installing...
    pip install mpremote
    echo mpremote installed
    echo.
)

REM Run deployment script
echo Starting deployment...
echo.

if "%~1"=="" (
    python "%SCRIPT_DIR%deploy.py"
) else (
    python "%SCRIPT_DIR%deploy.py" %1
)

echo.
echo Virtual environment is still active.
echo You can run manual mpremote commands or type 'deactivate' to exit.
echo.

cmd /k
