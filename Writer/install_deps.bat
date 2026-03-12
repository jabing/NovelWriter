@echo off
chcp 65001 >nul
title Writer Studio - Install Dependencies

echo.
echo ========================================
echo   Writer Studio - Install Dependencies
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.10+
    pause
    exit /b 1
)

echo Installing required packages...
echo.

REM Core dependencies
pip install textual openai pyperclip zhipuai rich click

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Create a .env file with your API keys:
echo      DEEPSEEK_API_KEY=your_deepseek_key
echo      ZHIPUAI_API_KEY=your_zhipuai_key
echo.
echo   2. Run run_chat.bat to start the app
echo.
pause
