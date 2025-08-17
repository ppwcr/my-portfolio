# Portfolio Dashboard Status Checker (PowerShell)
Write-Host "Portfolio Dashboard Status Checker" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Check if server is running
Write-Host "Checking if server is running..." -ForegroundColor Yellow
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/" -TimeoutSec 5 -UseBasicParsing
    Write-Host "✅ Server is running on http://127.0.0.1:8000" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "Testing API endpoints..." -ForegroundColor Yellow
    Write-Host ""
    
    # Test portfolio page
    try {
        $portfolioResponse = Invoke-WebRequest -Uri "http://127.0.0.1:8000/portfolio" -TimeoutSec 5 -UseBasicParsing
        Write-Host "✅ Portfolio page accessible" -ForegroundColor Green
    } catch {
        Write-Host "❌ Portfolio page not accessible" -ForegroundColor Red
    }
    
    # Test API endpoint
    try {
        $apiResponse = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/series/symbol/AOT" -TimeoutSec 5 -UseBasicParsing
        Write-Host "✅ API endpoint accessible" -ForegroundColor Green
    } catch {
        Write-Host "❌ API endpoint not accessible" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "🌐 Open your browser to: http://127.0.0.1:8000/portfolio" -ForegroundColor Cyan
    Write-Host ""
    
} catch {
    Write-Host "❌ Server is NOT running" -ForegroundColor Red
    Write-Host ""
    Write-Host "To start the server:" -ForegroundColor Yellow
    Write-Host "1. Double-click start.bat" -ForegroundColor White
    Write-Host "2. Or run: uvicorn main:app --reload --host 127.0.0.1 --port 8000" -ForegroundColor White
    Write-Host ""
}

# Check for running processes
Write-Host "Checking for running processes..." -ForegroundColor Yellow
Write-Host ""

$uvicornProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -eq "python" }
if ($uvicornProcesses) {
    Write-Host "✅ Found Python processes:" -ForegroundColor Green
    $uvicornProcesses | ForEach-Object { Write-Host "  PID: $($_.Id), Memory: $([math]::Round($_.WorkingSet64/1MB, 2)) MB" -ForegroundColor White }
} else {
    Write-Host "❌ No Python processes found" -ForegroundColor Red
}

Write-Host ""
Write-Host "Checking port 8000..." -ForegroundColor Yellow
Write-Host ""

$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port8000) {
    Write-Host "✅ Port 8000 is in use:" -ForegroundColor Green
    $port8000 | ForEach-Object { Write-Host "  Local: $($_.LocalAddress):$($_.LocalPort), State: $($_.State)" -ForegroundColor White }
} else {
    Write-Host "❌ Port 8000 is not in use" -ForegroundColor Red
}

Write-Host ""
Write-Host "=================================" -ForegroundColor Cyan
Write-Host "STATUS CHECK COMPLETE" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "If the server is not running:" -ForegroundColor Yellow
Write-Host "1. Double-click start.bat" -ForegroundColor White
Write-Host "2. Check for error messages in the terminal" -ForegroundColor White
Write-Host "3. Make sure Python and dependencies are installed" -ForegroundColor White
Write-Host "4. Check if port 8000 is available" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to continue"
