@echo off
setlocal
cd /d "%~dp0"
echo Playlist Desk - Windows and Linux companion overlay for your existing Dumbplayer DEV17 GitHub repository.
echo.
set /p REPOSITORY_URL=Existing GitHub repository URL (https://github.com/owner/repo.git): 
if "%REPOSITORY_URL%"=="" (echo No URL supplied. & pause & exit /b 1)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0UPLOAD_DESK_ADDON.ps1" -RepositoryUrl "%REPOSITORY_URL%"
if errorlevel 1 (echo Upload process did not complete. Review the message above.)
pause
