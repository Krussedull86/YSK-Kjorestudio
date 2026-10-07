@echo off
cd /d "%~dp0"
call Finn_Python.bat
if errorlevel 1 goto fail
%PY_CMD% -m venv .build_env
if errorlevel 1 goto fail
.build_env\Scripts\python.exe -m pip install "pyinstaller>=6,<7"
if errorlevel 1 goto fail
.build_env\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name YSK_Kjorestudio --add-data "mobile.html;." main.py
if errorlevel 1 goto fail
echo Ferdig: dist\YSK_Kjorestudio.exe
explorer dist
pause
exit /b 0
:fail
echo Bygging feilet. Se feilmeldingen ovenfor.
pause
exit /b 1
