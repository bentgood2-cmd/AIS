@echo off
REM AIS System Launcher for Windows
REM This batch file runs the AIS system launcher

echo ========================================
echo    AIS System Launcher Starting...
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found in PATH. Trying py launcher...
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo Python not found. Please install Python 3.8+ and try again.
        pause
        exit /b 1
    )
    set PYTHON_CMD=py
) else (
    set PYTHON_CMD=python
)

echo Python found. Starting AIS System Launcher...
echo.

REM Run the AIS system launcher
%PYTHON_CMD% run_ais_system.py

REM If we get here, the launcher has exited
echo.
echo ========================================
echo    AIS System Launcher Exited
echo ========================================
pause
