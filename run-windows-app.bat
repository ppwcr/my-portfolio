@echo off
echo ========================================
echo SET Portfolio Manager - Development Mode
echo ========================================
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Node.js and Python are available.
echo.

REM Navigate to electron-app directory
cd electron-app

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies!
        pause
        exit /b 1
    )
)

echo.
echo Starting SET Portfolio Manager in development mode...
echo.
echo The application will:
echo 1. Start the Python backend server
echo 2. Open the Electron window
echo 3. Load your FastAPI application
echo.
echo Press Ctrl+C to stop the application
echo.

REM Start the Electron app in development mode
npm run dev

echo.
echo Application stopped.
pause
