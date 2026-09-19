@echo off
cd /d "%~dp0"
title AI Video making By Mizan - v2.0.0

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_and_run.ps1"

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] An error occurred while launching the application.
    pause
)
