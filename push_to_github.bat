@echo off
chcp 65001 >nul
title Push Mizan AI Video Studio to GitHub
cd /d "%~dp0"

:: Ensure Git is in PATH
set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;C:\Program Files\Git\cmd;%PATH%"

echo ========================================================
echo    🎬 Mizan AI Video Studio - GitHub Sync & Push
echo    রিপোজিটরি: https://github.com/telemy464-arch/Autovideomaking.git
echo ========================================================
echo.

:: Check Git
where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ত্রুটি] Git পাওয়া যায়নি!
    echo দয়া করে run_app.bat চালান অথবা Git ইনস্টল করুন।
    echo.
    pause
    exit /b 1
)

:: Ensure safe directory
git config --global --add safe.directory "%~dp0" >nul 2>nul
git config --global --add safe.directory "*" >nul 2>nul

echo [১/৩] ফাইলের পরিবর্তন স্ক্যান ও অ্যাড করা হচ্ছে (git add)...
git add -A

:: Check if there are changes to commit
git diff --cached --quiet
if %ERRORLEVEL% neq 0 (
    echo [২/৩] নতুন পরিবর্তন সেভ করা হচ্ছে (git commit)...
    set "commit_msg="
    set /p "commit_msg=কমিট মেসেজ লিখুন (খালি রেখে Enter চাপলে ডিফল্ট মেসেজ হবে): "
    if not defined commit_msg (
        set "commit_msg=Update project files: %date% %time%"
    )
    git commit -m "%commit_msg%"
) else (
    echo [২/৩] নতুন কোনো লোকাল পরিবর্তন নেই (Already committed)।
)

echo.
echo [৩/৩] গিটহাবে আপলোড করা হচ্ছে (git push)...
git push -u origin main

echo.
if %ERRORLEVEL% equ 0 (
    echo ========================================================
    echo  ✔️ SUCCESS! সফলভাবে গিটহাবে আপলোড সম্পন্ন হয়েছে!
    echo ========================================================
) else (
    echo ========================================================
    echo  ❌ আপলোড সম্পন্ন করা যায়নি!
    echo ========================================================
    echo সম্ভাব্য কারণ ও সমাধান:
    echo 1. GitHub লগইন / Token সমস্যা:
    echo    - GitHub পাসওয়ার্ডের বদলে Personal Access Token (PAT) ব্যবহার করতে হবে।
    echo    - অথবা নিচের কমান্ড দিয়ে টোকেন সেট করতে পারেন:
    echo      git remote set-url origin https://<YOUR_TOKEN>@github.com/telemy464-arch/Autovideomaking.git
    echo.
    echo 2. ইন্টারনেটে সমস্যা বা রিমোটে নতুন কোড থাকলে:
    echo    - আগে update_app.bat চালিয়ে 'git pull' করে নিন।
    echo ========================================================
)

echo.
pause
