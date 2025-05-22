@echo off
setlocal enabledelayedexpansion

set "SRC_ROOT=D:\LDPlayer\LDPlayer9\vms"
set "DST_ROOT=Z:\Backup_LDPlayer_Fb_Acc"

set "LOG_FILE=%~dp0backup_log_%date:~-4,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt"
set "LOG_FILE=%LOG_FILE: =0%"

echo Starting LDPlayer backup...
echo Source: %SRC_ROOT%
echo Destination: %DST_ROOT%
echo Log file: %LOG_FILE%
echo.

if not exist "%DST_ROOT%" (
    echo Creating backup folder "%DST_ROOT%"
    mkdir "%DST_ROOT%"
)

for /D %%I in ("%SRC_ROOT%\*") do (
    set "INSTANCE=%%~nI"
    echo Backing up !INSTANCE! ...

    rem Run robocopy without removing backup folder, syncing changes only
    robocopy "%%I" "%DST_ROOT%\!INSTANCE!" /MIR /R:2 /W:2 /LOG+:"%LOG_FILE%"
    
    if errorlevel 8 (
        echo ERROR: Backup failed for !INSTANCE! >> "%LOG_FILE%"
        echo Backup failed for !INSTANCE!
    ) else (
        echo Backup succeeded for !INSTANCE! >> "%LOG_FILE%"
    )
    
    echo.
)

echo Backup process completed.
echo Detailed log saved to %LOG_FILE%
pause
endlocal
