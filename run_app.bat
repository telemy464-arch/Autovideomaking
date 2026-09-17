@echo off
chcp 65001 >nul
title AI Video making By Mizan - v1.0.0
cd /d "%~dp0"

echo ========================================================
echo         🎬 AI Video making By Mizan - v1.0.0
echo   স্বয়ংক্রিয় বাংলা ভিডিও তৈরির সবচেয়ে সহজ উপায়
echo                   তৈরি করেছেন: Mizan
echo ========================================================
echo.

if not exist ".venv\Scripts\streamlit.exe" (
    echo [তথ্য] ভার্চুয়াল এনভায়রনমেন্ট প্রস্তুত করা হচ্ছে...
    python -m venv .venv
    echo [তথ্য] প্রয়োজনীয় প্যাকেজ ইনস্টল করা হচ্ছে...
    .\.venv\Scripts\pip install -r requirements.txt
)

echo [তথ্য] অ্যাপ চালু হচ্ছে... ব্রাউজারে শীঘ্রই প্রদর্শিত হবে।
echo.
start "" "http://localhost:8501"
.\.venv\Scripts\streamlit.exe run app.py

pause
