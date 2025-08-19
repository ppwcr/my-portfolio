@echo off
echo ========================================
echo Scheduled SET Data Scraper
echo Time: %date% %time%
echo ========================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Logging error to scraper_error.log
    echo %date% %time% - Python not found >> scraper_error.log
    exit /b 1
)

REM Check if requirements are installed
echo Checking dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        echo %date% %time% - Dependencies installation failed >> scraper_error.log
        exit /b 1
    )
)

echo.
echo 🚀 Starting scheduled data scraping...
echo.

REM Create log file with timestamp
set "LOG_FILE=scraper_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%.log"
set "LOG_FILE=%LOG_FILE: =0%"

echo ======================================== >> %LOG_FILE%
echo Scheduled Scraping Started: %date% %time% >> %LOG_FILE%
echo ======================================== >> %LOG_FILE%

REM Run the background updater to scrape all data
echo Running data scraping operations...
python -c "
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath('.')))
from background_updater import updater
import logging

# Setup logging to file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%.log'.replace(' ', '0'), 'a'),
        logging.StreamHandler()
    ]
)

async def main():
    try:
        print('Starting scheduled data refresh...')
        success = await updater.update_all_data()
        if success:
            print('✅ Scheduled scraping completed successfully')
        else:
            print('⚠️ Scheduled scraping completed with some errors')
        return success
    except Exception as e:
        print(f'❌ Scheduled scraping failed: {e}')
        return False

if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
"

if errorlevel 1 (
    echo.
    echo ❌ Scheduled scraping failed
    echo Check the log file for details: %LOG_FILE%
    echo %date% %time% - Scheduled scraping failed >> scraper_error.log
) else (
    echo.
    echo ✅ Scheduled scraping completed successfully
    echo Log saved to: %LOG_FILE%
)

echo ======================================== >> %LOG_FILE%
echo Scheduled Scraping Completed: %date% %time% >> %LOG_FILE%
echo ======================================== >> %LOG_FILE%

echo.
echo Scheduled scraping finished at %time%
echo.
