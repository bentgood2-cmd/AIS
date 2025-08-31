@echo off
echo AIS System Quick Start
echo ======================
echo.

REM Change to project directory
cd /d "%~dp0"

REM Check if setup is needed
if not exist "ais_env\Scripts\python.exe" (
    echo Setting up environment for first time...
    echo.
    call setup_environment.bat
    if errorlevel 1 (
        echo Setup failed. Please check the errors above.
        pause
        exit /b 1
    )
)

echo.
echo Starting AIS System...
echo.

REM Run the system
call run_direct.bat