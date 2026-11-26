@echo off
setlocal
title Stem Splitter - Installer
cd /d "%~dp0"

echo   Installer
echo.

REM ---------- 1) Check Python ----------
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found.
    echo Install Python 3.9 - 3.12 from https://www.python.org/downloads/
    echo IMPORTANT: tick "Add python.exe to PATH" during setup, then run this file again.
    start "" "https://www.python.org/downloads/"
    pause
    exit /b 1
)
for /f "delims=" %%v in ('python --version') do echo Found %%v
echo.

REM ---------- 2) Choose PyTorch version ----------
echo Which PyTorch version do you want?
echo   [1] CPU only (works everywhere, slower)
echo   [2] NVIDIA GPU / CUDA (much faster, needs an NVIDIA graphics card)
echo.
choice /c 12 /n /m "Press 1 or 2: "
if errorlevel 2 goto gpu
goto cpu

:cpu
set "TORCH_CMD=python -m pip install torch~=2.8.0 torchaudio~=2.8.0"
goto install

:gpu
set "TORCH_CMD=python -m pip install torch~=2.8.0 torchaudio~=2.8.0 --index-url https://download.pytorch.org/whl/cu126"
goto install

:install
echo.
echo [1/4] Updating pip...
python -m pip install --upgrade pip
if errorlevel 1 goto fail

echo.
echo [2/4] Installing PyTorch (this is a big download, please wait)...
%TORCH_CMD%
if errorlevel 1 goto fail

echo.
echo [3/4] Installing the other libraries...
python -m pip install demucs soundfile scipy numpy librosa pretty_midi customtkinter
if errorlevel 1 goto fail

REM ---------- 3) FFmpeg ----------
echo.
echo [4/4] Checking FFmpeg (needed to read mp3 files)...
where ffmpeg >nul 2>nul
if not errorlevel 1 (
    echo FFmpeg already installed.
    goto done
)
where winget >nul 2>nul
if errorlevel 1 (
    echo [WARNING] FFmpeg not found and winget is not available.
    echo Install FFmpeg manually from https://ffmpeg.org/download.html and add it to PATH.
    goto done
)
echo Installing FFmpeg with winget...
winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
if errorlevel 1 (
    echo [WARNING] FFmpeg install failed. Install it manually from https://ffmpeg.org/download.html
) else (
    echo FFmpeg installed. If mp3 files do not load, restart your PC once.
)

:done
echo.
echo   Installation complete!
echo Start the app by double-clicking "Stem Splitter.vbs"
echo.
choice /c YN /n /m "Launch the app now? (Y/N): "
if errorlevel 2 goto end
start "" wscript.exe "%~dp0Stem Splitter.vbs"
goto end

:fail
echo.
echo [ERROR] Installation failed. Check your internet connection and try again.
pause
exit /b 1

:end
endlocal
