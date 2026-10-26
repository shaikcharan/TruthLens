@echo off
cd /d "%~dp0\.."
echo ==============================================================================
echo                   TruthLens -- Push to GitHub
echo ==============================================================================
echo Remote URL: https://github.com/shaikcharan/TruthLens.git
echo Branch:     main
echo.
echo 1. Verify you created the repository at: https://github.com/new
echo    Repository name: TruthLens
echo 2. Press any key to push your code...
echo ==============================================================================
pause
git push -u origin main
echo.
if %errorlevel% equ 0 (
    echo [OK] Code successfully pushed to GitHub!
    echo Next step: Go to https://vercel.com/ and import this repository.
) else (
    echo [FAIL] Git push failed. Verify your GitHub login or remote URL.
)
echo.
pause
