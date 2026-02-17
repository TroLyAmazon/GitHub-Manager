@echo off
setlocal

REM Run PowerShell script in the same folder as this .bat
cd /d "%~dp0"

REM Allow running script for this process only (no permanent policy change)
powershell -NoProfile -ExecutionPolicy Bypass -File ".\clean_pycache.ps1"

echo.
echo Done.
pause
endlocal
