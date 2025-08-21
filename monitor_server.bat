@echo off
setlocal enabledelayedexpansion
echo ========================================
echo Portfolio Dashboard Server Monitor
echo ========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: This script requires administrator privileges
    echo Please right-click and "Run as administrator"
    pause
    exit /b 1
)
echo ✅ Administrator privileges confirmed
echo.

REM Change to script directory
cd /d "%~dp0"
echo 📁 Working directory: %CD%
echo.

:MONITOR_LOOP
cls
echo ========================================
echo Portfolio Dashboard Server Monitor
echo ========================================
echo.
echo Last updated: %date% %time%
echo.

REM Check if server is running
echo 🔍 Server Status:
netstat -an | findstr :8000 >nul 2>&1
if errorlevel 1 (
    echo ❌ Server is NOT running on port 8000
) else (
    echo ✅ Server is running on port 8000
)
echo.

REM Show server processes
echo 🔍 Server Processes:
tasklist /fi "imagename eq python.exe" /fo table | findstr python
echo.

REM Show port 8000 connections
echo 🔍 Port 8000 Connections:
netstat -an | findstr :8000
echo.

REM Show recent activity in _out directory
echo 📁 Recent Data Files:
if exist "_out" (
    dir "_out" /o-d /t:w | findstr /v "Directory" | head -10
) else (
    echo No _out directory found
)
echo.

REM Show scheduled tasks status
echo ⏰ Scheduled Tasks Status:
schtasks /query /tn "PortfolioDashboard_GitUpdate" /fo table 2>nul | findstr "PortfolioDashboard_GitUpdate"
schtasks /query /tn "SET_Scraper_1030" /fo table 2>nul | findstr "SET_Scraper_1030"
schtasks /query /tn "SET_Scraper_1300" /fo table 2>nul | findstr "SET_Scraper_1300"
schtasks /query /tn "SET_Scraper_1730" /fo table 2>nul | findstr "SET_Scraper_1730"
echo.

REM Show auto-start status
echo 🔄 Auto-Start Status:
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "PortfolioDashboard" 2>nul | findstr "PortfolioDashboard"
if errorlevel 1 (
    echo ❌ Auto-start not configured
) else (
    echo ✅ Auto-start configured
)
echo.

REM Show system resources
echo 💻 System Resources:
echo CPU Usage:
wmic cpu get loadpercentage /value | findstr LoadPercentage
echo.
echo Memory Usage:
wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value | findstr Memory
echo.

echo ========================================
echo Monitor Options:
echo ========================================
echo 1. Refresh (wait 5 seconds)
echo 2. Start server manually
echo 3. Stop server
echo 4. View server logs
echo 5. Check git status
echo 6. Exit monitor
echo.
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" (
    echo Refreshing in 5 seconds...
    timeout /t 5 /nobreak >nul
    goto MONITOR_LOOP
) else if "%choice%"=="2" (
    echo Starting server manually...
    start /min python -c "import uvicorn; uvicorn.run('main:app', host='127.0.0.1', port=8000, log_level='info')"
    echo Server started. Refreshing in 3 seconds...
    timeout /t 3 /nobreak >nul
    goto MONITOR_LOOP
) else if "%choice%"=="3" (
    echo Stopping server...
    taskkill /f /im python.exe /fi "WINDOWTITLE eq Portfolio*" >nul 2>&1
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 2^>nul') do (
        taskkill /f /pid %%a >nul 2>&1
    )
    echo Server stopped. Refreshing in 3 seconds...
    timeout /t 3 /nobreak >nul
    goto MONITOR_LOOP
) else if "%choice%"=="4" (
    echo Opening server logs...
    if exist "*.log" (
        start notepad *.log
    ) else (
        echo No log files found
    )
    echo Press any key to continue...
    pause >nul
    goto MONITOR_LOOP
) else if "%choice%"=="5" (
    echo Checking git status...
    git status
    echo.
    echo Press any key to continue...
    pause >nul
    goto MONITOR_LOOP
) else if "%choice%"=="6" (
    echo Exiting monitor...
    exit /b 0
) else (
    echo Invalid choice. Press any key to continue...
    pause >nul
    goto MONITOR_LOOP
)
