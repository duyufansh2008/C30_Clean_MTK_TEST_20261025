@echo off
setlocal
cd /d "%~dp0"
set "C30_PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%C30_PY%" goto run
set "C30_PY=python"
:run
"%C30_PY%" %*
exit /b %errorlevel%
