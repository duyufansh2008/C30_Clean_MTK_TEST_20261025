@echo off
setlocal
cd /d "%~dp0"
if not exist backup mkdir backup
call "%~dp0PYTHON.cmd" "%~dp0tools\prepare_read.py" layout
if errorlevel 1 exit /b 1
call "%~dp0MTK.cmd" gpt backup
if errorlevel 1 exit /b 1
call "%~dp0PYTHON.cmd" "%~dp0tools\check_layout.py"
exit /b %errorlevel%
