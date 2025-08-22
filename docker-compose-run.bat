@echo off
echo ========================================
echo SET Portfolio API - Docker Compose
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

REM Check if docker-compose is available
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Compose is not available!
    echo Please ensure Docker Desktop includes Docker Compose.
    pause
    exit /b 1
)

echo Docker and Docker Compose are available.

REM Create necessary directories if they don't exist
if not exist "_out" mkdir "_out"
if not exist "out_set_sectors" mkdir "out_set_sectors"

echo.
echo Starting the application with Docker Compose...
echo The API will be available at: http://localhost:8000
echo.
echo Commands:
echo   - Press Ctrl+C to stop
echo   - Run 'docker-compose up -d' for background mode
echo   - Run 'docker-compose down' to stop and remove containers
echo   - Run 'docker-compose logs -f' to view logs
echo.

docker-compose up

pause
