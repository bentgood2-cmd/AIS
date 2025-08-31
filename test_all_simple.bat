@echo off
echo Running AIS System Quick Tests...
echo.
ais_env\Scripts\python.exe test_all_simple.py
echo.
pause