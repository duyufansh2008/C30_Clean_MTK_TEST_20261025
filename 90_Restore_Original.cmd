@echo off
setlocal
cd /d "%~dp0"
call "%~dp0PYTHON.cmd" "%~dp0tools\verify_files.py"
if errorlevel 1 exit /b 1
call "%~dp0PYTHON.cmd" "%~dp0tools\check_layout.py"
if errorlevel 1 exit /b 1
call "%~dp0MTK.cmd" w super,vbmeta rollback\super.img,rollback\vbmeta.img
exit /b %errorlevel%
