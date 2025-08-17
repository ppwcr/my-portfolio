@echo off
echo Setting up Portfolio Dashboard Auto-Start...
echo.

REM Get the current directory
set "CURRENT_DIR=%~dp0"
set "BATCH_PATH=%CURRENT_DIR%start.bat"

REM Create a VBS script to run the batch file hidden
echo Set WshShell = CreateObject("WScript.Shell") > "%TEMP%\portfolio_startup.vbs"
echo WshShell.Run """%BATCH_PATH%""", 0, False >> "%TEMP%\portfolio_startup.vbs"

REM Create shortcut in Startup folder
echo Creating startup shortcut...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Portfolio Dashboard.lnk'); $Shortcut.TargetPath = 'wscript.exe'; $Shortcut.Arguments = '%TEMP%\portfolio_startup.vbs'; $Shortcut.WorkingDirectory = '%CURRENT_DIR%'; $Shortcut.Description = 'Portfolio Dashboard Auto-Start'; $Shortcut.Save()"

if errorlevel 1 (
    echo Error: Failed to create startup shortcut
    echo Please run this script as Administrator
    pause
    exit /b 1
)

echo.
echo ✅ Auto-start setup complete!
echo.
echo The Portfolio Dashboard will now start automatically when you log in.
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
