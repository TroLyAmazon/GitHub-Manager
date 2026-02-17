@echo off
chcp 65001 >nul
set "FOLDER=%LOCALAPPDATA%\GitHubManager"
if not exist "%FOLDER%" (
    echo Khong tim thay thu muc: %FOLDER%
    echo App chua luu du lieu hoac da xoa roi.
    pause
    exit /b 0
)
echo Dang xoa du lieu app tai: %FOLDER%
rd /s /q "%FOLDER%"
if exist "%FOLDER%" (
    echo LOI: Khong xoa duoc. Thu muc co the dang duoc mo boi app khac.
) else (
    echo Da xoa xong du lieu (data, logs, workspaces).
)
echo.
pause
