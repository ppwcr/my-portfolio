@echo off
echo ========================================
echo Portfolio Dashboard Auto-Start Fix
echo ========================================
echo.
echo This script will fix common auto-start issues by recreating
echo the VBS script and startup shortcut.
echo.

set "CURRENT_DIR=%~dp0"

echo ========================================
echo Step 1: Recreating VBS Script
echo ========================================

REM Create the VBS script
set "VBS_PATH=%CURRENT_DIR%portfolio_startup_server.vbs"
set "BATCH_PATH=%CURRENT_DIR%start.bat"

echo Creating VBS script at: %VBS_PATH%
echo Set WshShell = CreateObject("WScript.Shell") > "%VBS_PATH%"
echo WshShell.Run """%BATCH_PATH%""", 0, False >> "%VBS_PATH%"

if exist "%VBS_PATH%" (
    echo ✅ VBS script created successfully
) else (
    echo ❌ Failed to create VBS script
    pause
    exit /b 1
)

echo.
echo ========================================
echo Step 2: Finding Startup Folder
echo ========================================

REM Find startup folder
set "STARTUP_FOLDER="

REM Method 1: Registry query
for /f "tokens=2*" %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Startup 2^>nul') do set "STARTUP_FOLDER=%%b"

REM Method 2: If registry failed, try environment variable
if not defined STARTUP_FOLDER (
    set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
)

REM Method 3: If still not found, try common location
if not defined STARTUP_FOLDER (
    set "STARTUP_FOLDER=%USERPROFILE%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"
)

if not exist "%STARTUP_FOLDER%" (
    echo ❌ Error: Startup folder not found
    echo Please check your Windows startup folder location
    pause
    exit /b 1
)

echo ✅ Found startup folder at: %STARTUP_FOLDER%

echo.
echo ========================================
echo Step 3: Recreating Startup Shortcut
echo ========================================

REM Remove existing shortcut if it exists
if exist "%STARTUP_FOLDER%\Portfolio Dashboard Server.lnk" (
    del "%STARTUP_FOLDER%\Portfolio Dashboard Server.lnk" >NUL 2>&1
    echo Removed existing shortcut
)

REM Create new shortcut
echo Creating startup shortcut...
powershell -Command "try { $WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTUP_FOLDER%\Portfolio Dashboard Server.lnk'); $Shortcut.TargetPath = 'wscript.exe'; $Shortcut.Arguments = '%VBS_PATH%'; $Shortcut.WorkingDirectory = '%CURRENT_DIR%'; $Shortcut.Description = 'Portfolio Dashboard Server Auto-Start (No Browser)'; $Shortcut.Save(); Write-Host '✅ Startup shortcut created successfully' } catch { Write-Host '❌ Error creating shortcut: ' + $_.Exception.Message; exit 1 }"

if errorlevel 1 (
    echo ❌ Failed to create startup shortcut
    echo.
    echo Troubleshooting:
    echo 1. Run this script as Administrator
    echo 2. Check if PowerShell execution policy allows script execution
    echo 3. Verify the startup folder is writable
    pause
    exit /b 1
) else (
    echo ✅ Startup shortcut created successfully
)

echo.
echo ========================================
echo Auto-Start Fix Complete
echo ========================================
echo.
echo ✅ VBS script: %VBS_PATH%
echo ✅ Startup shortcut: %STARTUP_FOLDER%\Portfolio Dashboard Server.lnk
echo.
echo The auto-start should now work correctly.
echo.
echo To test:
echo 1. Restart your computer
echo 2. Check if the server starts automatically
echo 3. If it doesn't work, run diagnose_autostart.bat to check for other issues
echo.
echo ========================================
echo Fix complete! Press any key to exit...
pause >nul
