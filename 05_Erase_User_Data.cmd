@echo off
setlocal
cd /d "%~dp0"
call "%~dp0PYTHON.cmd" "%~dp0tools\verify_files.py"
if errorlevel 1 exit /b 1
call "%~dp0PYTHON.cmd" "%~dp0tools\check_layout.py"
if errorlevel 1 exit /b 1
echo This erases userdata, metadata, md_udc and cache. Personal data will be deleted.
call "%~dp0MTK.cmd" e userdata,metadata,md_udc,cache
exit /b %errorlevel%
