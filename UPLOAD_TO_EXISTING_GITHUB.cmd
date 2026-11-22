@echo off
setlocal
cd /d "%~dp0"
echo Dumbplayer DEV17 - upload the FULL source to an EXISTING GitHub repository.
echo No private keystore or Android APK is included.
echo.
set /p REPOSITORY_URL=Enter your existing Dumbplayer repository HTTPS URL: 
if "%REPOSITORY_URL%"=="" (echo No URL entered. & pause & exit /b 1)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0PUSH_DEV17_TO_GITHUB.ps1" -RepositoryUrl "%REPOSITORY_URL%"
echo.
echo Return to this folder if you need the READ FIRST guide.
pause
