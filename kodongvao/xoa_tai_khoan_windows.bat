@echo off
chcp 65001 >nul
echo Dang tim va xoa tai khoan (PAT) GitHubManager trong Windows Credential Manager...
echo.

setlocal enabledelayedexpansion
set "count=0"
for /f "tokens=1* delims=:" %%a in ('cmdkey /list 2^>nul ^| findstr /i "Target"') do (
    if "%%a"=="Target" (
        set "target=%%b"
        set "target=!target:~1!"
        echo !target! | findstr /i "GitHubManager" >nul
        if !errorlevel! equ 0 (
            echo Xoa: !target!
            cmdkey /delete:"!target!" 2>nul
            set /a count+=1
        )
    )
)

if %count% equ 0 (
    echo Khong tim thay credential nao chua "GitHubManager".
    echo Hoac ban da xoa roi.
) else (
    echo Da xoa %count% credential.
)
echo.
pause
