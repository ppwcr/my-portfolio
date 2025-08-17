@echo off
REM Update Supabase database once per weekday via API
setlocal
cd /d "%~dp0"

REM Skip weekends (Saturday/Sunday)
for /f %%D in ('powershell -NoProfile -Command "(Get-Date).DayOfWeek"') do set DOW=%%D
if /I "%DOW%"=="Saturday" exit /b 0
if /I "%DOW%"=="Sunday" exit /b 0

set URL=http://127.0.0.1:8000

REM Trigger consolidated update (investor, sectors, NVDR, short sales)
curl -fsS -X POST "%URL%/api/save-to-database" -H "Content-Type: application/json" -o NUL

if errorlevel 1 (
  echo [%date% %time%] Update failed >> update_log.txt
  exit /b 1
) else (
  echo [%date% %time%] Update succeeded >> update_log.txt
)
endlocal

