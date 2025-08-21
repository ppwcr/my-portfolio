@echo off
setlocal enabledelayedexpansion
echo ========================================
echo Portfolio Dashboard Auto-Setup
echo ========================================
echo.
echo This script will set up:
echo 1. Auto-start on Windows boot
echo 2. Scheduled task for daily updates
echo 3. Scheduled task for data refresh
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

REM Get current user and path
for /f "tokens=2 delims==" %%a in ('wmic useraccount where "name='%USERNAME%'" get name /value') do set "CURRENT_USER=%%a"
set "SCRIPT_PATH=%CD%"
set "START_BAT=%SCRIPT_PATH%\start.bat"
set "GIT_UPDATE_BAT=%SCRIPT_PATH%\git_update.bat"

echo 👤 Current user: %CURRENT_USER%
echo 📁 Script path: %SCRIPT_PATH%
echo.

REM 1. Create auto-start entry
echo 🔧 Setting up auto-start...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "PortfolioDashboard" /t REG_SZ /d "\"%START_BAT%\"" /f
if errorlevel 1 (
    echo ❌ Failed to create auto-start entry
    pause
    exit /b 1
)
echo ✅ Auto-start entry created
echo.

REM 2. Create scheduled task for daily git updates at 6:00 AM
echo 🔧 Creating scheduled task for daily updates at 6:00 AM...
schtasks /create /tn "PortfolioDashboard_GitUpdate" /tr "\"%GIT_UPDATE_BAT%\"" /sc daily /st 06:00 /ru "%CURRENT_USER%" /f
if errorlevel 1 (
    echo ❌ Failed to create git update scheduled task
    pause
    exit /b 1
)
echo ✅ Git update scheduled task created (daily at 6:00 AM)
echo.

REM 3. Create scheduled tasks for data scraping (10:30, 13:00, 17:30 weekdays)
echo 🔧 Creating scheduled tasks for data scraping...
schtasks /create /tn "SET_Scraper_1030" /tr "python \"%SCRIPT_PATH%\background_updater.py\"" /sc weekly /d MON,TUE,WED,THU,FRI /st 10:30 /ru "%CURRENT_USER%" /f
if errorlevel 1 (
    echo ❌ Failed to create 10:30 AM scheduled task
    pause
    exit /b 1
)
echo ✅ 10:30 AM scheduled task created (weekdays)

schtasks /create /tn "SET_Scraper_1300" /tr "python \"%SCRIPT_PATH%\background_updater.py\"" /sc weekly /d MON,TUE,WED,THU,FRI /st 13:00 /ru "%CURRENT_USER%" /f
if errorlevel 1 (
    echo ❌ Failed to create 1:00 PM scheduled task
    pause
    exit /b 1
)
echo ✅ 1:00 PM scheduled task created (weekdays)

schtasks /create /tn "SET_Scraper_1730" /tr "python \"%SCRIPT_PATH%\background_updater.py\"" /sc weekly /d MON,TUE,WED,THU,FRI /st 17:30 /ru "%CURRENT_USER%" /f
if errorlevel 1 (
    echo ❌ Failed to create 5:30 PM scheduled task
    pause
    exit /b 1
)
echo ✅ 5:30 PM scheduled task created (weekdays)
echo.

REM 4. Create startup script that runs git update first, then starts server
echo 🔧 Creating startup script with git update...
(
echo @echo off
echo cd /d "%SCRIPT_PATH%"
echo echo Starting Portfolio Dashboard with git update...
echo echo Running git update...
echo call "%GIT_UPDATE_BAT%"
echo echo Starting server...
echo start /min python -c "import uvicorn; uvicorn.run('main:app', host='127.0.0.1', port=8000, log_level='error')"
echo echo Portfolio Dashboard started successfully
) > "%SCRIPT_PATH%\startup_with_update.bat"

echo ✅ Startup script with git update created
echo.

REM 5. Create auto-start entry
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "PortfolioDashboard" /t REG_SZ /d "\"%SCRIPT_PATH%\startup_with_update.bat\"" /f
echo ✅ Auto-start configured with git update
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo ✅ Auto-start configured
echo ✅ Daily git updates scheduled (6:00 AM)
echo ✅ Data refresh scheduled (every 30 minutes)
echo ✅ Silent startup script created
echo.
echo The Portfolio Dashboard will now:
echo - Start automatically when Windows boots (with git update)
echo - Update from git daily at 6:00 AM (scheduled task)
echo - Refresh data at 10:30 AM, 1:00 PM, 5:30 PM (weekdays only)
echo.
echo To stop auto-start, run: uninstall.bat
echo.
pause
