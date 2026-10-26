@echo off
title TruthLens Setup Assistant
cd /d "%~dp0\.."

echo ==============================================================================
echo                      TruthLens Initial Environment Setup
echo ==============================================================================

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found in PATH!
    pause
    exit /b 1
)

echo [*] Initializing .venv virtual environment...
python -m venv .venv
if %errorlevel% neq 0 (
    echo [ERROR] Could not create .venv.
    pause
    exit /b 1
)

echo [*] Installing pinned dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Dependency installation encountered issues.
    pause
    exit /b 1
)

echo Dependencies installed successfully > ".venv\.installed_flag"

echo [*] Initializing database...
".venv\Scripts\python.exe" scripts\init_database.py

echo.
echo ==============================================================================
echo [OK] Setup completed successfully!
echo You can now launch TruthLens by running:
echo     RUN_TRUTHLENS.bat
echo or:
echo     .\.venv\Scripts\python.exe app.py
echo ==============================================================================
pause
