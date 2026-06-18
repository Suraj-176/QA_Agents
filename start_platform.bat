@echo off
title QA.AI Platform Launcher
echo ====================================================================
echo   QA.AI Platform Launcher — Zero-Friction Setup
echo ====================================================================
echo.

:: 1. Verify Python Installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not registered in your system PATH!
    echo Please install Python 3.10+ before running this script.
    echo.
    pause
    exit /b
)

:: 2. Verify Node.js Installation
node -v >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not registered in your system PATH!
    echo Please install Node.js before running this script.
    echo.
    pause
    exit /b
)

echo [1/2] Starting Backend API Server ^(FastAPI on http://127.0.0.1:5000^)...
:: Launches FastAPI in a new separate Command Prompt window so logs are clearly visible
start "QA.AI Backend Server" cmd /k "cd backend && venv\Scripts\activate && python main.py"

echo [2/2] Starting Frontend UI Server ^(Vite + React on http://127.0.0.1:3000^)...
:: Launches Vite in a new separate Command Prompt window
start "QA.AI Frontend Server" cmd /k "cd frontend && npm run dev"

echo.
echo ====================================================================
echo   SUCCESS: Both servers have been successfully launched!
echo   - Close the newly opened command windows to stop the servers.
echo.
echo   Please open your browser and navigate to:
echo   👉 http://127.0.0.1:3000
echo ====================================================================
echo.
pause
