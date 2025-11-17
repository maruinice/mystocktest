@echo off
chcp 65001 >nul
title 服务启动诊断工具

echo ========================================
echo 🔍 服务启动诊断工具
echo ========================================
echo.

cd /d "%~dp0"

echo 📂 当前目录: %CD%
echo.

echo ========================================
echo 1. Python环境检查
echo ========================================
python --version
if errorlevel 1 (
    echo ❌ Python未安装或未添加到PATH
    goto :end
)
echo ✅ Python可用
echo.

echo ========================================
echo 2. 依赖检查
echo ========================================
echo 检查Flask...
python -c "import flask; print('Flask版本:', flask.__version__)"
if errorlevel 1 (
    echo ❌ Flask未安装
    goto :end
)
echo.

echo 检查websockets...
python -c "import websockets; print('websockets版本:', websockets.__version__)"
if errorlevel 1 (
    echo ❌ websockets未安装
    goto :end
)
echo.

echo 检查flask_cors...
python -c "import flask_cors; print('flask_cors已安装')"
if errorlevel 1 (
    echo ❌ flask_cors未安装
    goto :end
)
echo.

echo ✅ 所有依赖已安装
echo.

echo ========================================
echo 3. 文件检查
echo ========================================
if exist "run_flask.py" (
    echo ✅ run_flask.py 存在
) else (
    echo ❌ run_flask.py 不存在
)

if exist "start_websocket.py" (
    echo ✅ start_websocket.py 存在
) else (
    echo ❌ start_websocket.py 不存在
)

if exist ".env" (
    echo ✅ .env 配置文件存在
) else (
    echo ⚠️ .env 配置文件不存在
)
echo.

echo ========================================
echo 4. 端口检查
echo ========================================
echo 检查5000端口...
netstat -ano | findstr :5000
if errorlevel 1 (
    echo ✅ 端口5000空闲
) else (
    echo ⚠️ 端口5000已被占用
)
echo.

echo 检查8765端口...
netstat -ano | findstr :8765
if errorlevel 1 (
    echo ✅ 端口8765空闲
) else (
    echo ⚠️ 端口8765已被占用
)
echo.

echo ========================================
echo 5. 测试Flask启动
echo ========================================
echo 尝试导入Flask应用...
python -c "from run_flask import app; print('Flask应用加载成功')"
if errorlevel 1 (
    echo ❌ Flask应用加载失败
    echo.
    echo 详细错误信息:
    python -c "from run_flask import app"
    goto :end
)
echo ✅ Flask应用可以正常加载
echo.

echo ========================================
echo 6. 测试WebSocket启动
echo ========================================
echo 尝试导入WebSocket模块...
python -c "from app.services.websocket_manager import start_websocket_server; print('WebSocket模块加载成功')"
if errorlevel 1 (
    echo ❌ WebSocket模块加载失败
    echo.
    echo 详细错误信息:
    python -c "from app.services.websocket_manager import start_websocket_server"
    goto :end
)
echo ✅ WebSocket模块可以正常加载
echo.

echo ========================================
echo 7. 尝试启动服务（测试模式）
echo ========================================
echo.
echo 现在将尝试启动服务...
echo 如果启动失败，请查看错误信息
echo.
pause

echo 启动Flask服务器（新窗口）...
start "Flask服务器" cmd /k "python run_flask.py --port 5000 --debug"
echo.

timeout /t 5 /nobreak

echo 检查Flask是否启动...
netstat -ano | findstr :5000
if errorlevel 1 (
    echo ❌ Flask服务器未能启动，请查看Flask窗口的错误信息
) else (
    echo ✅ Flask服务器已启动
)
echo.

echo 启动WebSocket服务器（新窗口）...
start "WebSocket服务器" cmd /k "python start_websocket.py"
echo.

timeout /t 3 /nobreak

echo 检查WebSocket是否启动...
netstat -ano | findstr :8765
if errorlevel 1 (
    echo ❌ WebSocket服务器未能启动，请查看WebSocket窗口的错误信息
) else (
    echo ✅ WebSocket服务器已启动
)
echo.

:end
echo ========================================
echo 诊断完成
echo ========================================
echo.
echo 💡 提示:
echo   - 如果服务未启动，请查看弹出窗口中的错误信息
echo   - 如果有端口被占用，请先关闭占用端口的程序
echo   - 如果依赖缺失，请运行 install_dependencies.bat
echo.

pause
