@echo off
setlocal
cd /d "%~dp0"
call "%~dp0PYTHON.cmd" "%~dp0tools\verify_files.py"
exit /b %errorlevel%
