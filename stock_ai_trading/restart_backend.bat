@echo off
echo ========================================
echo   重启后端服务
echo ========================================
echo.

echo [1/3] 停止现有Python进程...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak > nul
echo.

echo [2/3] 启动Flask服务...
start "Flask Backend" cmd /k "cd /d d:\code\AIgogogo\stock_ai_trading && python app/main.py"
timeout /t 5 /nobreak > nul
echo.

echo [3/3] 测试API...
curl http://127.0.0.1:5000/api/system/health
echo.
echo.
curl http://127.0.0.1:5000/api/data-sync/sync/status
echo.
echo.

echo ========================================
echo   后端服务已重启！
echo   Flask运行在: http://127.0.0.1:5000
echo ========================================
pause
