@echo off
chcp 65001 >nul
title 测试服务启动

echo ========================================
echo 测试服务启动
echo ========================================
echo.

cd /d "%~dp0"

echo 当前目录: %CD%
echo.

echo 测试1: 启动Flask服务器...
start "Flask测试" cmd /k "python run_flask.py --port 5000 --debug"
echo.

timeout /t 5 /nobreak

echo 测试2: 检查Flask端口...
netstat -ano | findstr :5000
echo.

echo 测试3: 启动WebSocket服务器...
start "WebSocket测试" cmd /k "python start_websocket.py"
echo.

timeout /t 3 /nobreak

echo 测试4: 检查WebSocket端口...
netstat -ano | findstr :8765
echo.

echo ========================================
echo 测试完成
echo ========================================
echo.
echo 如果看到端口监听信息，说明服务启动成功
echo 如果没有看到，请查看弹出的窗口中的错误信息
echo.

pause
