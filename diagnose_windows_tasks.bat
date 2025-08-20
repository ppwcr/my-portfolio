@echo off
echo ========================================
echo Portfolio Dashboard - Windows Diagnostic
echo ========================================
echo.
echo This script will check all Windows-specific components
echo including scheduled tasks, auto-start, and .bat files.
echo.

set "CURRENT_DIR=%~dp0"
set "ERRORS_FOUND=0"

echo ========================================
echo Step 1: Checking Required .bat Files
echo ========================================

REM Check if required .bat files exist
if exist "%CURRENT_DIR%setup.bat" (
    echo ✅ setup.bat found
) else (
    echo ❌ setup.bat missing
    set /a ERRORS_FOUND+=1
)

if exist "%CURRENT_DIR%start.bat" (
    echo ✅ start.bat found
) else (
    echo ❌ start.bat missing
    set /a ERRORS_FOUND+=1
)

if exist "%CURRENT_DIR%run_scheduled_scrape.bat" (
    echo ✅ run_scheduled_scrape.bat found
) else (
    echo ❌ run_scheduled_scrape.bat missing
    set /a ERRORS_FOUND+=1
)

if exist "%CURRENT_DIR%server_manager.bat" (
    echo ✅ server_manager.bat found
) else (
    echo ❌ server_manager.bat missing
    set /a ERRORS_FOUND+=1
)

echo.
echo ========================================
echo Step 2: Checking Python Environment
echo ========================================

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL%==0 (
    echo ✅ Python found
    python --version
) else (
    echo ❌ Python not found or not in PATH
    set /a ERRORS_FOUND+=1
)

REM Check if required packages are installed
pip show fastapi >nul 2>&1
if %ERRORLEVEL%==0 (
    echo ✅ FastAPI installed
) else (
    echo ❌ FastAPI not installed
    set /a ERRORS_FOUND+=1
)

pip show uvicorn >nul 2>&1
if %ERRORLEVEL%==0 (
    echo ✅ Uvicorn installed
) else (
    echo ❌ Uvicorn not installed
    set /a ERRORS_FOUND+=1
)

pip show pandas >nul 2>&1
if %ERRORLEVEL%==0 (
    echo ✅ Pandas installed
) else (
    echo ❌ Pandas not installed
    set /a ERRORS_FOUND+=1
)

echo.
echo ========================================
echo Step 3: Checking Windows Scheduled Tasks
echo ========================================

REM Check each scheduled task
schtasks /Query /TN SET_Scraper_1030 >nul 2>&1
if %ERRORLEVEL%==0 (
    echo ✅ 10:30 AM scheduled task found
) else (
    echo ❌ 10:30 AM scheduled task missing
    set /a ERRORS_FOUND+=1
)

schtasks /Query /TN SET_Scraper_1300 >nul 2>&1
if %ERRORLEVEL%==0 (
    echo ✅ 13:00 PM scheduled task found
) else (
    echo ❌ 13:00 PM scheduled task missing
    set /a ERRORS_FOUND+=1
)

schtasks /Query /TN SET_Scraper_1730 >nul 2>&1
if %ERRORLEVEL%==0 (
    echo ✅ 17:30 PM scheduled task found
) else (
    echo ❌ 17:30 PM scheduled task missing
    set /a ERRORS_FOUND+=1
)

echo.
echo ========================================
echo Step 4: Checking Auto-Start Setup
echo ========================================

REM Check if VBS script exists
if exist "%CURRENT_DIR%portfolio_startup_server.vbs" (
    echo ✅ VBS script found
) else (
    echo ❌ VBS script missing
    set /a ERRORS_FOUND+=1
)

REM Check if startup shortcut exists
for /f "tokens=2*" %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Startup 2^>nul') do set "STARTUP_FOLDER=%%b"

