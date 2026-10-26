@echo off
setlocal enabledelayedexpansion

title TruthLens -- Multilingual News Analysis & Media Literacy Platform

:: 1. Change to project directory
cd /d "%~dp0"

echo ==============================================================================
echo                      TruthLens Launch Controller
echo ==============================================================================

:: 2. Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in your system PATH!
    echo         Please install Python 3.9+ from https://www.python.org/
    echo         Ensure "Add python.exe to PATH" is checked during installation.
    echo ==============================================================================
    pause
    exit /b 1
)

:: 3. Setup local virtual environment if missing
if not exist ".venv\Scripts\python.exe" (
    echo [*] Creating isolated virtual environment in .venv...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
)

:: 4. Check & Install dependencies if not already installed
if not exist ".venv\.installed_flag" (
    echo [*] Installing pinned dependencies from requirements.txt...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Dependency installation failed! Check network connection.
        pause
        exit /b 1
    )
    echo Dependencies installed successfully > ".venv\.installed_flag"
    echo [OK] Dependencies installed and verified.
) else (
    echo [OK] Pinned dependencies already verified.
)

:: 5. Create storage directory
if not exist "storage" (
    mkdir storage
)

:: 6. Initialize database
echo [*] Verifying database schema...
".venv\Scripts\python.exe" scripts\init_database.py
if %errorlevel% neq 0 (
    echo [ERROR] Database initialization failed.
    pause
    exit /b 1
)

:: 7. Check if port 8765 is in use
netstat -ano | findstr ":8765" | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo ==============================================================================
    echo Port 8765 is already in use. Close the existing TruthLens instance or select a different port in config.py.
    echo ==============================================================================
    pause
    exit /b 1
)

:: 8. Launch browser in background after short delay
echo [*] Starting TruthLens on http://127.0.0.1:8765 ...
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8765"

:: 9. Run TruthLens via Python in .venv
".venv\Scripts\python.exe" app.py

:: 10. Keep console open if stopped
echo.
echo ==============================================================================
echo TruthLens server has terminated.
echo ==============================================================================
pause
