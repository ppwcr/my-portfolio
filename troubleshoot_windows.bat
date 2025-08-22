@echo off
echo ========================================
echo Portfolio Dashboard - Windows Troubleshooter
echo ========================================
echo.

REM Check current directory
echo Current directory: %CD%
echo.

REM Check if we're in the correct directory
if not exist "main.py" (
    echo ❌ ERROR: main.py not found!
    echo.
    echo Please ensure you are running this script from the portfolio project directory.
    echo The directory should contain: main.py, auto_scraper.py, scheduled_scraper.py
    echo.
    echo If you downloaded/cloned the project, navigate to the project folder first.
    echo Example: cd C:\path\to\my-portfolio
    echo.
    pause
    exit /b 1
)

echo ✅ main.py found
echo ✅ auto_scraper.py found
echo ✅ scheduled_scraper.py found
echo.

REM Check Python installation
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python not found in PATH
    echo.
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python version: %PYTHON_VERSION%
echo.

REM Check required packages
echo Checking required packages...
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: FastAPI not installed
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo ✅ FastAPI installed
)

python -c "import schedule" >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: schedule package not installed
    echo Installing auto-scraper dependencies...
    pip install schedule psutil
    if errorlevel 1 (
        echo ❌ Failed to install auto-scraper dependencies
        pause
        exit /b 1
    )
) else (
    echo ✅ schedule package installed
)

python -c "import psutil" >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: psutil package not installed
    echo Installing auto-scraper dependencies...
    pip install schedule psutil
    if errorlevel 1 (
        echo ❌ Failed to install auto-scraper dependencies
        pause
        exit /b 1
    )
) else (
    echo ✅ psutil package installed
)

echo.

REM Check Playwright
echo Checking Playwright...
playwright --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  WARNING: Playwright not installed
    echo Installing Playwright browsers...
    playwright install
    if errorlevel 1 (
        echo ⚠️  Playwright installation failed, but continuing...
    ) else (
        echo ✅ Playwright installed
    )
) else (
    echo ✅ Playwright installed
)

echo.

REM Check environment variables
echo Checking environment variables...
if not defined SUPABASE_URL (
    echo ❌ ERROR: SUPABASE_URL environment variable not set
    echo Please create a .env file with your Supabase credentials
    echo Example .env file:
    echo SUPABASE_URL=your_supabase_url
    echo SUPABASE_SERVICE_KEY=your_supabase_key
    echo.
    pause
    exit /b 1
) else (
    echo ✅ SUPABASE_URL found
)

if not defined SUPABASE_SERVICE_KEY (
    echo ❌ ERROR: SUPABASE_SERVICE_KEY environment variable not set
    echo Please create a .env file with your Supabase credentials
    echo.
    pause
    exit /b 1
) else (
    echo ✅ SUPABASE_SERVICE_KEY found
)

echo.

REM Test database connection
echo Testing database connection...
python -c "from supabase_database import SupabaseDatabase; db = SupabaseDatabase(); print('✅ Database connection successful')" >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Database connection failed
    echo Please check your Supabase credentials and internet connection
    echo.
    pause
    exit /b 1
) else (
    echo ✅ Database connection successful
)

echo.
echo ========================================
echo ✅ All checks passed! System is ready.
echo ========================================
echo.
echo You can now run: start.bat
echo.
pause
