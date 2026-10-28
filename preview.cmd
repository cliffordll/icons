@echo off
cd /d "%~dp0"
python scripts\preview_server.py %*
if errorlevel 1 pause
