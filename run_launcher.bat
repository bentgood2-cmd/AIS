@echo off
echo AIS System Launcher Starting...
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "ais_env\Scripts\python.exe" (
    echo Virtual environment not found!
    echo Please run setup first or create virtual environment.
    echo.
    pause
    exit /b 1
)

REM Run with virtual environment Python
ais_env\Scripts\python.exe run_ais_system.py

echo.
echo AIS System Launcher finished.
pause