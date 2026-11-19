@echo off
setlocal
cd /d "%~dp0"
call "%~dp0MTK.cmd" reset
exit /b %errorlevel%
