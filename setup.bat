@echo off
echo ========================================
echo Portfolio Dashboard Complete Setup
echo ========================================
echo.
echo This will set up:
echo 1. Auto-start server (no browser) with update checking
echo 2. Scheduled data scraping at 10:30, 13:00, and 17:30
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause >nul

echo.
echo ========================================
echo Step 1: Setting up Auto-Start (Server Only)
echo ========================================
echo.

REM Get the current directory
set "CURRENT_DIR=%~dp0"
set "BATCH_PATH=%CURRENT_DIR%start.bat"

REM Verify the start.bat file exists
if not exist "%BATCH_PATH%" (
    echo ❌ Error: start.bat not found at %BATCH_PATH%
    echo Please ensure start.bat exists in the same directory as setup.bat
    pause
    exit /b 1
)

echo ✅ Found start.bat at: %BATCH_PATH%

REM Create a permanent VBS script in the project directory instead of TEMP
set "VBS_PATH=%CURRENT_DIR%portfolio_startup_server.vbs"
echo Creating VBS script at: %VBS_PATH%

echo Set WshShell = CreateObject("WScript.Shell") > "%VBS_PATH%"
echo WshShell.Run """%BATCH_PATH%""", 0, False >> "%VBS_PATH%"

if not exist "%VBS_PATH%" (
    echo ❌ Failed to create VBS script
    pause
    exit /b 1
)

echo ✅ VBS script created successfully

REM Get the startup folder path with multiple fallback methods
set "STARTUP_FOLDER="

REM Method 1: Try registry query
for /f "tokens=2*" %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Startup 2^>nul') do set "STARTUP_FOLDER=%%b"

REM Method 2: If registry failed, try environment variable
if not defined STARTUP_FOLDER (
    set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
)

REM Method 3: If still not found, try common location
if not defined STARTUP_FOLDER (
    set "STARTUP_FOLDER=%USERPROFILE%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"
)

REM Verify startup folder exists
if not exist "%STARTUP_FOLDER%" (
    echo ❌ Error: Startup folder not found at: %STARTUP_FOLDER%
    echo Please check your Windows startup folder location
    pause
    exit /b 1
)

echo ✅ Found startup folder at: %STARTUP_FOLDER%

REM Create shortcut in Startup folder with better error handling
echo Creating startup shortcut...
powershell -Command "try { $WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTUP_FOLDER%\Portfolio Dashboard Server.lnk'); $Shortcut.TargetPath = 'wscript.exe'; $Shortcut.Arguments = '%VBS_PATH%'; $Shortcut.WorkingDirectory = '%CURRENT_DIR%'; $Shortcut.Description = 'Portfolio Dashboard Server Auto-Start (No Browser)'; $Shortcut.Save(); Write-Host '✅ Auto-start shortcut created successfully' } catch { Write-Host '❌ Error creating shortcut: ' + $_.Exception.Message; exit 1 }"

if errorlevel 1 (
    echo ❌ Auto-start setup failed
    echo.
    echo Troubleshooting steps:
    echo 1. Run this script as Administrator
    echo 2. Check if PowerShell execution policy allows script execution
    echo 3. Verify the startup folder is writable
    echo.
    echo Press any key to continue with scheduled tasks setup...
    pause >nul
) else (
    echo ✅ Auto-start setup completed successfully
)

echo.
echo ========================================
echo Step 2: Setting up Scheduled Scraping
echo ========================================
echo.

REM Configuration for scheduled tasks
set TASK_NAME_PREFIX=SET_Scraper
set SCRIPT_PATH=%CURRENT_DIR%run_scheduled_scrape.bat

REM Verify the scheduled script exists
if not exist "%SCRIPT_PATH%" (
    echo ❌ Error: run_scheduled_scrape.bat not found at %SCRIPT_PATH%
    echo Please ensure run_scheduled_scrape.bat exists in the same directory
    pause
    exit /b 1
)

echo ✅ Found scheduled script at: %SCRIPT_PATH%

REM Delete existing tasks if present
echo Cleaning up existing scheduled tasks...
schtasks /Query /TN %TASK_NAME_PREFIX%_1030 >NUL 2>&1
if %ERRORLEVEL%==0 (
    schtasks /Delete /TN %TASK_NAME_PREFIX%_1030 /F >NUL 2>&1
    echo Deleted existing 10:30 task
)

