@echo off
setlocal
cd /d "%~dp0"
call "%~dp0MTK.cmd" w super,vbmeta images\super.img,images\vbmeta.img
exit /b %errorlevel%
