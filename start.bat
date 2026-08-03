@echo off
echo ========================================
echo TSRTC Smart Analytics Platform
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

echo Python found
echo.

REM Navigate to backend directory
cd backend

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo.

REM Start the server
echo ========================================
echo Starting TSRTC Analytics Backend
echo ========================================
echo.
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo To access frontend, open frontend/index.html
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python main.py

pause