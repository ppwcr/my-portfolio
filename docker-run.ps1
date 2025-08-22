# SET Portfolio API - Docker PowerShell Script
# Run this script in PowerShell to build and run the application

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SET Portfolio API - Docker Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed and running
try {
    $dockerVersion = docker --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker not found"
    }
    Write-Host "✓ Docker is available: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Docker is not installed or not running!" -ForegroundColor Red
    Write-Host "Please install Docker Desktop for Windows and start it." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if docker-compose is available
try {
    $composeVersion = docker-compose --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose not found"
    }
    Write-Host "✓ Docker Compose is available: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠️  WARNING: Docker Compose not found, will use Docker directly" -ForegroundColor Yellow
}

Write-Host ""

# Create necessary directories
$directories = @("_out", "out_set_sectors")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "✓ Created directory: $dir" -ForegroundColor Green
    }
}

# Ask user for deployment method
Write-Host "Choose deployment method:" -ForegroundColor Yellow
Write-Host "1. Docker Compose (Recommended)" -ForegroundColor White
Write-Host "2. Docker directly" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1 or 2)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Building and starting with Docker Compose..." -ForegroundColor Cyan
        
        # Build and start with docker-compose
        docker-compose up --build
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Docker Compose failed!" -ForegroundColor Red
            Read-Host "Press Enter to exit"
            exit 1
        }
    }
    "2" {
        Write-Host ""
        Write-Host "Building Docker image..." -ForegroundColor Cyan
        docker build -t set-portfolio-api .
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Docker build failed!" -ForegroundColor Red
            Read-Host "Press Enter to exit"
            exit 1
        }
        
        Write-Host "✓ Docker image built successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Starting the application..." -ForegroundColor Cyan
        Write-Host "The API will be available at: http://localhost:8000" -ForegroundColor Yellow
        Write-Host "Press Ctrl+C to stop the container" -ForegroundColor Yellow
        Write-Host ""
        
        # Get current directory for volume mounting
        $currentDir = Get-Location
        docker run --rm -p 8000:8000 -v "${currentDir}\_out:/app/_out" -v "${currentDir}\out_set_sectors:/app/out_set_sectors" set-portfolio-api
    }
    default {
        Write-Host "❌ Invalid choice. Please run the script again." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host ""
Write-Host "Application stopped." -ForegroundColor Yellow
Read-Host "Press Enter to exit"
