@echo off
echo Setting up Portfolio Dashboard as Windows Task...
echo.

REM Get the current directory
set "CURRENT_DIR=%~dp0"
set "BATCH_PATH=%CURRENT_DIR%start.bat"

REM Create the scheduled task
echo Creating scheduled task...
schtasks /create /tn "Portfolio Dashboard" /tr "%BATCH_PATH%" /sc onlogon /ru "%USERNAME%" /f

if errorlevel 1 (
    echo Error: Failed to create scheduled task
    echo Please run this script as Administrator
    pause
    exit /b 1
)

echo.
echo ✅ Task Scheduler setup complete!
echo.
echo The Portfolio Dashboard will now start automatically when you log in.
echo.
echo To disable auto-start:
echo 1. Open Task Scheduler (search in Start menu)
echo 2. Find "Portfolio Dashboard" task
echo 3. Right-click and select "Disable" or "Delete"
echo.
echo To manually start/stop:
echo - Start: Double-click start.bat
echo - Stop: Close the terminal window or press Ctrl+C
echo.
pause
