@echo off
setlocal enabledelayedexpansion
echo ========================================
echo Portfolio Dashboard Server
echo ========================================
echo.

REM Change to script directory
cd /d "%~dp0"
echo 📁 Working directory: %CD%
echo.

REM Check if Python is installed
echo 🔍 Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)
python --version
echo ✅ Python found
echo.

REM Check if port 8000 is already in use
echo 🔍 Checking if port 8000 is available...
netstat -an | findstr :8000 >nul 2>&1
if not errorlevel 1 (
    echo ⚠️  Port 8000 is already in use
    echo Stopping existing processes on port 8000...
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
        taskkill /f /pid %%a >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
    echo ✅ Port 8000 cleared
) else (
    echo ✅ Port 8000 is available
)
echo.

REM Check and install dependencies
echo 📦 Checking dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Error: Failed to install dependencies
        pause
        exit /b 1
    )
    echo ✅ Dependencies installed
) else (
    echo ✅ Dependencies OK
)
echo.

REM Check if main.py exists
if not exist "main.py" (
    echo ❌ Error: main.py not found in current directory
    echo Current directory: %CD%
    pause
    exit /b 1
)
echo ✅ main.py found
echo.

echo 🚀 Starting Portfolio Dashboard server...
echo 📡 Server will be available at: http://127.0.0.1:8000/portfolio
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the server
uvicorn main:app --reload --host 127.0.0.1 --port 8000

echo.
echo 👋 Server stopped. Press any key to exit...
pause >nul
