@echo off
setlocal
cd /d "%~dp0"
if not exist readback mkdir readback
call "%~dp0PYTHON.cmd" "%~dp0tools\prepare_read.py" readback
if errorlevel 1 exit /b 1
call "%~dp0MTK.cmd" r super,vbmeta readback\super.img,readback\vbmeta.img
if errorlevel 1 exit /b 1
call "%~dp0PYTHON.cmd" "%~dp0tools\verify_files.py" --readback original
exit /b %errorlevel%
