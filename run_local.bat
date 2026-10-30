@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" goto use_venv
where py >nul 2>nul
if %errorlevel%==0 goto find_py
where python >nul 2>nul
if %errorlevel%==0 (
  python -c "import sys; raise SystemExit(sys.version_info < (3, 11))" >nul 2>nul
  if errorlevel 1 goto no_python
  python -m venv .venv
  if errorlevel 1 goto venv_error
  goto use_venv
)
echo Python 3.11 or newer was not found. Install Python from https://www.python.org/downloads/windows/ and try again.
pause
exit /b 1

:find_py
py -3.12 -m venv .venv >nul 2>nul
if not errorlevel 1 goto use_venv
py -3.13 -m venv .venv >nul 2>nul
if not errorlevel 1 goto use_venv
py -3.11 -m venv .venv >nul 2>nul
if not errorlevel 1 goto use_venv
py -3 -c "import sys; raise SystemExit(sys.version_info < (3, 11))" >nul 2>nul
if errorlevel 1 goto no_python
py -3 -m venv .venv >nul 2>nul
if not errorlevel 1 goto use_venv
:no_python
echo No usable Python interpreter was found. Install Python 3.11 or newer and try again.
pause
exit /b 1

:use_venv
if not exist ".venv\Scripts\python.exe" (
  echo Could not create the local virtual environment.
  pause
  exit /b 1
)
if not exist ".venv\deps-installed" (
  echo Installing Big Prezo dependencies into .venv...
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  if errorlevel 1 goto install_error
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 goto install_error
  echo ready>.venv\deps-installed
)
echo Starting Big Prezo at http://127.0.0.1:7860
".venv\Scripts\python.exe" app.py
exit /b %errorlevel%

:venv_error
echo Failed to create the local virtual environment.
pause
exit /b 1

:install_error
echo Dependency installation failed. Check your internet connection and try again.
pause
exit /b 1
