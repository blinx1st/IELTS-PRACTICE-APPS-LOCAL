@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Chua co moi truong Python. Hay chay CAI_DAT_LAN_DAU.cmd truoc.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -X utf8 "scripts\diagnose.py"
pause
