@echo off
echo AIS System Environment Setup
echo =============================
echo.

REM Change to project directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH!
    echo.
    echo Please install Python 3.8+ from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo Python found: 
python --version

REM Create virtual environment if it doesn't exist
if not exist "ais_env" (
    echo.
    echo Creating virtual environment...
    python -m venv ais_env
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)

REM Install dependencies
echo.
echo Installing dependencies...
ais_env\Scripts\python.exe -m pip install --upgrade pip
ais_env\Scripts\python.exe -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo WARNING: Some dependencies may have failed to install.
    echo The system may still work with basic functionality.
) else (
    echo ✓ Dependencies installed successfully
)

echo.
echo =============================
echo Setup complete!
echo.
echo You can now run:
echo   - run_direct.bat (recommended)
echo   - run_launcher.bat
echo   - test_all_simple.bat
echo.
pause