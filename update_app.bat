@echo off
setlocal
cd /d "%~dp0"
title Update Mizan AI Video Studio

echo ========================================================
echo   Updating Mizan AI Video Studio from GitHub...
echo ========================================================
echo.

where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [INFO] Git is not found in PATH.
    echo Please install Git from https://git-scm.com/
    goto CheckDeps
)

echo [1/2] Fetching latest updates from GitHub...
git pull origin main
if %ERRORLEVEL% equ 0 (
    echo [OK] Code updated successfully!
) else (
    echo [WARNING] Git pull encountered an issue. Check connection or conflicts.
)

:CheckDeps
echo.
echo [2/2] Checking dependencies...
if exist "%~dp0runtime\python.exe" (
    "%~dp0runtime\python.exe" -m pip install -r "%~dp0requirements.txt" --quiet --no-warn-script-location
) else if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt" --quiet
)

echo.
echo ========================================================
echo   Update completed! Launching application...
echo ========================================================
ping 127.0.0.1 -n 3 >nul
if exist "%~dp0MizanAIStudio.exe" (
    start "" "%~dp0MizanAIStudio.exe"
) else (
    start "" "%~dp0run_app.bat"
)
exit
