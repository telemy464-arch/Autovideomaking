@echo off
chcp 65001 >nul
title Update Mizan AI Video Studio
cd /d "%~dp0"

echo ========================================================
echo        ?? Mizan AI Video Studio - Update Manager
echo ========================================================
echo.
echo [1/2] Checking for latest updates from GitHub...
git pull origin main

if %ERRORLEVEL% equ 0 (
    echo.
    echo [2/2] Checking dependencies...
    if exist ".venv\Scripts\pip.exe" (
        .\.venv\Scripts\pip.exe install -r requirements.txt --quiet
    )
    echo.
    echo ========================================================
    echo ? SUCCESS: App is now completely updated to the latest version!
    echo ========================================================
) else (
    echo.
    echo ?? Could not fetch update. Please check your internet connection.
)

echo.
pause
