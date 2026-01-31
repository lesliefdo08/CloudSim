# CloudSim Build Script
Write-Host "CloudSim v1.0 - Building Executable" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Kill any running Python processes
Write-Host "[1/4] Stopping running processes..." -ForegroundColor Yellow
Stop-Process -Name python -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Clean old build
Write-Host "[2/4] Cleaning old build..." -ForegroundColor Yellow
if (Test-Path "dist") { Remove-Item -Recurse -Force dist }
if (Test-Path "build") { Remove-Item -Recurse -Force build }

# Run PyInstaller
Write-Host "[3/4] Building with PyInstaller..." -ForegroundColor Yellow
pyinstaller cloudsim.spec --clean --noconfirm 2>&1 | Out-Null

# Check result
Write-Host "[4/4] Verifying build..." -ForegroundColor Yellow
if (Test-Path "dist\CloudSim.exe") {
    $size = [math]::Round((Get-Item dist\CloudSim.exe).Length / 1MB, 2)
    Write-Host ""
    Write-Host "✓ BUILD SUCCESSFUL!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  File: dist\CloudSim.exe" -ForegroundColor Gray
    Write-Host "  Size: $size MB" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  CHANGES:" -ForegroundColor Cyan
    Write-Host "  • Taskbar icon fixed (uses sys._MEIPASS)" -ForegroundColor White
    Write-Host "  • All demo data removed" -ForegroundColor White
    Write-Host ""
    Write-Host "  READY FOR TESTING!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "✗ BUILD FAILED - See errors above" -ForegroundColor Red
    exit 1
}
