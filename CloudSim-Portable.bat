@echo off
REM CloudSim - TRUE Standalone Launcher
REM No Python installation required!
title CloudSim

echo ======================================================================
echo   CloudSim - Cloud Infrastructure Simulator v1.0
echo   Loading...
echo ======================================================================
echo.

REM Get script directory
set "CLOUDSIM_ROOT=%~dp0"
cd /d "%CLOUDSIM_ROOT%"

REM Check if portable Python exists
if not exist "python-embed\python.exe" (
    echo.
    echo ======================================================================
    echo   FIRST TIME SETUP REQUIRED
    echo ======================================================================
    echo.
    echo This is your first time running CloudSim!
    echo.
    echo CloudSim requires Python to run, but don't worry - we'll handle it.
    echo.
    echo OPTION 1 - Use Your Python ^(Recommended if you have Python^):
    echo   - You already have Python installed
    echo   - Just need to install dependencies once
    echo   - Run: SETUP_WITH_YOUR_PYTHON.bat
    echo.
    echo OPTION 2 - Download Portable Python ^(No installation needed^):
    echo   - Download Python Embedded from: https://www.python.org/downloads/
    echo   - Extract to: %CLOUDSIM_ROOT%python-embed\
    echo   - Run this file again
    echo.
    echo ======================================================================
    pause
    exit /b 1
)

REM Use portable Python
set "PATH=%CLOUDSIM_ROOT%python-embed;%PATH%"
set "PYTHONPATH=%CLOUDSIM_ROOT%backend"

echo [1/3] Starting Backend Server...
start /min "CloudSim Backend" "%CLOUDSIM_ROOT%python-embed\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
timeout /t 6 /nobreak > nul

echo [2/3] Verifying Backend...
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing -TimeoutSec 2 | Out-Null; Write-Host '      Backend Ready!' -ForegroundColor Green } catch { Write-Host '      Starting...please wait' -ForegroundColor Yellow }" 

echo [3/3] Launching Desktop Application...
echo.
"%CLOUDSIM_ROOT%desktop-app\dist\CloudSim.exe"

REM Cleanup
taskkill /FI "WINDOWTITLE eq CloudSim Backend*" /F > nul 2>&1
exit
