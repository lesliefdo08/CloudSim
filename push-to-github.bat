@echo off
REM CloudSim - Git Setup and Push to GitHub
REM Run this script to initialize git and push to GitHub

echo ============================================
echo CloudSim - GitHub Deployment
echo ============================================
echo.

cd "C:\Users\Leslie Fernando\Projects\CloudSim"

echo [1/5] Initializing Git repository...
git init
echo.

echo [2/5] Adding files to Git...
git add .
echo.

echo [3/5] Creating initial commit...
git commit -m "v1.0: CloudSim Desktop Application with AWS-grade UI polish"
echo.

echo [4/5] Adding GitHub remote...
git remote add origin https://github.com/lesliefdo08/CloudSim.git
echo.

echo [5/5] Pushing to GitHub...
git branch -M main
git push -u origin main
echo.

echo ============================================
echo  SUCCESS! CloudSim pushed to GitHub
echo ============================================
echo.
echo Repository: https://github.com/lesliefdo08/CloudSim
echo.

pause
