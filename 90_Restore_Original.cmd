@echo off
setlocal
cd /d "%~dp0"
call "%~dp0MTK.cmd" w super,vbmeta rollback\super.img,rollback\vbmeta.img
exit /b %errorlevel%
