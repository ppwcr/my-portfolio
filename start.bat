@echo off
echo Starting Portfolio Dashboard Server with Auto-Scraper...
echo.
echo This will start:
echo - Web server on http://0.0.0.0:8000 (accessible from network)
echo - Auto-scraper that runs every 10 minutes (sector + SET index)
echo - Scheduled scraper that runs full updates at 10:30, 13:00, 17:30 (weekdays)
echo Press Ctrl+C to stop all services
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if requirements are installed
echo Checking dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Check if auto-scraper dependencies are installed
pip show schedule >nul 2>&1
if errorlevel 1 (
    echo Installing auto-scraper dependencies...
    pip install schedule psutil
    if errorlevel 1 (
        echo Error: Failed to install auto-scraper dependencies
        pause
        exit /b 1
    )
)

REM Check if playwright is installed
echo Checking Playwright...
playwright --version >nul 2>&1
if errorlevel 1 (
    echo Installing Playwright browsers...
    playwright install
    if errorlevel 1 (
        echo Warning: Playwright installation failed, but continuing...
    )
)

echo.
echo Starting server...
echo.
REM Get the local IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set LOCAL_IP=%%a
    goto :found_ip
)
:found_ip
set LOCAL_IP=%LOCAL_IP: =%

echo.
echo ========================================
echo Server will be accessible at:
echo Local:  http://127.0.0.1:8000
echo Network: http://%LOCAL_IP%:8000
echo.
echo Auto-Scraper will:
echo - Scrape sector and SET index data every 10 minutes
echo - Clean up old data automatically
echo - Update web interface when new data arrives
echo.
echo Scheduled Scraper will:
echo - Run full updates (all data sources) at 10:30, 13:00, 17:30
echo - Weekdays only (Monday-Friday)
echo - Update investor, NVDR, and short sales data
echo ========================================
echo.

echo Starting auto-scraper in background...
start /min python auto_scraper.py

echo Starting scheduled scraper in background...
start /min python scheduled_scraper.py

echo Opening browser in 3 seconds...
timeout /t 3 /nobreak >nul

REM Start the server in background and open browser
start "" http://127.0.0.1:8000/portfolio
uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause

