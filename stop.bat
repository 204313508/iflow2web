@echo off
title Stop iFlow2Web Server

echo ========================================
echo       Stop iFlow2Web Server
echo ========================================
echo.

REM Find and stop Python processes running main.py
for /f "tokens=2" %%a in ('wmic process where "name='python.exe' and commandline like '%%main.py%%'" get processid 2^>nul ^| findstr /r "[0-9]"') do (
    echo [STOP] Stopping process PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)

REM Find and stop uvicorn processes (if any)
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq uvicorn.exe" /FI "STATUS eq running" /FO CSV ^| findstr /i "uvicorn.exe"') do (
    echo [STOP] Stopping process PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo [DONE] iFlow2Web server stopped
echo.
pause