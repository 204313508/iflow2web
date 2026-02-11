@echo off
setlocal enabledelayedexpansion
title iFlow2Web Server

echo ========================================
echo       iFlow2Web - iFlow CLI Web Interface
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "iflow2web\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run the following commands first:
    echo   python -m venv iflow2web
    echo   iflow2web\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Stop old server
echo [INFO] Stopping old server...
for /f "tokens=2" %%a in ('wmic process where "name='python.exe' and commandline like '%%main.py%%'" get processid 2^>nul ^| findstr /r "[0-9]"') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo [INFO] Old server stopped.
echo.

REM Activate virtual environment
call iflow2web\Scripts\activate.bat

REM Check dependencies
python -c "import fastapi, uvicorn, iflow_sdk" 2>nul
if errorlevel 1 (
    echo [WARNING] Dependencies not found, installing...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies!
        pause
        exit /b 1
    )
    echo.
    echo Dependencies installed!
    echo.
)

REM Check if iFlow CLI is installed
where iflow >nul 2>&1
if errorlevel 1 (
    echo [WARNING] iFlow CLI not installed!
    echo Please install iFlow CLI first:
    echo   npm install -g @iflow-ai/iflow-cli
    echo.
    echo Then run: iflow
    echo.
    pause
    exit /b 1
)

REM Input port number
:input_port
set /p PORT="Enter port number (1-65535, default 8000): "
if "%PORT%"=="" set PORT=8000

REM Validate port number
if %PORT% LSS 1 (
    echo [ERROR] Port number must be greater than 0!
    goto :input_port
)
if %PORT% GTR 65535 (
    echo [ERROR] Port number must be less than 65536!
    goto :input_port
)

echo.
echo ========================================
echo  Startup Info:
echo  - Server: http://0.0.0.0:%PORT%
echo  - LAN: Use your IP address
echo  - Press Ctrl+C to stop
echo ========================================
echo.

REM Get local IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set "IP=%%a"
    set IP=!IP: =!
    echo [INFO] LAN access: http://!IP!:%PORT%
    goto :found_ip
)
:found_ip
echo.

REM Start server
echo [START] Starting iFlow2Web server on port %PORT%...
echo.

python main.py %PORT%

REM If server exits abnormally
echo.
echo [STOP] Server stopped
pause