schtasks /Query /TN %TASK_NAME_PREFIX%_1300 >NUL 2>&1
if %ERRORLEVEL%==0 (
    schtasks /Delete /TN %TASK_NAME_PREFIX%_1300 /F >NUL 2>&1
    echo Deleted existing 13:00 task
)

schtasks /Query /TN %TASK_NAME_PREFIX%_1730 >NUL 2>&1
if %ERRORLEVEL%==0 (
    schtasks /Delete /TN %TASK_NAME_PREFIX%_1730 /F >NUL 2>&1
    echo Deleted existing 17:30 task
)

echo.
echo Creating scheduled tasks...

REM Create 10:30 AM task (Weekdays only)
echo Creating 10:30 AM task...
schtasks /Create ^
  /TN %TASK_NAME_PREFIX%_1030 ^
  /TR "\"%SCRIPT_PATH%\"" ^
  /SC WEEKLY ^
  /D MON,TUE,WED,THU,FRI ^
  /ST 10:30 ^
  /RL LIMITED >NUL 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to create 10:30 AM task
    set "TASK_ERROR=1"
) else (
    echo ✅ 10:30 AM task created successfully
)

REM Create 13:00 PM task (Weekdays only)
echo Creating 13:00 PM task...
schtasks /Create ^
  /TN %TASK_NAME_PREFIX%_1300 ^
  /TR "\"%SCRIPT_PATH%\"" ^
  /SC WEEKLY ^
  /D MON,TUE,WED,THU,FRI ^
  /ST 13:00 ^
  /RL LIMITED >NUL 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to create 13:00 PM task
    set "TASK_ERROR=1"
) else (
    echo ✅ 13:00 PM task created successfully
)

REM Create 17:30 PM task (Weekdays only)
echo Creating 17:30 PM task...
schtasks /Create ^
  /TN %TASK_NAME_PREFIX%_1730 ^
  /TR "\"%SCRIPT_PATH%\"" ^
  /SC WEEKLY ^
  /D MON,TUE,WED,THU,FRI ^
  /ST 17:30 ^
  /RL LIMITED >NUL 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to create 17:30 PM task
    set "TASK_ERROR=1"
) else (
    echo ✅ 17:30 PM task created successfully
)

echo.
echo ========================================
echo Setup Summary
echo ========================================
echo.

if defined TASK_ERROR (
    echo ⚠️  Setup completed with some errors
    echo.
    echo Auto-start: ✅ Ready
    echo Scheduled tasks: ❌ Some tasks failed to create
    echo.
    echo To fix scheduled tasks, run as Administrator:
    echo - Right-click this script and "Run as Administrator"
    echo.
) else (
    echo ✅ Complete setup successful!
    echo.
    echo Auto-start: ✅ Ready
    echo Scheduled tasks: ✅ Ready
    echo.
)

echo ========================================
echo What's been set up:
echo ========================================
echo.
echo 🚀 Auto-Start (Server Only):
echo - Server will start automatically on login
echo - No browser will open automatically
echo - Git updates will be checked automatically
echo - VBS script location: %VBS_PATH%
echo - Shortcut location: %STARTUP_FOLDER%\Portfolio Dashboard Server.lnk
echo.
echo ⏰ Scheduled Data Scraping:
echo - 10:30 AM (Monday-Friday)
echo - 13:00 PM (Monday-Friday)
echo - 17:30 PM (Monday-Friday)
echo.
echo 📊 Manual Controls:
echo - Start server: Double-click start.bat
echo - Server manager: Double-click server_manager.bat
echo - Git updates: Double-click git_update.bat
echo.
echo 🔧 Management:
echo - View tasks: Press Win+R, type "taskschd.msc"
echo - Disable auto-start: Delete "Portfolio Dashboard Server.lnk" from startup folder
echo - Remove scheduled tasks: Run the delete commands shown below
echo.
echo 🗑️  To remove everything:
echo - Auto-start: Delete shortcut from startup folder
echo - VBS script: Delete %VBS_PATH%
echo - Scheduled tasks: 
echo   schtasks /Delete /TN SET_Scraper_1030 /F
echo   schtasks /Delete /TN SET_Scraper_1300 /F
echo   schtasks /Delete /TN SET_Scraper_1730 /F
echo.
echo ========================================
echo Setup complete! Press any key to exit...
pause >nul

