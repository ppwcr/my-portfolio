@echo off
echo Setting up Portfolio Dashboard Manual Auto-Start...
echo.

REM Get the current directory and startup folder
set "CURRENT_DIR=%~dp0"
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

REM Copy start.bat to startup folder
echo Copying start.bat to startup folder...
copy "%CURRENT_DIR%start.bat" "%STARTUP_FOLDER%\Portfolio Dashboard.bat"

if errorlevel 1 (
    echo Error: Failed to copy file to startup folder
    echo Please run this script as Administrator
    pause
    exit /b 1
)

echo.
echo ✅ Manual startup setup complete!
echo.
echo The Portfolio Dashboard will now start automatically when you log in.
echo.
echo To disable auto-start:
echo 1. Press Win+R, type "shell:startup" and press Enter
echo 2. Delete "Portfolio Dashboard.bat"
echo.
echo To manually start/stop:
echo - Start: Double-click start.bat
echo - Stop: Close the terminal window or press Ctrl+C
echo.
pause
