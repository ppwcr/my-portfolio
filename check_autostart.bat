@echo off
echo Portfolio Dashboard Auto-Start Diagnostic Tool
echo =============================================
echo.

REM Get the current directory
set "CURRENT_DIR=%~dp0"
set "BATCH_PATH=%CURRENT_DIR%start.bat"

REM Get the startup folder path
for /f "tokens=2*" %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Startup 2^>nul') do set "STARTUP_FOLDER=%%b"

echo Checking configuration...
echo.

echo 1. Current Directory: %CURRENT_DIR%
echo 2. Batch File Path: %BATCH_PATH%
echo 3. Startup Folder: %STARTUP_FOLDER%
echo.

REM Check if start.bat exists
if exist "%BATCH_PATH%" (
    echo ✅ start.bat found
) else (
    echo ❌ start.bat NOT FOUND
    echo Please make sure you're running this from the correct directory
    pause
    exit /b 1
)

REM Check if startup folder exists
if exist "%STARTUP_FOLDER%" (
    echo ✅ Startup folder found
) else (
    echo ❌ Startup folder NOT FOUND
    echo This might be a Windows configuration issue
    pause
    exit /b 1
)

REM Check for existing shortcuts
echo.
echo Checking for existing shortcuts...
if exist "%STARTUP_FOLDER%\Portfolio Dashboard.lnk" (
    echo ✅ Found: Portfolio Dashboard.lnk
) else (
    echo ❌ NOT FOUND: Portfolio Dashboard.lnk
    echo Auto-start is not configured
)

if exist "%STARTUP_FOLDER%\Portfolio Dashboard.bat" (
    echo ✅ Found: Portfolio Dashboard.bat
) else (
    echo ❌ NOT FOUND: Portfolio Dashboard.bat
)

echo.
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python NOT FOUND
    echo Please install Python 3.8+ and add it to PATH
) else (
    echo ✅ Python found
    python --version
)

echo.
echo Checking dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo ❌ FastAPI NOT FOUND
    echo Please run: pip install -r requirements.txt
) else (
    echo ✅ FastAPI found
)

echo.
echo =============================================
echo DIAGNOSTIC COMPLETE
echo =============================================
echo.

echo If auto-start is not working:
echo 1. Make sure you ran the setup script as Administrator
echo 2. Check if the shortcut exists in startup folder
echo 3. Try the simple setup: setup_simple_autostart.bat
echo 4. Check Windows Event Viewer for errors
echo.

echo To manually test:
echo 1. Double-click start.bat
echo 2. Check if the application starts
echo 3. Check if browser opens automatically
echo.

pause
