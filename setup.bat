@echo off
REM One-time setup: venv + dependencies + Playwright
cd /d "%~dp0"
python -m venv .venv || (echo Install Python 3.10+ first & pause & exit /b 1)
call .venv\Scripts\activate
pip install -r requirements.txt
pip install playwright
python -m playwright install chromium
echo Setup done. You can now run start.bat
pause

