@echo off
setlocal
cd /d "%~dp0"
title Push Mizan AI Video Studio to GitHub

set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;C:\Program Files\Git\cmd;%PATH%"

echo ========================================================
echo    Mizan AI Video Studio - GitHub Sync and Push
echo    Repository: https://github.com/telemy464-arch/Autovideomaking.git
echo ========================================================
echo.

where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Git is not installed or not in PATH!
    echo Please install Git from https://git-scm.com/
    pause
    exit /b 1
)

git config --global --add safe.directory "%~dp0" >nul 2>nul
git config --global --add safe.directory "*" >nul 2>nul

echo [1/3] Staging changes...
git add -A

git diff --cached --quiet
if %ERRORLEVEL% equ 0 goto NoChanges

echo [2/3] Saving changes to Git...
set "commit_msg="
set /p "commit_msg=Enter commit message or press Enter for default: "
if not defined commit_msg set "commit_msg=Update project files: %date% %time%"
git commit -m "%commit_msg%"
goto DoPush

:NoChanges
echo [2/3] No new local changes to commit.

:DoPush
echo.
echo [3/3] Uploading to GitHub...
git push -u origin main

if %ERRORLEVEL% equ 0 (
    echo.
    echo ========================================================
    echo  SUCCESS: Successfully pushed to GitHub!
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo  FAILED: Could not push to GitHub.
    echo ========================================================
    echo 1. Check your Internet connection.
    echo 2. If there are remote changes, run update_app.bat first.
    echo 3. Check your GitHub authentication.
    echo ========================================================
)

echo.
pause
