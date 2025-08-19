@echo off
setlocal enabledelayedexpansion
echo 🔄 Portfolio Dashboard Update & Restart
echo =====================================
echo.

REM Check for git updates
echo 📡 Checking for updates from repository...
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
                set "UPDATED=1"
            ) else (
                echo ⚠️  Git pull failed, continuing with current version
                set "UPDATED=0"
            )
        ) else (
            echo ✅ Already up to date
            set "UPDATED=0"
        )
    )
) else (
    echo ⚠️  Git fetch failed or not a git repository
    set "UPDATED=0"
)
echo.

REM Stop existing server
echo 🛑 Stopping existing server processes...
taskkill /f /im python.exe /fi "WINDOWTITLE eq Portfolio*" >nul 2>&1
taskkill /f /im uvicorn.exe >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    taskkill /f /pid %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul
echo ✅ Server processes stopped
echo.

REM Check if dependencies need updating (only if code was updated)
if "!UPDATED!"=="1" (
    echo 📦 Checking dependencies...
    pip show fastapi >nul 2>&1
    if errorlevel 1 (
        echo Installing dependencies...
        pip install -r requirements.txt
        if errorlevel 1 (
            echo ⚠️  Failed to install dependencies, but continuing...
        )
    ) else (
        echo ✅ Dependencies OK
    )
    echo.
    
    REM Check playwright
    echo 🎭 Checking Playwright...
    playwright --version >nul 2>&1
    if errorlevel 1 (
        echo Installing Playwright browsers...
        playwright install chromium >nul 2>&1
    ) else (
        echo ✅ Playwright OK
    )
    echo.
)

REM Start the server
echo 🚀 Starting Portfolio Dashboard server...
echo 📡 Server will be available at: http://127.0.0.1:8000/portfolio
echo.
echo Opening browser in 3 seconds...
timeout /t 3 /nobreak >nul

REM Start server in background and open browser
start "" http://127.0.0.1:8000/portfolio
uvicorn main:app --reload --host 127.0.0.1 --port 8000

echo.
echo 👋 Server stopped. Press any key to exit...
pause >nul