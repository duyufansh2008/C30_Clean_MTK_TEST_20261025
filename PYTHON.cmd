@echo off
setlocal
cd /d "%~dp0"
set "C30_PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%C30_PY%" goto run
set "C30_PY=python"
:run
"%C30_PY%" "%~dp0tools\check_runtime.py"
if errorlevel 1 exit /b 1
"%C30_PY%" %*
exit /b %errorlevel%