if defined STARTUP_FOLDER (
    if exist "%STARTUP_FOLDER%\Portfolio Dashboard Server.lnk" (
        echo ✅ Startup shortcut found
    ) else (
        echo ❌ Startup shortcut missing
        set /a ERRORS_FOUND+=1
    )
) else (
    echo ⚠️  Could not determine startup folder
    set /a ERRORS_FOUND+=1
)

echo.
echo ========================================
echo Step 5: Checking Recent Activity
echo ========================================

REM Check for recent files in _out directory
if exist "%CURRENT_DIR%_out" (
    echo ✅ _out directory found
    dir "%CURRENT_DIR%_out" /o-d /b | findstr /i "2025" >nul 2>&1
    if %ERRORLEVEL%==0 (
        echo ✅ Recent files found in _out directory
    ) else (
        echo ⚠️  No recent files found in _out directory
    )
) else (
    echo ❌ _out directory missing
    set /a ERRORS_FOUND+=1
)

REM Check for log files
dir "%CURRENT_DIR%scraper_*.log" >nul 2>&1
if %ERRORLEVEL%==0 (
    echo ✅ Scraper log files found
) else (
    echo ⚠️  No scraper log files found
)

echo.
echo ========================================
echo Step 6: Testing Scheduled Script
echo ========================================

REM Test if the scheduled script can be imported
python -c "import sys; sys.path.append('.'); from background_updater import BackgroundUpdater; print('BackgroundUpdater imported successfully')" >nul 2>&1
if %ERRORLEVEL%==0 (
    echo ✅ BackgroundUpdater module works
) else (
    echo ❌ BackgroundUpdater module failed
    set /a ERRORS_FOUND+=1
)

echo.
echo ========================================
echo Step 7: Checking Permissions
echo ========================================

REM Check if running as administrator
net session >nul 2>&1
if %ERRORLEVEL%==0 (
    echo ✅ Running as Administrator
) else (
    echo ⚠️  Not running as Administrator (may cause issues)
)

REM Check if current directory is writable
echo test > "%CURRENT_DIR%test_write.tmp" 2>nul
if exist "%CURRENT_DIR%test_write.tmp" (
    del "%CURRENT_DIR%test_write.tmp" >nul 2>&1
    echo ✅ Current directory is writable
) else (
    echo ❌ Current directory is not writable
    set /a ERRORS_FOUND+=1
)

echo.
echo ========================================
echo Diagnostic Summary
echo ========================================

if %ERRORS_FOUND%==0 (
    echo ✅ All checks passed! Your Windows setup is working correctly.
    echo.
    echo Scheduled tasks should be running at:
    echo - 10:30 AM (Monday-Friday)
    echo - 13:00 PM (Monday-Friday)
    echo - 17:30 PM (Monday-Friday)
    echo.
    echo Auto-start should work on next login.
) else (
    echo ❌ Found %ERRORS_FOUND% issue(s) that need to be fixed.
    echo.
    echo To fix these issues:
    echo 1. Run setup.bat as Administrator
    echo 2. If that doesn't work, run the manual commands below
    echo.
    echo Manual fix commands:
    echo - Recreate tasks: Use the schtasks commands in WINDOWS_SCHEDULED_TASKS_SETUP.md
    echo - Fix auto-start: Run fix_autostart.bat
    echo - Install dependencies: pip install -r requirements.txt
)

echo.
echo ========================================
echo Management Commands
echo ========================================
echo.
echo To manage your setup:
echo - View tasks: schtasks /query /fo table
echo - Edit tasks: taskschd.msc
echo - Test scraping: run_scheduled_scrape.bat
echo - Start server: start.bat
echo - Server manager: server_manager.bat
echo.
echo To remove everything:
echo - Delete tasks: schtasks /Delete /TN SET_Scraper_1030 /F
echo - Delete auto-start: Remove shortcut from startup folder
echo.
echo ========================================
echo Windows diagnostic complete! Press any key to exit...
pause >nul
