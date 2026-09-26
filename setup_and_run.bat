@echo off
cd /d "%~dp0"
title AI Video making By Mizan - v2.0.0

if exist "%~dp0runtime\python.exe" (
    set PYTHONIOENCODING=utf-8
    set PYTHONUTF8=1
    start http://localhost:8501
    "%~dp0runtime\python.exe" -m streamlit run "%~dp0app.py" --theme.base dark
    exit /b
)

if exist "%~dp0.venv\Scripts\python.exe" (
    set PYTHONIOENCODING=utf-8
    set PYTHONUTF8=1
    start http://localhost:8501
    "%~dp0.venv\Scripts\python.exe" -m streamlit run "%~dp0app.py" --theme.base dark
    exit /b
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_and_run.ps1"

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] An error occurred while launching the application.
    pause
)
