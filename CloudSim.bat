@echo off
REM CloudSim Launcher - Starts Backend and Desktop App
title CloudSim Launcher

echo ======================================================================
echo   CloudSim - Cloud Infrastructure Simulator
echo   Starting Application...
echo ======================================================================
echo.

REM Get the directory where this script is located
set "CLOUDSIM_ROOT=%~dp0"
cd /d "%CLOUDSIM_ROOT%"

REM Check if backend is already running
echo [1/3] Checking backend status...
powershell -Command "$response = try { Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop; 'running' } catch { 'not running' }; $response" > nul 2>&1
if %errorlevel% equ 0 (
    echo      Backend already running on port 8000
    goto START_DESKTOP
)

REM Start backend server
echo [2/3] Starting Backend Server...
cd backend
start /min "CloudSim Backend" cmd /c "set PYTHONPATH=%CLOUDSIM_ROOT%backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
cd ..

REM Wait for backend to be ready
echo      Waiting for backend to initialize...
timeout /t 5 /nobreak > nul

:WAIT_BACKEND
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop | Out-Null; exit 0 } catch { exit 1 }" > nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 1 /nobreak > nul
    goto WAIT_BACKEND
)

echo      Backend ready!

:START_DESKTOP
REM Start desktop application
echo [3/3] Launching CloudSim Desktop...
echo.
echo ======================================================================
echo   Application starting - Please wait...
echo ======================================================================
echo.

cd desktop-app
python main_simple.py
cd ..

REM Cleanup - Kill backend when desktop app closes
echo.
echo Shutting down CloudSim...
taskkill /FI "WINDOWTITLE eq CloudSim Backend*" /F > nul 2>&1

exit
