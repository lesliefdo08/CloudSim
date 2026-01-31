#!/usr/bin/env pwsh
# CloudSim v1.0 - Automated Build and Release Script

param(
    [switch]$SkipBuild,
    [switch]$SkipPackage
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        CloudSim v1.0 - Build and Release Script        ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Step 1: Clean previous builds
if (-not $SkipBuild) {
    Write-Host "[1/5] Cleaning previous builds..." -ForegroundColor Yellow
    Set-Location desktop-app
    Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue
    Set-Location ..
    Write-Host "  ✓ Clean complete" -ForegroundColor Green
}

# Step 2: Build executable
if (-not $SkipBuild) {
    Write-Host "`n[2/5] Building Windows executable..." -ForegroundColor Yellow
    Set-Location desktop-app
    
    Write-Host "  Running PyInstaller..."
    pyinstaller cloudsim.spec --clean
    
    Set-Location ..
    
    if (Test-Path "desktop-app/dist/CloudSim.exe") {
        $exeSize = (Get-Item "desktop-app/dist/CloudSim.exe").Length / 1MB
        Write-Host "  ✓ Build successful! (Size: $([math]::Round($exeSize, 2)) MB)" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Build failed! CloudSim.exe not found." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "`n[2/5] Skipping build step (using existing executable)" -ForegroundColor Yellow
}

# Step 3: Create release package
if (-not $SkipPackage) {
    Write-Host "`n[3/5] Creating release package..." -ForegroundColor Yellow
    
    # Clean release directory
    Remove-Item -Recurse -Force release -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force release | Out-Null
    Write-Host "  Created release directory"
    
    # Copy executable
    Copy-Item desktop-app/dist/CloudSim.exe release/
    Write-Host "  ✓ Copied CloudSim.exe"
    
    # Copy backend (exclude test files)
    Copy-Item -Recurse backend release/backend
    Remove-Item release/backend/test*.py -ErrorAction SilentlyContinue
    Remove-Item release/backend/test*.ps1 -ErrorAction SilentlyContinue
    Write-Host "  ✓ Copied backend files"
    
    # Create Quick Start Guide
    $quickStart = @"
CloudSim v1.0 - Quick Start Guide
==================================

Thank you for downloading CloudSim!

REQUIREMENTS
------------
1. Windows 10/11 (64-bit)
2. Docker Desktop (Download: https://www.docker.com/products/docker-desktop)
3. 4 GB RAM minimum

INSTALLATION STEPS
------------------
1. Install Docker Desktop
   - Download from link above
   - Ensure Docker Desktop is running (check system tray)

2. Start Backend Server
   - Open PowerShell or Command Prompt
   - Navigate to the 'backend' folder
   - Run:
     pip install -r requirements.txt
     python main.py
   - Keep this window open (backend runs on http://127.0.0.1:8000)

3. Launch CloudSim
   - Double-click CloudSim.exe
   - The application will open

4. Start Learning!
   - Go to EC2 (Compute) section
   - Click "Launch Instance"
   - Fill in details and create
   - Click "Start" to create a Docker container
   - Use "Terminal" to execute commands inside the container

FEATURES
--------
✓ EC2 Instances with real Docker containers
✓ Interactive Linux terminal
✓ S3 Storage buckets
✓ RDS Databases
✓ Lambda Functions
✓ IAM Simulation

TROUBLESHOOTING
---------------
- "Backend not available": Ensure backend server is running
- "Docker not available": Ensure Docker Desktop is running
- Port 8000 conflict: Close other applications using port 8000

DOCUMENTATION
-------------
Full documentation: https://github.com/lesliefdo08/CloudSim

SUPPORT
-------
Issues: https://github.com/lesliefdo08/CloudSim/issues

LICENSE
-------
Educational Use Only

Developed by Leslie Fernando
Released: January 2026
"@
    
    $quickStart | Out-File -FilePath release/README.txt -Encoding UTF8
    Write-Host "  ✓ Created README.txt"
    
    # Create ZIP
    Write-Host "  Creating ZIP archive..."
    Compress-Archive -Path release/* -DestinationPath CloudSim-v1.0-Windows.zip -Force
    
    $zipSize = (Get-Item CloudSim-v1.0-Windows.zip).Length / 1MB
    Write-Host "  ✓ Package created (Size: $([math]::Round($zipSize, 2)) MB)" -ForegroundColor Green
} else {
    Write-Host "`n[3/5] Skipping package step" -ForegroundColor Yellow
}

# Step 4: Git status check
Write-Host "`n[4/5] Checking Git status..." -ForegroundColor Yellow
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "  ⚠ Uncommitted changes detected:" -ForegroundColor Yellow
    git status --short
    Write-Host ""
    $commit = Read-Host "  Commit changes? (y/n)"
    if ($commit -eq 'y') {
        $message = Read-Host "  Commit message"
        git add .
        git commit -m $message
        Write-Host "  ✓ Changes committed" -ForegroundColor Green
    }
} else {
    Write-Host "  ✓ No uncommitted changes" -ForegroundColor Green
}

# Step 5: Summary and next steps
Write-Host "`n[5/5] Build Summary" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────" -ForegroundColor Gray

if (Test-Path "CloudSim-v1.0-Windows.zip") {
    $packageSize = (Get-Item "CloudSim-v1.0-Windows.zip").Length / 1MB
    Write-Host "  Package: CloudSim-v1.0-Windows.zip" -ForegroundColor White
    Write-Host "  Size: $([math]::Round($packageSize, 2)) MB" -ForegroundColor White
    Write-Host "  Location: $(Get-Location)\CloudSim-v1.0-Windows.zip" -ForegroundColor Gray
}

Write-Host ""
Write-Host "✓ Build process complete!" -ForegroundColor Green
Write-Host ""

# Next steps
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                      NEXT STEPS                          ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Test the release package:" -ForegroundColor Yellow
Write-Host "   - Extract CloudSim-v1.0-Windows.zip to a test location"
Write-Host "   - Run backend/main.py"
Write-Host "   - Launch CloudSim.exe"
Write-Host "   - Test EC2 instance creation and terminal"
Write-Host ""
Write-Host "2. Push to GitHub:" -ForegroundColor Yellow
Write-Host "   git push origin main"
Write-Host ""
Write-Host "3. Create GitHub Release:" -ForegroundColor Yellow
Write-Host "   - Go to: https://github.com/lesliefdo08/CloudSim/releases/new"
Write-Host "   - Tag: v1.0"
Write-Host "   - Title: CloudSim v1.0 - Local Cloud Simulator"
Write-Host "   - Upload: CloudSim-v1.0-Windows.zip"
Write-Host "   - Publish release"
Write-Host ""
Write-Host "4. Verify release:" -ForegroundColor Yellow
Write-Host "   - Download ZIP from GitHub"
Write-Host "   - Test fresh installation"
Write-Host ""

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
