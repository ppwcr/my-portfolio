@echo off
echo Setting up Portfolio Dashboard Auto-Start...
echo.

REM Get the current directory
set "CURRENT_DIR=%~dp0"
set "BATCH_PATH=%CURRENT_DIR%start.bat"

REM Create a VBS script to run the batch file hidden
echo Set WshShell = CreateObject("WScript.Shell") > "%TEMP%\portfolio_startup.vbs"
echo WshShell.Run """%BATCH_PATH%""", 0, False >> "%TEMP%\portfolio_startup.vbs"

REM Get the startup folder path
for /f "tokens=2*" %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Startup 2^>nul') do set "STARTUP_FOLDER=%%b"

REM Create shortcut in Startup folder
echo Creating startup shortcut...
echo Current directory: %CURRENT_DIR%
echo Batch path: %BATCH_PATH%
echo Startup folder: %STARTUP_FOLDER%

REM Create the shortcut using PowerShell
powershell -Command "try { $WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTUP_FOLDER%\Portfolio Dashboard.lnk'); $Shortcut.TargetPath = 'wscript.exe'; $Shortcut.Arguments = '%TEMP%\portfolio_startup.vbs'; $Shortcut.WorkingDirectory = '%CURRENT_DIR%'; $Shortcut.Description = 'Portfolio Dashboard Auto-Start'; $Shortcut.Save(); Write-Host 'Shortcut created successfully' } catch { Write-Host 'Error creating shortcut: ' + $_.Exception.Message; exit 1 }"

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
echo ✅ Auto-start setup complete!
echo.
echo The Portfolio Dashboard will now start automatically when you log in.
echo It will also start the auto-scraper that updates data every 10 minutes.
echo.
echo To disable auto-start:
echo 1. Press Win+R, type "shell:startup" and press Enter
echo 2. Delete "Portfolio Dashboard.lnk"
echo.
echo To manually start/stop:
echo - Start with auto-scraper: Double-click start.bat
echo - Stop: Close the terminal window or press Ctrl+C
echo.
pause
