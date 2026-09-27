@echo off
setlocal
cd /d "%~dp0"
title Update Mizan AI Video Studio

:: Ensure Git is in PATH
set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;C:\Program Files\Git\cmd;%PATH%"

echo ========================================================
echo   Updating Mizan AI Video Studio from GitHub...
echo   Repository: https://github.com/telemy464-arch/Autovideomaking.git
echo ========================================================
echo.

where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [INFO] Git is not found in PATH.
    echo Please install Git from https://git-scm.com/
    goto CheckDeps
)

:: Ensure safe directory
git config --global --add safe.directory "%~dp0" >nul 2>nul
git config --global --add safe.directory "*" >nul 2>nul

echo [1/2] Fetching and syncing latest updates from GitHub...
git fetch origin main
if %ERRORLEVEL% equ 0 (
    git reset --hard origin/main
    echo [OK] Code updated to the latest version successfully!
) else (
    echo [WARNING] Git fetch encountered an issue. Checking direct pull...
    git pull origin main
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
