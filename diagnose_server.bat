@echo off
echo ========================================
echo Server Diagnostic Tool
echo ========================================
echo.

REM Change to script directory
cd /d "%~dp0"
echo 📁 Working directory: %CD%
echo.

echo 🔍 System Information:
echo - OS: %OS%
echo - Python Path: 
where python
echo.

echo 🔍 Python Version:
python --version
echo.

echo 🔍 Checking main.py:
if exist "main.py" (
    echo ✅ main.py exists
    echo - File size: 
    dir main.py | findstr main.py
) else (
    echo ❌ main.py not found
)
echo.

echo 🔍 Checking requirements.txt:
if exist "requirements.txt" (
    echo ✅ requirements.txt exists
) else (
    echo ❌ requirements.txt not found
)
echo.

echo 🔍 Checking key dependencies:
echo - FastAPI:
pip show fastapi 2>nul | findstr Version
echo - Uvicorn:
pip show uvicorn 2>nul | findstr Version
echo - Pandas:
pip show pandas 2>nul | findstr Version
echo.

echo 🔍 Port 8000 status:
netstat -an | findstr :8000
if errorlevel 1 (
    echo ✅ Port 8000 is free
) else (
    echo ⚠️  Port 8000 is in use
)
echo.

echo 🔍 Testing server startup (5 second test):
echo Starting server for 5 seconds...
timeout /t 2 /nobreak >nul
start /b python -c "import uvicorn; uvicorn.run('main:app', host='127.0.0.1', port=8000, log_level='error')" >nul 2>&1
timeout /t 5 /nobreak >nul
taskkill /f /im python.exe >nul 2>&1
echo ✅ Server test completed
echo.

echo 🔍 Checking if server responded:
curl -s http://127.0.0.1:8000/docs >nul 2>&1
if errorlevel 1 (
    echo ❌ Server did not respond to test request
) else (
    echo ✅ Server responded successfully
)
echo.

echo ========================================
echo Diagnostic Complete
echo ========================================
pause
