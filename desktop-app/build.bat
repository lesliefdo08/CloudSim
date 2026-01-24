@echo off
REM CloudSim Desktop Build Script
REM Builds a standalone Windows executable using PyInstaller

echo ============================================
echo CloudSim Desktop - Build Script
echo ============================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [ERROR] PyInstaller is not installed
    echo.
    echo Installing PyInstaller...
    pip install pyinstaller
    echo.
)

REM Clean previous builds
echo [1/4] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo       Done.
echo.

REM Build with PyInstaller
echo [2/4] Building executable with PyInstaller...
echo       This may take 2-5 minutes...
echo.
pyinstaller cloudsim.spec
echo.

REM Check if build succeeded
if not exist dist\CloudSim\CloudSim.exe (
    echo [ERROR] Build failed. Check errors above.
    echo.
    pause
    exit /b 1
)

echo [3/4] Build successful!
echo.

REM Display build info
echo [4/4] Build Information:
echo       Executable: dist\CloudSim\CloudSim.exe
for %%A in (dist\CloudSim) do echo       Size: %%~zA bytes
echo.

REM Test the executable
echo Testing executable...
start "" "dist\CloudSim\CloudSim.exe"
timeout /t 3 /nobreak >nul
echo.

echo ============================================
echo Build Complete!
echo ============================================
echo.
echo To distribute:
echo   1. Navigate to: dist\CloudSim\
echo   2. Zip the entire CloudSim folder
echo   3. Rename to: CloudSim-v1.0-Windows.zip
echo   4. Share with students
echo.
echo To test:
echo   - The application should now be running
echo   - Try creating resources in each service
echo   - Check that data\ folder is created
echo.

pause
