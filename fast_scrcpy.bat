@echo off
title Android Mirror - 1-Click WiFi & Cable
cd /d "C:\Users\yeasi\OneDrive\Desktop\scrcpy\scrcpy-win64-v2.4"
cls

echo ======================================================
echo           SCRCPY DIRECT CONTROLLER
echo ======================================================
echo.
echo  [1] USB Cable Mode
echo  [2] WiFi Mode (Direct Connect)
echo  [3] Exit
echo.
echo ======================================================
set /p mode="Choose connection type (1/2/3): "

if "%mode%"=="1" goto USB_MODE
if "%mode%"=="2" goto WIFI_MODE
if "%mode%"=="3" exit

:USB_MODE
cls
echo [Connecting via USB Cable]...
scrcpy.exe -d --audio-codec=aac --audio-buffer=40 --display-buffer=0 --max-fps=120 --video-bit-rate=16M --max-size=1080 --stay-awake
if %ERRORLEVEL% NEQ 0 (
    echo Retrying with Opus audio codec...
    scrcpy.exe -d --audio-codec=opus --audio-buffer=50 --max-size=1080
)
goto END

:WIFI_MODE
cls
echo ======================================================
echo Make sure "Wireless Debugging" is toggled ON on your phone
echo ======================================================
echo.
set /p phone_target="Enter Phone IP:Port (e.g. 192.168.1.2:42001): "

echo.
echo [Connecting to %phone_target%]...
adb.exe connect %phone_target%
echo.

scrcpy.exe -s %phone_target% --audio-codec=aac --audio-buffer=50 --display-buffer=0 --max-fps=90 --video-bit-rate=10M --max-size=1080 --stay-awake
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Connection failed or primary audio failed. Retrying...
    scrcpy.exe -s %phone_target% --audio-codec=opus --audio-buffer=60 --max-size=1080
)
goto END

:END
echo.
pause
