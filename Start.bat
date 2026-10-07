@echo off
cd /d "%~dp0"
call Finn_Python.bat
if errorlevel 1 (
 pause
 exit /b 1
)
%PY_CMD% main.py
if errorlevel 1 pause
