@echo off
setlocal

set PYTHON_EXE=python
set SCRIPT_PY=generate_config_files.py
set TEMPLATE_FOLDER=D:\LDPlayer\LDPlayer9\vms\leidian0
set TARGET_FOLDER=D:\LDPlayer\LDPlayer9\vms

for /L %%i in (1,1,340) do (
    echo [COPY] -> leidian%%i
    xcopy "%TEMPLATE_FOLDER%" "%TARGET_FOLDER%\leidian%%i" /E /Y /I
    timeout /t 5 /nobreak >nul
)

echo [GENERATE CONFIG FILES]
%PYTHON_EXE% "%SCRIPT_PY%"

pause
