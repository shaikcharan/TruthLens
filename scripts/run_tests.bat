@echo off
title TruthLens Test Suite Runner
cd /d "%~dp0\.."

echo ==============================================================================
echo                     TruthLens Automated Test Suite
echo ==============================================================================

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m pytest -q
) else (
    python -m pytest -q
)

echo.
echo ==============================================================================
pause
