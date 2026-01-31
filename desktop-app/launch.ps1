# Quick launch script for CloudSim Desktop App
# Make sure backend is running on localhost:8000 first!

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "CloudSim Desktop Application Launcher" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Checking backend connection..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -Method GET -TimeoutSec 3 -UseBasicParsing
    Write-Host "[OK] Backend is running!" -ForegroundColor Green
}
catch {
    Write-Host "" -ForegroundColor Red
    Write-Host "[ERROR] Cannot connect to backend!" -ForegroundColor Red
    Write-Host "" -ForegroundColor Red
    Write-Host "Please start the backend first:" -ForegroundColor Yellow
    Write-Host "  cd backend" -ForegroundColor White
    Write-Host "  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000" -ForegroundColor White
    Write-Host "" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "Launching CloudSim Desktop App..." -ForegroundColor Yellow
Write-Host ""

& python main_simple.py

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] Failed to launch app!" -ForegroundColor Red
    Write-Host "Make sure PySide6 is installed:" -ForegroundColor Yellow
    Write-Host "  pip install PySide6==6.6.1 requests==2.31.0" -ForegroundColor White
    Write-Host ""
    pause
}
