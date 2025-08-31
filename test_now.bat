@echo off
echo Testing AIS Core Functionality
echo ==============================
echo.

echo Testing synthetic data generator...
ais_env\Scripts\python.exe test_core_only.py

pause