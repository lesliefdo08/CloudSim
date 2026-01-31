@echo off
REM CloudSim Setup - For users with Python installed
title CloudSim Setup

echo ======================================================================
echo   CloudSim v1.0 - Setup Wizard
echo ======================================================================
echo.

REM Check Python
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Python is NOT installed!
    echo.
    echo Please install Python 3.8 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

echo [OK] Python found:
python --version
echo.

REM Install backend dependencies
echo [1/2] Installing backend dependencies...
cd backend
pip install -r requirements.txt --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo [X] Backend installation failed!
    pause
    exit /b 1
)
echo      Done!
cd ..

REM Install desktop dependencies  
echo [2/2] Installing desktop dependencies...
cd desktop-app
pip install -r requirements.txt --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo [X] Desktop installation failed!
    pause
    exit /b 1
)
echo      Done!
cd ..

echo.
echo ======================================================================
echo   Setup Complete!
echo ======================================================================
echo.
echo CloudSim is ready to use!
echo.
echo To launch CloudSim:
echo   - Double-click: CloudSim.bat
echo   - Or run from command line: CloudSim.bat
echo.
echo ======================================================================
pause
