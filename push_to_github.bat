@echo off
title Push Mizan AI Video Studio to GitHub
cd /d "%~dp0"
echo ========================================================
echo Pushing Mizan AI Video Studio to GitHub:
echo https://github.com/telemy464-arch/Autovideomaking.git
echo ========================================================
echo.
git push -u origin main
echo.
if %ERRORLEVEL% equ 0 (
    echo ========================================================
    echo SUCCESS! Project successfully uploaded to GitHub!
    echo ========================================================
) else (
    echo ========================================================
    echo Notice: If login failed, you can use a GitHub Token.
    echo ========================================================
)
pause
