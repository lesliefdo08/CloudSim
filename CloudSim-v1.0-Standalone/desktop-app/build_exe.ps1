# CloudSim Desktop - Build Script for Windows Executable
# Creates a standalone .exe file with PyInstaller

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "CloudSim Desktop - Building Windows Executable" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if PyInstaller is installed
Write-Host "Checking PyInstaller..." -ForegroundColor Yellow
$pyinstaller = & "C:/Users/Leslie Fernando/Projects/CloudSim/.venv/Scripts/pip.exe" list | Select-String "pyinstaller"
if (-not $pyinstaller) {
    Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
    & "C:/Users/Leslie Fernando/Projects/CloudSim/.venv/Scripts/pip.exe" install pyinstaller
}
Write-Host "✅ PyInstaller ready" -ForegroundColor Green
Write-Host ""

# Clean previous builds
Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "*.spec") { Remove-Item -Force "*.spec" }
Write-Host "✅ Cleaned" -ForegroundColor Green
Write-Host ""

# Build the executable
Write-Host "Building CloudSim Desktop executable..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray
Write-Host ""

& "C:/Users/Leslie Fernando/Projects/CloudSim/.venv/Scripts/pyinstaller.exe" `
    --name "CloudSim-Desktop" `
    --windowed `
    --onefile `
    --icon "icon.ico" `
    --add-data "icon.ico;." `
    --hidden-import "PySide6.QtCore" `
    --hidden-import "PySide6.QtGui" `
    --hidden-import "PySide6.QtWidgets" `
    --hidden-import "requests" `
    main_simple.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "✅ BUILD SUCCESSFUL!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Executable location:" -ForegroundColor Cyan
    Write-Host "  dist\CloudSim-Desktop.exe" -ForegroundColor White
    Write-Host ""
    
    if (Test-Path "dist\CloudSim-Desktop.exe") {
        $fileInfo = Get-Item "dist\CloudSim-Desktop.exe"
        $sizeInMB = [math]::Round($fileInfo.Length / 1MB, 2)
        Write-Host "File size: $sizeInMB MB" -ForegroundColor Gray
        Write-Host "Created: $($fileInfo.CreationTime)" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "You can now distribute: dist\CloudSim-Desktop.exe" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ BUILD FAILED" -ForegroundColor Red
    Write-Host "Check the output above for errors" -ForegroundColor Yellow
    exit 1
}
