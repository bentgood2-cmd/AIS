@echo off
echo Installing Core Dependencies Only (Python 3.13 Compatible)
echo =========================================================
echo.

REM Upgrade pip first
echo Upgrading pip...
ais_env\Scripts\python.exe -m pip install --upgrade pip

echo.
echo Installing core packages individually...

REM Install packages one by one
ais_env\Scripts\python.exe -m pip install fastapi
ais_env\Scripts\python.exe -m pip install "uvicorn[standard]"
ais_env\Scripts\python.exe -m pip install psutil
ais_env\Scripts\python.exe -m pip install pydantic
ais_env\Scripts\python.exe -m pip install python-dateutil

echo.
echo Core installation complete!
echo.
echo The following will work:
echo - AIS Core System
echo - Synthetic Data Generator  
echo - Health Check
echo - System Tests
echo.
echo Optional (may not work with Python 3.13):
echo - Web API (if FastAPI installed successfully)
echo - GUI (requires PyQt6)
echo - Advanced ML features (requires numpy, torch, etc.)
echo.
pause