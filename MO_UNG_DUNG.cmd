@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -X utf8 "scripts\launch.py"
) else (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\bootstrap.ps1"
  if errorlevel 1 goto setup_failed
  ".venv\Scripts\python.exe" -X utf8 "scripts\launch.py"
)
if errorlevel 1 pause
exit /b
:setup_failed
pause
exit /b 1
