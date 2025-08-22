@echo off
echo ========================================
echo SET Portfolio API - Docker Build & Run
echo ========================================
echo.

REM Check if Docker is installed and running
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not running!
    echo Please install Docker Desktop for Windows and start it.
    pause
    exit /b 1
)

echo Docker is available. Proceeding with build...

REM Build the Docker image
echo.
echo Building Docker image...
docker build -t set-portfolio-api .

if errorlevel 1 (
    echo ERROR: Docker build failed!
    pause
    exit /b 1
)

echo.
echo Docker image built successfully!

REM Create necessary directories if they don't exist
if not exist "_out" mkdir "_out"
if not exist "out_set_sectors" mkdir "out_set_sectors"

REM Run the container
echo.
echo Starting the application...
echo The API will be available at: http://localhost:8000
echo.
echo Press Ctrl+C to stop the container
echo.

docker run --rm -p 8000:8000 -v "%cd%\_out:/app/_out" -v "%cd%\out_set_sectors:/app/out_set_sectors" set-portfolio-api

pause
