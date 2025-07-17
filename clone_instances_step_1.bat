@echo off
setlocal

set TEMPLATE_FOLDER=D:\LDPlayer\LDPlayer9\vms\leidian0
set TARGET_FOLDER=D:\LDPlayer\LDPlayer9\vms
set CONFIG_FOLDER=D:\LDPlayer\LDPlayer9\vms\config

for /L %%i in (1,1,340) do (
    echo ========================
    echo Tạo instance leidian%%i

    rem Copy thư mục VM template
    xcopy "%TEMPLATE_FOLDER%" "%TARGET_FOLDER%\leidian%%i" /E /Y /I

    rem Copy file cấu hình .config
    copy /Y "%CONFIG_FOLDER%\leidian0.config" "%CONFIG_FOLDER%\leidian%%i.config"

    timeout /t 7 /nobreak >nul
)

pause
