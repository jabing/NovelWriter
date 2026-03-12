@echo off
chcp 65001 >nul
title Writer Studio - Chat Interface
cd /d "%~dp0"

echo.
echo ========================================
echo   Writer Studio - Chat Interface
echo ========================================
echo.

REM Check if .env file exists
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo.
    echo Please create a .env file with your API keys:
    echo.
    echo   DEEPSEEK_API_KEY=your_deepseek_key
    echo   ZHIPUAI_API_KEY=your_zhipuai_key
    echo.
    echo You can still use the app, but LLM features won't work.
    echo.
)

REM Check Python

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.10+
    pause
    exit /b 1
)

REM Detect terminal and show info
echo [INFO] Detecting terminal...
python -c "import sys; sys.path.insert(0, 'src'); from studio.chat.app import detect_terminal; t=detect_terminal(); print(f'       Terminal: {t[\"terminal_name\"]}'); print(f'       Mouse: {\"Enabled\" if t[\"supports_mouse\"] else \"Disabled (use keyboard scrolling)\"}')"
echo.

REM Run the Chat Studio
echo Starting Writer Studio...
echo Press Ctrl+C to exit
echo.

python -m src.main studio

if errorlevel 1 (
    echo.
    echo [ERROR] Application crashed or failed to start
    echo.
    echo Common issues:
    echo   1. Missing dependencies: run install_deps.bat
    echo   2. Missing API keys: create .env file
    echo   3. Python version: need Python 3.10+
    echo.
    pause
)
