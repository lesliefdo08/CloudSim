@echo off
REM Quick launch script for CloudSim Desktop App
REM Make sure backend is running on localhost:8000 first!

echo ============================================================
echo CloudSim Desktop Application Launcher
echo ============================================================
echo.
echo Checking backend connection...
curl -s http://localhost:8000/docs > nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Cannot connect to backend!
    echo.
    echo Please start the backend first:
    echo   cd backend
    echo   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
    echo.
    pause
    exit /b 1
)

echo [OK] Backend is running!
echo.
echo Launching CloudSim Desktop App...
echo.

python main_simple.py

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to launch app!
    echo Make sure PySide6 is installed:
    echo   pip install PySide6==6.6.1 requests==2.31.0
    echo.
    pause
)
