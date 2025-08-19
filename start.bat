@echo off
setlocal enabledelayedexpansion
echo Starting Portfolio Dashboard Server...
echo.
echo This will start the server on http://127.0.0.1:8000
echo Press Ctrl+C to stop the server
echo.

REM Check for git updates
echo 🔄 Checking for git updates...
git fetch >nul 2>&1
if not errorlevel 1 (
    for /f %%i in ('git rev-list HEAD...origin/main --count 2^>nul') do set "UPDATE_COUNT=%%i"
    if defined UPDATE_COUNT (
        if not "!UPDATE_COUNT!"=="0" (
            echo 📥 Found !UPDATE_COUNT! update(s) available
            echo ⬇️  Pulling latest changes...
            git pull origin main
            if not errorlevel 1 (
                echo ✅ Successfully updated to latest version
            ) else (
                echo ⚠️  Git pull failed, continuing with current version
            )
        ) else (
            echo ✅ Already up to date
        )
    )
) else (
    echo ⚠️  Git fetch failed or not a git repository, continuing...
)
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
echo Starting server...
echo.
echo Opening browser in 3 seconds...
timeout /t 3 /nobreak >nul

REM Start the server in background and open browser
start "" http://127.0.0.1:8000/portfolio
uvicorn main:app --reload --host 127.0.0.1 --port 8000

pause

