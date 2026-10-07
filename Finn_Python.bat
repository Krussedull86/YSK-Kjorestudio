@echo off
set "PY_CMD="
py -3 -c "import sys; assert sys.version_info >= (3,9)" >nul 2>nul
if not errorlevel 1 (
 set "PY_CMD=py -3"
 exit /b 0
)
python -c "import sys; assert sys.version_info >= (3,9)" >nul 2>nul
if not errorlevel 1 (
 set "PY_CMD=python"
 exit /b 0
)
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
 if exist "%%~D\python.exe" (
  "%%~D\python.exe" -c "import sys; assert sys.version_info >= (3,9)" >nul 2>nul
  if not errorlevel 1 (
   set PY_CMD="%%~D\python.exe"
   exit /b 0
  )
 )
)
echo Fant ikke Python 3.9 eller nyere.
echo Installer Python fra https://www.python.org/downloads/windows/
echo Velg Add python.exe to PATH og Tcl/Tk ved installasjon.
exit /b 1
