# SET Portfolio Manager - Windows Build Script (PowerShell)
# Run this script in PowerShell to build the Windows desktop application

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SET Portfolio Manager - Windows Build" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Node.js is installed
try {
    $nodeVersion = node --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Node.js not found"
    }
    Write-Host "✓ Node.js is available: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Node.js is not installed!" -ForegroundColor Red
    Write-Host "Please install Node.js from https://nodejs.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if npm is available
try {
    $npmVersion = npm --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "npm not found"
    }
    Write-Host "✓ npm is available: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: npm is not available!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Navigate to electron-app directory
$electronAppPath = Join-Path $PSScriptRoot "electron-app"
if (-not (Test-Path $electronAppPath)) {
    Write-Host "❌ ERROR: electron-app directory not found!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Set-Location $electronAppPath
Write-Host "📁 Working directory: $electronAppPath" -ForegroundColor Yellow

# Install dependencies
Write-Host ""
Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
npm install

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ERROR: Failed to install dependencies!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✓ Dependencies installed successfully!" -ForegroundColor Green
Write-Host ""

# Ask user for build type
Write-Host "Choose build type:" -ForegroundColor Yellow
Write-Host "1. Portable executable (.exe)" -ForegroundColor White
Write-Host "2. Installer (.exe)" -ForegroundColor White
Write-Host "3. Both" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1-3)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "🔨 Building portable executable..." -ForegroundColor Cyan
        npm run build-win-portable
    }
    "2" {
        Write-Host ""
        Write-Host "🔨 Building installer..." -ForegroundColor Cyan
        npm run build-win-installer
    }
    "3" {
        Write-Host ""
        Write-Host "🔨 Building both portable and installer..." -ForegroundColor Cyan
        npm run build-win
    }
    default {
        Write-Host "❌ Invalid choice. Please run the script again." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ERROR: Build failed!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Build completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

$distPath = Join-Path $electronAppPath "dist-windows"
if (Test-Path $distPath) {
    Write-Host "📁 Output files are in: $distPath" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "📋 Output files:" -ForegroundColor Cyan
    Get-ChildItem $distPath | ForEach-Object {
        Write-Host "   $($_.Name)" -ForegroundColor White
    }
    Write-Host ""
}

Write-Host "🎉 You can now run the application by:" -ForegroundColor Green
Write-Host "   1. Double-clicking the .exe file in dist-windows\" -ForegroundColor White
Write-Host "   2. Or running: npm start (for development)" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to exit"
