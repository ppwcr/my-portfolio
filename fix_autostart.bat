@echo off
echo Setting up Portfolio Dashboard Simple Auto-Start...
echo.

REM Get the current directory
set "CURRENT_DIR=%~dp0"
set "BATCH_PATH=%CURRENT_DIR%start.bat"

REM Get the startup folder path
for /f "tokens=2*" %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Startup 2^>nul') do set "STARTUP_FOLDER=%%b"

echo Current directory: %CURRENT_DIR%
echo Batch path: %BATCH_PATH%
echo Startup folder: %STARTUP_FOLDER%
echo.

REM Create shortcut directly to the batch file
echo Creating startup shortcut...
powershell -Command "try { $WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTUP_FOLDER%\Portfolio Dashboard.lnk'); $Shortcut.TargetPath = '%BATCH_PATH%'; $Shortcut.WorkingDirectory = '%CURRENT_DIR%'; $Shortcut.Description = 'Portfolio Dashboard Auto-Start'; $Shortcut.Save(); Write-Host 'Shortcut created successfully' } catch { Write-Host 'Error creating shortcut: ' + $_.Exception.Message; exit 1 }"

if errorlevel 1 (
    echo.
    echo Error: Failed to create startup shortcut
    echo Please run this script as Administrator
    echo.
    echo Alternative: Try Method 3 (setup_manual_startup.bat) instead
    pause
    exit /b 1
)

echo.
echo ✅ Simple auto-start setup complete!
echo.
echo The Portfolio Dashboard will now start automatically when you log in.
echo Note: This will show a terminal window when starting.
echo.
echo To disable auto-start:
echo 1. Press Win+R, type "shell:startup" and press Enter
echo 2. Delete "Portfolio Dashboard.lnk"
echo.
echo To manually start/stop:
echo - Start: Double-click start.bat
echo - Stop: Close the terminal window or press Ctrl+C
echo.
pause
