@echo off
chcp 65001 >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalar_mod.ps1" -Zip "%~1"
pause
