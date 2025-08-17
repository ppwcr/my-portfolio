@echo off
REM Start the API server and open the app
cd /d "%~dp0"
call .venv\Scripts\activate
start "" http://localhost:8000
uvicorn main:app --host 127.0.0.1 --port 8000

