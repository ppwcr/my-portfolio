@echo off
echo ========================================
echo Simple Git Update
echo ========================================
echo.

REM Change to my-portfolio directory
cd /d "%~dp0"

echo 📁 Changed to directory: %CD%
echo.

echo 🔄 Pulling latest changes from main...
git pull origin main

if errorlevel 1 (
    echo ❌ Git pull failed
    pause
    exit /b 1
) else (
    echo ✅ Successfully updated!
)

echo.
echo ========================================
echo Update Complete!
echo ========================================
pause
