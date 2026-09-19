[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path $RootDir

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   🎬 AI Video making By Mizan - Auto Setup & Launcher" -ForegroundColor Yellow
Write-Host "   স্বয়ংক্রিয় বাংলা ভিডিও তৈরির স্বয়ংসম্পূর্ণ ইঞ্জিন" -ForegroundColor White
Write-Host "                   তৈরি করেছেন: Mizan" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# ----------------------------------------------------
# 1. Check / Create .env
# ----------------------------------------------------
if (-not (Test-Path "$RootDir\.env")) {
    if (Test-Path "$RootDir\.env.example") {
        Write-Host "[1/5] 📄 .env কনফিগারেশন ফাইল তৈরি করা হচ্ছে (.env.example থেকে)..." -ForegroundColor Gray
        Copy-Item "$RootDir\.env.example" "$RootDir\.env"
    }
} else {
    Write-Host "[1/5] ✔️ .env কনফিগারেশন ফাইল পাওয়া গেছে।" -ForegroundColor Green
}

# ----------------------------------------------------
# 2. Check / Setup Python
# ----------------------------------------------------
Write-Host "[2/5] 🔍 পাইথন (Python) যাচাই করা হচ্ছে..." -ForegroundColor Gray

function Test-PythonUsable($pyPath) {
    if (-not $pyPath) { return $false }
    try {
        $res = & $pyPath -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($res -and [float]$res -ge 3.10) {
            return $true
        }
    } catch {}
    return $false
}

function Find-Python {
    # Check PATH first
    foreach ($name in @("python", "py")) {
        if (Get-Command $name -ErrorAction SilentlyContinue) {
            if (Test-PythonUsable $name) {
                return (Get-Command $name).Source
            }
        }
    }
    
    # Check common user & system install paths
    $paths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "C:\Program Files\Python311\python.exe",
        "C:\Program Files\Python312\python.exe",
        "C:\Program Files\Python310\python.exe"
    )
    foreach ($p in $paths) {
        if ((Test-Path $p) -and (Test-PythonUsable $p)) {
            return $p
        }
    }
    return $null
}

$PythonExe = Find-Python

if (-not $PythonExe) {
    Write-Host "   ⚠️ পাইথন পাওয়া যায়নি! স্বয়ংক্রিয়ভাবে ডাউনলোড ও ইনস্টল করা হচ্ছে..." -ForegroundColor Yellow
    $installerUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    $tempInstaller = "$env:TEMP\python-3.11.9-amd64.exe"
    
    Write-Host "   📥 Python 3.11.9 ইনস্টলার ডাউনলোড হচ্ছে (আনুমানিক ২৫ MB)..." -ForegroundColor Cyan
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $installerUrl -OutFile $tempInstaller -UseBasicParsing
    } catch {
        Write-Host "   ⚠️ curl দিয়ে পুনরায় চেষ্টা করা হচ্ছে..." -ForegroundColor Yellow
        & curl.exe -L -o $tempInstaller $installerUrl
    }
    
    Write-Host "   ⚙️ পাইথন ব্যাকগ্রাউন্ডে ইনস্টল হচ্ছে (কোনো অ্যাডমিন পাসওয়ার্ড লাগবে না)..." -ForegroundColor Cyan
    $proc = Start-Process -FilePath $tempInstaller -ArgumentList "/quiet InstallAllUsers=0 InstallLauncherAllUsers=0 Include_launcher=0 PrependPath=1" -Wait -PassThru
    
    # Add newly installed python paths to current process environment
    $pyUserBase = "$env:LOCALAPPDATA\Programs\Python\Python311"
    $pyUserScripts = "$pyUserBase\Scripts"
    $env:PATH = "$pyUserBase;$pyUserScripts;" + $env:PATH
    
    $PythonExe = Find-Python
    if (-not $PythonExe) {
        Write-Host "   ❌ পাইথন ইনস্টলেশন সম্পূর্ণ হয়নি। দয়া করে python.org থেকে Python 3.11 ইনস্টল করুন।" -ForegroundColor Red
        Read-Host "প্রস্থান করতে Enter চাপুন..."
        exit 1
    }
    Write-Host "   ✔️ পাইথন সফলভাবে ইনস্টল ও কনফিগার হয়েছে!" -ForegroundColor Green
} else {
    Write-Host "   ✔️ উপযুক্ত পাইথন পাওয়া গেছে: $PythonExe" -ForegroundColor Green
}

# ----------------------------------------------------
# 3. Check / Setup FFmpeg
# ----------------------------------------------------
Write-Host "[3/5] 🎬 FFmpeg মিডিয়া ইঞ্জিন যাচাই করা হচ্ছে..." -ForegroundColor Gray
$BinDir = "$RootDir\bin"
if (-not (Test-Path $BinDir)) {
    New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
}
$FfmpegExe = "$BinDir\ffmpeg.exe"
$FfprobeExe = "$BinDir\ffprobe.exe"

$hasFfmpeg = $false
if ((Test-Path $FfmpegExe) -and (Test-Path $FfprobeExe)) {
    $hasFfmpeg = $true
} else {
    if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
        $hasFfmpeg = $true
    }
}

