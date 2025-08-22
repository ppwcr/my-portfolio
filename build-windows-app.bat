@echo off
echo ========================================
echo SET Portfolio Manager - Windows Build
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

REM Check if npm is available
npm --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm is not available!
    pause
    exit /b 1
)

echo Node.js and npm are available.
echo.

REM Navigate to electron-app directory
cd electron-app

REM Install dependencies
echo Installing dependencies...
npm install
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo Dependencies installed successfully!
echo.

REM Ask user for build type
echo Choose build type:
echo 1. Portable executable (.exe)
echo 2. Installer (.exe)
echo 3. Both
echo.

set /p BUILD_TYPE="Enter your choice (1-3): "

if "%BUILD_TYPE%"=="1" (
    echo.
    echo Building portable executable...
    npm run build-win-portable
) else if "%BUILD_TYPE%"=="2" (
    echo.
    echo Building installer...
    npm run build-win-installer
) else if "%BUILD_TYPE%"=="3" (
    echo.
    echo Building both portable and installer...
    npm run build-win
) else (
    echo ERROR: Invalid choice!
    pause
    exit /b 1
)

if errorlevel 1 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Output files are in: electron-app\dist-windows\
echo.

REM List output files
if exist "dist-windows" (
    echo Output files:
    dir /b dist-windows\
    echo.
)

echo You can now run the application by:
echo 1. Double-clicking the .exe file in dist-windows\
echo 2. Or running: npm start (for development)
echo.

pause
