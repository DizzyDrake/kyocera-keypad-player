@echo off
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (
  py -3 integrated_app.py
) else (
  python integrated_app.py
)
if errorlevel 1 pause
