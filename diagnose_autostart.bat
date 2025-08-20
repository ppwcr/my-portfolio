@echo off
echo ========================================
echo Portfolio Dashboard Auto-Start Diagnostics
echo ========================================
echo.
echo This script will check all components of the auto-start system
echo and help identify any issues.
echo.

set "CURRENT_DIR=%~dp0"
set "ERRORS_FOUND=0"

echo ========================================
echo Step 1: Checking Required Files
echo ========================================

REM Check if start.bat exists
if exist "%CURRENT_DIR%start.bat" (
    echo ✅ start.bat found
) else (
    echo ❌ start.bat missing
    set /a ERRORS_FOUND+=1
)

REM Check if run_scheduled_scrape.bat exists
if exist "%CURRENT_DIR%run_scheduled_scrape.bat" (
    echo ✅ run_scheduled_scrape.bat found
) else (
    echo ❌ run_scheduled_scrape.bat missing
    set /a ERRORS_FOUND+=1
)

REM Check if VBS script exists
if exist "%CURRENT_DIR%portfolio_startup_server.vbs" (
    echo ✅ portfolio_startup_server.vbs found
) else (
    echo ❌ portfolio_startup_server.vbs missing
    set /a ERRORS_FOUND+=1
)

echo.
echo ========================================
echo Step 2: Checking Startup Folder
echo ========================================

REM Try to find startup folder
set "STARTUP_FOLDER="

REM Method 1: Registry query
for /f "tokens=2*" %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Startup 2^>nul') do set "STARTUP_FOLDER=%%b"

if defined STARTUP_FOLDER (
    echo ✅ Startup folder found via registry: %STARTUP_FOLDER%
) else (
    echo ⚠️  Registry query failed, trying alternative methods...
    
    REM Method 2: Environment variable
    set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
    if exist "%STARTUP_FOLDER%" (
        echo ✅ Startup folder found via environment: %STARTUP_FOLDER%
    ) else (
        REM Method 3: Common location
        set "STARTUP_FOLDER=%USERPROFILE%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"
        if exist "%STARTUP_FOLDER%" (
            echo ✅ Startup folder found via common path: %STARTUP_FOLDER%
        ) else (
            echo ❌ Startup folder not found
            set /a ERRORS_FOUND+=1
        )
    )
)

echo.
echo ========================================
echo Step 3: Checking Startup Shortcut
echo ========================================

if defined STARTUP_FOLDER (
    if exist "%STARTUP_FOLDER%\Portfolio Dashboard Server.lnk" (
        echo ✅ Startup shortcut found
    ) else (
        echo ❌ Startup shortcut missing
        set /a ERRORS_FOUND+=1
    )
) else (
    echo ❌ Cannot check shortcut - startup folder not found
    set /a ERRORS_FOUND+=1
)

echo.
echo ========================================
echo Step 4: Checking Scheduled Tasks
echo ========================================

REM Check each scheduled task
schtasks /Query /TN SET_Scraper_1030 >NUL 2>&1
if %ERRORLEVEL%==0 (
    echo ✅ 10:30 AM scheduled task found
) else (
    echo ❌ 10:30 AM scheduled task missing
    set /a ERRORS_FOUND+=1
)

schtasks /Query /TN SET_Scraper_1300 >NUL 2>&1
if %ERRORLEVEL%==0 (
    echo ✅ 13:00 PM scheduled task found
) else (
    echo ❌ 13:00 PM scheduled task missing
    set /a ERRORS_FOUND+=1
)

schtasks /Query /TN SET_Scraper_1730 >NUL 2>&1
if %ERRORLEVEL%==0 (
    echo ✅ 17:30 PM scheduled task found
) else (
    echo ❌ 17:30 PM scheduled task missing
    set /a ERRORS_FOUND+=1
)

echo.
echo ========================================
echo Step 5: Checking Python Environment
echo ========================================

REM Check if Python is installed
python --version >NUL 2>&1
if %ERRORLEVEL%==0 (
    echo ✅ Python found
    python --version
) else (
    echo ❌ Python not found or not in PATH
    set /a ERRORS_FOUND+=1
)

REM Check if requirements are installed
pip show fastapi >NUL 2>&1
if %ERRORLEVEL%==0 (
    echo ✅ FastAPI installed
) else (
    echo ❌ FastAPI not installed
    set /a ERRORS_FOUND+=1
)

echo.
echo ========================================
echo Step 6: Testing VBS Script
echo ========================================

if exist "%CURRENT_DIR%portfolio_startup_server.vbs" (
    echo Testing VBS script syntax...
    cscript //nologo "%CURRENT_DIR%portfolio_startup_server.vbs" >NUL 2>&1
    if %ERRORLEVEL%==0 (
        echo ✅ VBS script syntax is valid
    ) else (
        echo ❌ VBS script has syntax errors
        set /a ERRORS_FOUND+=1
    )
) else (
    echo ❌ Cannot test VBS script - file missing
    set /a ERRORS_FOUND+=1
)

echo.
echo ========================================
echo Step 7: Checking Permissions
echo ========================================

REM Check if running as administrator
net session >NUL 2>&1
if %ERRORLEVEL%==0 (
    echo ✅ Running as Administrator
) else (
    echo ⚠️  Not running as Administrator (may cause issues with scheduled tasks)
)

REM Check if startup folder is writable
if defined STARTUP_FOLDER (
    echo Test > "%STARTUP_FOLDER%\test_write.tmp" 2>NUL
    if exist "%STARTUP_FOLDER%\test_write.tmp" (
        del "%STARTUP_FOLDER%\test_write.tmp" >NUL 2>&1
        echo ✅ Startup folder is writable
    ) else (
        echo ❌ Startup folder is not writable
        set /a ERRORS_FOUND+=1
    )
)

echo.
echo ========================================
echo Diagnostic Summary
echo ========================================

if %ERRORS_FOUND%==0 (
    echo ✅ All checks passed! Auto-start should work correctly.
    echo.
    echo If auto-start still doesn't work:
    echo 1. Check Windows Event Viewer for errors
    echo 2. Try manually running start.bat to see if it works
    echo 3. Check if antivirus is blocking the startup
) else (
    echo ❌ Found %ERRORS_FOUND% issue(s) that need to be fixed.
    echo.
    echo To fix these issues:
    echo 1. Run setup.bat as Administrator
    echo 2. If that doesn't work, run the manual fix commands below
    echo.
    echo Manual fix commands:
    echo - Recreate VBS: echo Set WshShell = CreateObject("WScript.Shell") ^> portfolio_startup_server.vbs
    echo - Recreate shortcut: Use setup.bat as Administrator
    echo - Recreate tasks: Use setup.bat as Administrator
)

echo.
echo ========================================
echo Troubleshooting Commands
echo ========================================
echo.
echo To manually test components:
echo - Test start.bat: Double-click start.bat
echo - Test VBS: cscript //nologo portfolio_startup_server.vbs
echo - View tasks: Press Win+R, type "taskschd.msc"
echo - View startup items: Press Win+R, type "shell:startup"
echo.
echo To remove auto-start:
echo - Delete shortcut: del "%STARTUP_FOLDER%\Portfolio Dashboard Server.lnk"
echo - Delete VBS: del portfolio_startup_server.vbs
echo - Delete tasks: schtasks /Delete /TN SET_Scraper_1030 /F
echo.
echo ========================================
echo Diagnostics complete. Press any key to exit...
pause >nul
