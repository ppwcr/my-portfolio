@echo off
echo ========================================
echo Git Update Script
echo ========================================
echo.
echo This script will check for git updates and pull latest changes.
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if git is available
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Git is not installed or not in PATH
    echo Please install Git and try again
    pause
    exit /b 1
)

echo 🔄 Checking for git updates...
echo.

REM Check current branch
for /f "tokens=*" %%i in ('git branch --show-current 2^>nul') do set "CURRENT_BRANCH=%%i"
echo 📍 Current branch: %CURRENT_BRANCH%

REM Check if there are any uncommitted changes
git diff --quiet HEAD
if errorlevel 1 (
    echo ⚠️  Warning: You have uncommitted changes
    echo.
    echo Current changes:
    git status --porcelain
    echo.
    set /p choice="Do you want to stash changes before updating? (y/n): "
    if /i "%choice%"=="y" (
        echo 📦 Stashing changes...
        git stash push -m "Auto-stash before git update"
        if errorlevel 1 (
            echo ❌ Failed to stash changes
            pause
            exit /b 1
        )
        echo ✅ Changes stashed successfully
        set "STASHED=1"
    ) else (
        echo ❌ Update cancelled due to uncommitted changes
        echo Please commit or stash your changes first
        pause
        exit /b 1
    )
)

echo.
echo 🔍 Fetching latest changes from remote...
git fetch origin
if errorlevel 1 (
    echo ❌ Failed to fetch from remote
    pause
    exit /b 1
)

REM Check if there are updates available
for /f %%i in ('git rev-list HEAD...origin/main --count 2^>nul') do set "BEHIND_COUNT=%%i"
for /f %%i in ('git rev-list origin/main...HEAD --count 2^>nul') do set "AHEAD_COUNT=%%i"

if "%BEHIND_COUNT%"=="" set "BEHIND_COUNT=0"
if "%AHEAD_COUNT%"=="" set "AHEAD_COUNT=0"

echo.
echo 📊 Update Status:
echo - Behind remote: %BEHIND_COUNT% commits
echo - Ahead of remote: %AHEAD_COUNT% commits

if "%BEHIND_COUNT%"=="0" (
    echo.
    echo ✅ Already up to date!
    echo No updates available.
) else (
    echo.
    echo 📥 Updates available! Pulling latest changes...
    
    REM Show what will be updated
    echo.
    echo 📋 Recent commits to be pulled:
    git log --oneline HEAD..origin/main
    
    echo.
    echo ⬇️  Pulling changes...
    git pull origin main
    if errorlevel 1 (
        echo ❌ Failed to pull changes
        echo There might be conflicts. Please resolve manually.
        pause
        exit /b 1
    )
    
    echo.
    echo ✅ Successfully updated to latest version!
    echo.
    echo 📋 Recent commits pulled:
    git log --oneline HEAD~%BEHIND_COUNT%..HEAD
)

REM Restore stashed changes if any
if defined STASHED (
    echo.
    echo 📦 Restoring stashed changes...
    git stash pop
    if errorlevel 1 (
        echo ⚠️  Warning: Could not restore stashed changes
        echo You can restore them manually with: git stash pop
    ) else (
        echo ✅ Stashed changes restored
    )
)

echo.
echo ========================================
echo Git Update Complete!
echo ========================================
echo.
echo Current status:
git status --porcelain
echo.
pause