if (-not $hasFfmpeg) {
    Write-Host "   ⚠️ FFmpeg পাওয়া যায়নি! স্বয়ংক্রিয়ভাবে ডাউনলোড হচ্ছে..." -ForegroundColor Yellow
    $ffmpegZip = "$env:TEMP\ffmpeg-release-essentials.zip"
    $ffmpegExtract = "$env:TEMP\ffmpeg_temp_extract"
    $ffmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    
    Write-Host "   📥 FFmpeg প্যাকেজ ডাউনলোড হচ্ছে (কিছুক্ষণ অপেক্ষা করুন)..." -ForegroundColor Cyan
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $ffmpegUrl -OutFile $ffmpegZip -UseBasicParsing
    } catch {
        Write-Host "   ⚠️ curl দিয়ে ডাউনলোড করা হচ্ছে..." -ForegroundColor Yellow
        & curl.exe -L -o $ffmpegZip $ffmpegUrl
    }
    
    Write-Host "   📦 FFmpeg আনপ্যাক করা হচ্ছে..." -ForegroundColor Cyan
    if (Test-Path $ffmpegExtract) { Remove-Item -Recurse -Force $ffmpegExtract -ErrorAction SilentlyContinue }
    Expand-Archive -Path $ffmpegZip -DestinationPath $ffmpegExtract -Force
    
    $foundFfmpeg = Get-ChildItem -Path $ffmpegExtract -Filter "ffmpeg.exe" -Recurse | Select-Object -First 1
    $foundFfprobe = Get-ChildItem -Path $ffmpegExtract -Filter "ffprobe.exe" -Recurse | Select-Object -First 1
    
    if ($foundFfmpeg -and $foundFfprobe) {
        Copy-Item $foundFfmpeg.FullName $FfmpegExe -Force
        Copy-Item $foundFfprobe.FullName $FfprobeExe -Force
        Write-Host "   ✔️ FFmpeg সফলভাবে সেটআপ করা হয়েছে!" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️ FFmpeg সরাসরি পাওয়া যায়নি।" -ForegroundColor Yellow
    }
    
    Remove-Item -Force $ffmpegZip -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force $ffmpegExtract -ErrorAction SilentlyContinue
} else {
    Write-Host "   ✔️ FFmpeg পাওয়া গেছে ও প্রস্তুত আছে।" -ForegroundColor Green
}

# Ensure bin is in current environment PATH
if (Test-Path $BinDir) {
    $env:PATH = "$BinDir;" + $env:PATH
}

# ----------------------------------------------------
# 4. Check / Rebuild Virtual Environment (.venv)
# ----------------------------------------------------
Write-Host "[4/5] 📦 ভার্চুয়াল এনভায়রনমেন্ট ও প্যাকেজ যাচাই করা হচ্ছে..." -ForegroundColor Gray
$VenvPython = "$RootDir\.venv\Scripts\python.exe"
$VenvPip = "$RootDir\.venv\Scripts\pip.exe"
$VenvStreamlit = "$RootDir\.venv\Scripts\streamlit.exe"

$isVenvValid = $false
if (Test-Path $VenvPython) {
    try {
        $testRes = & $VenvPython -c "import sys; print('ok')" 2>$null
        if ($testRes -match "ok") {
            $isVenvValid = $true
        }
    } catch {}
}

if (-not $isVenvValid) {
    Write-Host "   ⚠️ ভার্চুয়াল এনভায়রনমেন্ট অনুপস্থিত বা ক্ষতিগ্রস্ত। নতুন করে প্রস্তুত করা হচ্ছে (.venv)..." -ForegroundColor Yellow
    if (Test-Path "$RootDir\.venv") {
        Remove-Item -Recurse -Force "$RootDir\.venv" -ErrorAction SilentlyContinue
    }
    & $PythonExe -m venv "$RootDir\.venv"
    Write-Host "   📥 প্রয়োজনীয় প্যাকেজ ইনস্টল করা হচ্ছে (requirements.txt)..." -ForegroundColor Cyan
    & $VenvPython -m pip install --upgrade pip --quiet
    & $VenvPip install -r "$RootDir\requirements.txt"
    Write-Host "   ✔️ সকল ডিপেন্ডেন্সি সফলভাবে ইনস্টল হয়েছে!" -ForegroundColor Green
} else {
    # Check if streamlit is working in venv
    $stCheck = $false
    try {
        $stRes = & $VenvPython -c "import streamlit; print('ok')" 2>$null
        if ($stRes -match "ok") {
            $stCheck = $true
        }
    } catch {}
    
    if (-not $stCheck) {
        Write-Host "   📥 ডিপেন্ডেন্সি আপডেট/ইনস্টল করা হচ্ছে..." -ForegroundColor Cyan
        & $VenvPip install -r "$RootDir\requirements.txt"
    }
    Write-Host "   ✔️ ভার্চুয়াল এনভায়রনমেন্ট সক্রিয় ও প্রস্তুত।" -ForegroundColor Green
}

# ----------------------------------------------------
# 5. Launch App
# ----------------------------------------------------
Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "   🚀 AI Video Studio চালু হচ্ছে... ব্রাউজার ওপেন হবে।" -ForegroundColor White
Write-Host "   URL: http://localhost:8501" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""

Start-Process "http://localhost:8501"
& $VenvStreamlit run "$RootDir\app.py"
