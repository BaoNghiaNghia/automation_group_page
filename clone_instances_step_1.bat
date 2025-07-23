@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: Đường dẫn gốc của instance template
set "TEMPLATE=D:\LDPlayer\LDPlayer9\vms\leidian0"
set "TARGET=D:\LDPlayer\LDPlayer9\vms"
set "CONFIG_TEMPLATE=D:\LDPlayer\LDPlayer9\vms\config\leidian0.config"
set "CONFIG_TARGET=D:\LDPlayer\LDPlayer9\vms\config"

:: Giới hạn từ leidian338 đến leidian635
set "START=338"
set "END=635"
set /A TOTAL=%END% - %START% + 1

echo ==============================================
echo BẮT ĐẦU TẠO INSTANCE LDPLAYER TỪ %START% ĐẾN %END%
echo ==============================================

for /L %%i in (%START%,1,%END%) do (
    echo --------------------------
    echo Tạo instance leidian%%i...

    :: Bỏ qua nếu đã tồn tại
    if exist "%TARGET%\leidian%%i" (
        echo leidian%%i đã tồn tại. Bỏ qua.
        goto :continue_loop
    )

    :: Copy thư mục template
    robocopy "%TEMPLATE%" "%TARGET%\leidian%%i" /MIR /NFL /NDL /NJH /NJS >nul

    :: Copy file config
    copy /Y "%CONFIG_TEMPLATE%" "%CONFIG_TARGET%\leidian%%i.config" >nul

    :: Log & thông báo
    echo Đã tạo leidian%%i và sao chép config
    echo leidian%%i - %TIME% >> log_create_instances.txt

    :: Tiến độ %
    set /A done=%%i - %START% + 1
    set /A percent=done*100/TOTAL
    echo Đang xử lý: %%i/%END%  (%%percent%% %%)

    :: Nghỉ 3 giây mỗi lần
    timeout /T 10 /NOBREAK >nul

    :: Nghỉ 20 giây sau mỗi 20 instance
    set /A mod=done %% 20
    if !mod! EQU 0 (
        echo ======= Nghỉ 20 giây sau mỗi 20 instance =======
        timeout /T 25 /NOBREAK >nul
    )

    :continue_loop
)

echo =====================================
echo ĐÃ HOÀN TẤT TẠO %TOTAL% INSTANCE LDPLAYER
echo File log: log_create_instances.txt
echo =====================================
pause
