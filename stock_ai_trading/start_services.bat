@echo off
chcp 65001 >nul 2>&1
title Stock AI Trading System - Service Launcher

echo ========================================
echo Stock AI Trading System - Start All Services
echo ========================================
echo.

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please ensure Python is installed and added to PATH
    echo.
    echo Please check:
    echo   1. Python is installed
    echo   2. Python is added to system PATH environment variable
    echo.
    pause
    exit /b 1
)

echo [OK] Python environment check passed
python --version
echo.

:: Switch to script directory
cd /d "%~dp0"

echo [INFO] Current directory: %CD%
echo.

:: Activate virtual environment (if exists)
if exist "%~dp0.venv\Scripts\activate.bat" (
    echo [INFO] Virtual environment detected, activating...
    call "%~dp0.venv\Scripts\activate.bat"
    echo [OK] Virtual environment activated
) else if exist "%~dp0..\.venv\Scripts\activate.bat" (
    echo [INFO] Parent directory virtual environment detected, activating...
    call "%~dp0..\.venv\Scripts\activate.bat"
    echo [OK] Virtual environment activated
) else (
    echo [WARN] No virtual environment detected, using system Python.
)
echo.

:: Check if necessary Python files exist
if not exist "%~dp0run_flask.py" (
    echo [ERROR] run_flask.py file not found
    pause
    exit /b 1
)

if not exist "%~dp0start_websocket.py" (
    echo [ERROR] start_websocket.py file not found
    pause
    exit /b 1
)

if not exist "%~dp0.env" (
    echo [WARN] .env configuration file not found, services may not work properly
    echo        Please copy .env.example to .env and configure parameters
    echo.
)

echo [OK] Startup files check passed
echo.

:: Check if key dependencies are installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Flask is not installed
    echo.
    echo Please run install_dependencies.bat to install dependencies
    echo Or manually execute: pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

python -c "import websockets" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] websockets is not installed
    echo.
    echo Please run install_dependencies.bat to install dependencies
    echo Or manually execute: pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo [OK] Dependencies check passed
echo.

:: Start Flask API server
echo [INFO] Starting Flask API server...
:: Check if port 5000 is in use
netstat -ano | findstr :5000 >nul 2>&1
if %errorlevel%==0 (
    echo [WARN] Port 5000 is already in use, skipping Flask startup
) else (
    start "Flask API Server" cmd /k "cd /d %~dp0 && python run_flask.py --port 5000 --debug"
    echo [OK] Flask API server startup command executed
)

:: Wait for Flask to start
echo [INFO] Waiting for Flask server to start...
timeout /t 3 /nobreak >nul

:: Start WebSocket server
echo [INFO] Starting WebSocket server...
:: Check if port 8765 is in use
netstat -ano | findstr :8765 >nul 2>&1
if %errorlevel%==0 (
    echo [WARN] Port 8765 is already in use, WebSocket service may already be running
) else (
    start "WebSocket Server" cmd /k "cd /d %~dp0 && python start_websocket.py"
    echo [OK] WebSocket server startup command executed
)

:: Wait for WebSocket to start
echo [INFO] Waiting for WebSocket server to start...
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo All services startup completed!
echo ========================================
echo.

:: Verify if services started successfully
echo [INFO] Verifying service status...
echo.

timeout /t 2 /nobreak >nul

netstat -ano | findstr :5000 >nul 2>&1
if %errorlevel%==0 (
    echo [OK] Flask API Server (Port 5000) - Running
) else (
    echo [ERROR] Flask API Server (Port 5000) - Not Running
    echo        Please check Flask server window for error messages
)

netstat -ano | findstr :8765 >nul 2>&1
if %errorlevel%==0 (
    echo [OK] WebSocket Server (Port 8765) - Running
) else (
    echo [ERROR] WebSocket Server (Port 8765) - Not Running
    echo        Please check WebSocket server window for error messages
)

echo.
echo ========================================
echo Service URLs:
echo   Flask API Server: http://localhost:5000
echo   WebSocket Server: ws://localhost:8765
echo   API Documentation: http://localhost:5000/docs
echo ========================================
echo.

echo Tips: 
echo   - Each service runs in a separate command window
echo   - Close the corresponding window to stop the service
echo   - Or use stop_services.bat to stop all services
echo   - If services are not running, check the error messages in their windows
echo.

pause