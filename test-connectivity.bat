@echo off
echo ========================================
echo SET Portfolio API - Connectivity Test
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python and try again.
    pause
    exit /b 1
)

REM Check if requests module is available
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo Installing requests module...
    pip install requests
    if errorlevel 1 (
        echo ERROR: Failed to install requests module!
        pause
        exit /b 1
    )
)

echo Python and requests module are available.
echo.

REM Get Mac IP address
if "%~1"=="" (
    set /p MAC_IP="Enter Mac's IP address (e.g., 192.168.1.100): "
) else (
    set MAC_IP=%~1
)

if "%MAC_IP%"=="" (
    echo ERROR: No IP address provided!
    pause
    exit /b 1
)

echo.
echo Testing connectivity to Mac at: %MAC_IP%
echo.

REM Run the connectivity test
python test-connectivity.py %MAC_IP%

echo.
echo Test completed!
pause
