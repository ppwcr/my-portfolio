@echo off
setlocal enabledelayedexpansion
echo ========================================
echo Portfolio Dashboard Server Manager
echo ========================================
echo.

REM Change to script directory
cd /d "%~dp0"

:menu
echo Choose an option:
echo.
echo 1. Start server in background
echo 2. Stop server
echo 3. Check server status
echo 4. Restart server
echo 5. View server logs
echo 6. Exit
echo.
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto start_server
if "%choice%"=="2" goto stop_server
if "%choice%"=="3" goto check_status
if "%choice%"=="4" goto restart_server
if "%choice%"=="5" goto view_logs
if "%choice%"=="6" goto exit
echo Invalid choice. Please try again.
echo.
goto menu

:start_server
echo.
echo 🚀 Starting server in background...
echo.

REM Check if server is already running
netstat -an | find "127.0.0.1:8000" | find "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo ⚠️  Server is already running on port 8000
    echo.
    goto menu
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH
    echo.
    goto menu
)

REM Start the server in background using VBScript
echo Set WshShell = CreateObject("WScript.Shell") > "%TEMP%\start_server.vbs"
echo WshShell.Run "uvicorn main:app --reload --host 127.0.0.1 --port 8000", 0, False >> "%TEMP%\start_server.vbs"
wscript "%TEMP%\start_server.vbs"

echo ✅ Server started in background successfully!
echo.
echo Access the dashboard at: http://127.0.0.1:8000/portfolio
echo.
pause
goto menu

:stop_server
echo.
echo 🛑 Stopping server...
echo.

REM Kill Python processes running uvicorn
taskkill /f /im python.exe >nul 2>&1
if errorlevel 1 (
    echo ⚠️  No Python processes found or already stopped
) else (
    echo ✅ Server stopped successfully
)

echo.
pause
goto menu

:check_status
echo.
echo 📊 Checking server status...
echo.

REM Check if port 8000 is listening
netstat -an | find "127.0.0.1:8000" | find "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo ✅ Server is running on http://127.0.0.1:8000
    echo.
    echo Process information:
    netstat -ano | find "127.0.0.1:8000"
) else (
    echo ❌ Server is not running
)

echo.
pause
goto menu

:restart_server
echo.
echo 🔄 Restarting server...
echo.

REM Stop server first
taskkill /f /im python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM Start server again
echo Set WshShell = CreateObject("WScript.Shell") > "%TEMP%\start_server.vbs"
echo WshShell.Run "uvicorn main:app --reload --host 127.0.0.1 --port 8000", 0, False >> "%TEMP%\start_server.vbs"
wscript "%TEMP%\start_server.vbs"

echo ✅ Server restarted successfully!
echo.
pause
goto menu

:view_logs
echo.
echo 📋 Recent log files:
echo.

REM List recent log files
dir /b /o-d scraper_*.log 2>nul | findstr /v "^$" | head -5
if errorlevel 1 (
    echo No log files found
) else (
    echo.
    set /p logfile="Enter log file name to view (or press Enter to skip): "
    if not "!logfile!"=="" (
        if exist "!logfile!" (
            type "!logfile!"
        ) else (
            echo File not found: !logfile!
        )
    )
)

echo.
pause
goto menu

:exit
echo.
echo 👋 Goodbye!
echo.
exit /b 0
