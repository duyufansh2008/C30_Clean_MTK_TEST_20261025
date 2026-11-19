@echo off
setlocal
cd /d "%~dp0"
echo This erases userdata, metadata, md_udc and cache. Personal data will be deleted.
call "%~dp0MTK.cmd" e userdata,metadata,md_udc,cache
exit /b %errorlevel%
