@echo off
setlocal
cd /d "%~dp0"
call "%~dp0PYTHON.cmd" "%~dp0tools\run_mtk.py" %*
exit /b %errorlevel%
