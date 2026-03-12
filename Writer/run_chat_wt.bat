@echo off
chcp 65001 >nul

REM Check if Windows Terminal is available
wt --version >nul 2>&1
if errorlevel 1 (
    echo Windows Terminal not found, starting in CMD...
    call run_chat.bat
    exit /b 0
)

REM Start in Windows Terminal for better experience
wt -d "%~dp0" --title "Writer Studio" cmd /k "python -m src.main studio"
