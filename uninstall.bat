@echo off
setlocal enabledelayedexpansion
echo ========================================
echo Portfolio Dashboard Uninstall
echo ========================================
echo.
echo This script will remove:
echo 1. Auto-start on Windows boot
echo 2. Scheduled task for daily updates
echo 3. Scheduled task for data refresh
echo 4. Silent startup script
echo.

REM Change to script directory
cd /d "%~dp0"
echo 📁 Working directory: %CD%
echo.

REM Check if running as administrator
net session >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: This script requires administrator privileges
    echo Please right-click and "Run as administrator"
    pause
    exit /b 1
)
echo ✅ Administrator privileges confirmed
echo.

REM Get current user
for /f "tokens=2 delims==" %%a in ('wmic useraccount where "name='%USERNAME%'" get name /value') do set "CURRENT_USER=%%a"
echo 👤 Current user: %CURRENT_USER%
echo.

REM 1. Remove auto-start entry
echo 🔧 Removing auto-start entry...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "PortfolioDashboard" /f >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Auto-start entry not found or already removed
) else (
    echo ✅ Auto-start entry removed
)
echo.

REM 2. Remove scheduled task for daily git updates
echo 🔧 Removing git update scheduled task...
schtasks /delete /tn "PortfolioDashboard_GitUpdate" /f >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Git update scheduled task not found or already removed
) else (
    echo ✅ Git update scheduled task removed
)
echo.

REM 3. Remove scheduled tasks for data scraping
echo 🔧 Removing data scraping scheduled tasks...
schtasks /delete /tn "SET_Scraper_1030" /f >nul 2>&1
if errorlevel 1 (
    echo ⚠️  10:30 AM scheduled task not found or already removed
) else (
    echo ✅ 10:30 AM scheduled task removed
)

schtasks /delete /tn "SET_Scraper_1300" /f >nul 2>&1
if errorlevel 1 (
    echo ⚠️  1:00 PM scheduled task not found or already removed
) else (
    echo ✅ 1:00 PM scheduled task removed
)

schtasks /delete /tn "SET_Scraper_1730" /f >nul 2>&1
if errorlevel 1 (
    echo ⚠️  5:30 PM scheduled task not found or already removed
) else (
    echo ✅ 5:30 PM scheduled task removed
)
echo.

REM 4. Remove startup script
echo 🔧 Removing startup script...
if exist "startup_with_update.bat" (
    del "startup_with_update.bat"
    echo ✅ Startup script removed
) else (
    echo ⚠️  Startup script not found
)
echo.

REM 5. Stop any running server processes
echo 🔧 Stopping any running server processes...
taskkill /f /im python.exe /fi "WINDOWTITLE eq Portfolio*" >nul 2>&1
taskkill /f /im uvicorn.exe >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 2^>nul') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo ✅ Server processes stopped
echo.

echo ========================================
echo Uninstall Complete!
echo ========================================
echo.
echo ✅ Auto-start removed
echo ✅ Scheduled tasks removed
echo ✅ Silent startup script removed
echo ✅ Server processes stopped
echo.
echo The Portfolio Dashboard will no longer:
echo - Start automatically when Windows boots
echo - Update from git automatically
echo - Refresh data at scheduled times (10:30, 1:00, 5:30 PM weekdays)
echo.
echo To re-enable auto-start, run: setup.bat
echo.
pause
