@echo off
setlocal
set TEMPLATE=D:\LDPlayer\LDPlayer9\vms\leidian0
set TARGET=D:\LDPlayer\LDPlayer9\vms

for /L %%i in (0,1,340) do (
    echo ========================
    echo Tạo instance leidian%%i
    xcopy "%TEMPLATE%" "%TARGET%\leidian%%i" /E /Y /I
    timeout /t 1 /nobreak >nul
)

pause
