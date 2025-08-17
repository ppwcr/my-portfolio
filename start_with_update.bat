@echo off
echo Starting Portfolio Dashboard with Database Update...
echo.
echo This will:
echo 1. Update the database with fresh market data
echo 2. Start the server on http://127.0.0.1:8000
echo 3. Open the dashboard in your browser
echo.
echo Press Ctrl+C to stop the server
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
echo ⏳ Updating database with fresh market data...
echo This may take 1-2 minutes on first run...
echo.

REM Update database first
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --timeout-keep-alive 120 --app-dir . & 
timeout /t 5 /nobreak >nul

REM Call the database update API
curl -X POST http://127.0.0.1:8000/api/save-to-database >nul 2>&1
if errorlevel 1 (
    echo Warning: Database update via API failed, but server will still start
    echo The dashboard will update automatically in the background
)

echo.
echo ✅ Database update initiated
echo.
echo 🚀 Starting server...
echo.
echo Opening browser in 3 seconds...
timeout /t 3 /nobreak >nul

REM Open browser
start "" http://127.0.0.1:8000/portfolio

REM Server should already be running from the background start above
echo.
echo 📊 Portfolio Dashboard is now running!
echo.
echo The database will auto-update every 30 minutes in the background.
echo Close this window or press Ctrl+C to stop the server.
echo.

REM Wait for the background server process
:wait_loop
timeout /t 10 /nobreak >nul
goto wait_loop