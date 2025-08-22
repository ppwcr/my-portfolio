@echo off
echo Portfolio Dashboard Status Checker
echo =================================
echo.

echo Checking if server is running...
echo.

REM Try to connect to the server
curl -s http://127.0.0.1:8000/ >nul 2>&1
if errorlevel 1 (
    echo ❌ Server is NOT running
    echo.
    echo To start the server:
    echo 1. Double-click start.bat
    echo 2. Or run: uvicorn main:app --reload --host 127.0.0.1 --port 8000
    echo.
) else (
    echo ✅ Server is running on http://127.0.0.1:8000
    echo.
    echo Testing API endpoints...
    echo.
    
    REM Test the portfolio page
    curl -s http://127.0.0.1:8000/portfolio >nul 2>&1
    if errorlevel 1 (
        echo ❌ Portfolio page not accessible
    ) else (
        echo ✅ Portfolio page accessible
    )
    
    REM Test the API endpoint
    curl -s http://127.0.0.1:8000/api/series/symbol/AOT >nul 2>&1
    if errorlevel 1 (
        echo ❌ API endpoint not accessible
    ) else (
        echo ✅ API endpoint accessible
    )
    
    echo.
    echo 🌐 Open your browser to: http://127.0.0.1:8000/portfolio
    echo.
)

echo Checking for running processes...
echo.

REM Check for uvicorn processes
tasklist /FI "IMAGENAME eq python.exe" /FO CSV | findstr /I "uvicorn" >nul 2>&1
if errorlevel 1 (
    echo ❌ No uvicorn processes found
) else (
    echo ✅ Found uvicorn processes:
    tasklist /FI "IMAGENAME eq python.exe" /FO CSV | findstr /I "uvicorn"
)

echo.
echo Checking port 8000...
echo.

REM Check if port 8000 is in use
netstat -an | findstr ":8000" >nul 2>&1
if errorlevel 1 (
    echo ❌ Port 8000 is not in use
) else (
    echo ✅ Port 8000 is in use:
    netstat -an | findstr ":8000"
)

echo.
echo =================================
echo STATUS CHECK COMPLETE
echo =================================
echo.

echo If the server is not running:
echo 1. Double-click start.bat
echo 2. Check for error messages in the terminal
echo 3. Make sure Python and dependencies are installed
echo 4. Check if port 8000 is available
echo.

pause
