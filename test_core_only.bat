@echo off
echo Testing Core AIS Functionality (No External Dependencies)
echo ========================================================
echo.
ais_env\Scripts\python.exe test_core_only.py
echo.
pause