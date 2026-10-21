@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -X utf8 "scripts\launch.py" --stop
) else (
  python -X utf8 "scripts\launch.py" --stop
)
if errorlevel 1 pause
