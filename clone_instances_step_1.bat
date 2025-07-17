@echo off
setlocal enabledelayedexpansion

:: Cấu hình đường dẫn
set TEMPLATE=D:\LDPlayer\LDPlayer9\vms\leidian0
set TARGET=D:\LDPlayer\LDPlayer9\vms
set CONFIG_TEMPLATE=D:\LDPlayer\LDPlayer9\vms\config\leidian0.config
set CONFIG_TARGET=D:\LDPlayer\LDPlayer9\vms\config

:: Tổng số instance cần tạo
set MAX_INSTANCE=340

:: Lặp từ 1 đến MAX_INSTANCE
for /L %%i in (1,1,%MAX_INSTANCE%) do (
    echo ========================
    echo Tạo instance leidian%%i

    :: Tạo thư mục clone từ template
    xcopy "%TEMPLATE%" "%TARGET%\leidian%%i" /E /Y /I >nul

    :: Copy file config
    copy /Y "%CONFIG_TEMPLATE%" "%CONFIG_TARGET%\leidian%%i.config" >nul

    echo Đã tạo leidian%%i và sao chép config

    :: Nghỉ 10 giây
    timeout /T 10 /NOBREAK >nul

    :: Sau mỗi 20 lần thì nghỉ 25s
    set /A mod=%%i %% 20
    if !mod! EQU 0 (
        echo ====== Nghỉ 25s sau 20 instances ======
        timeout /T 25 /NOBREAK >nul
    )
)

echo Hoàn tất tạo tất cả instances!
pause
