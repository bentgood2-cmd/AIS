@echo off
echo AIS System Direct Launcher
echo ===========================
echo.

REM Change to project directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "ais_env\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo.
    echo Please run one of these commands first:
    echo   1. Double-click setup_environment.bat
    echo   2. Run: python -m venv ais_env
    echo   3. Run: ais_env\Scripts\activate ^&^& pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo Using Python: ais_env\Scripts\python.exe
echo Project directory: %CD%
echo.

REM Run the launcher
"ais_env\Scripts\python.exe" run_ais_system.py

echo.
pause