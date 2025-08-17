@echo off
REM Register a Windows Scheduled Task to update database on weekdays
setlocal
cd /d "%~dp0"

REM Configuration: change the time as needed (HH:MM in 24h)
set RUN_TIME=18:05
set TASK_NAME=SET_UpdateDatabase

REM Delete existing task if present
schtasks /Query /TN %TASK_NAME% >NUL 2>&1
if %ERRORLEVEL%==0 (
  schtasks /Delete /TN %TASK_NAME% /F >NUL 2>&1
)

REM Create weekday task running the local update script
schtasks /Create ^
  /TN %TASK_NAME% ^
  /TR "\"%~dp0update_database_daily.bat\"" ^
  /SC WEEKLY ^
  /D MON,TUE,WED,THU,FRI ^
  /ST %RUN_TIME% ^
  /RL LIMITED >NUL 2>&1

if %ERRORLEVEL% NEQ 0 (
  echo Failed to create scheduled task. Try running as Administrator.
  exit /b 1
)

echo Scheduled task '%TASK_NAME%' created to run at %RUN_TIME% (Mon-Fri).
endlocal

