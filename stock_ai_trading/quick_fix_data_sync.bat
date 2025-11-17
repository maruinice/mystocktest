@echo off
chcp 65001 >nul
echo ========================================
echo 数据同步功能快速修复
echo ========================================
echo.

echo [步骤1] 停止现有服务...
echo 请手动关闭所有Flask服务窗口，然后按任意键继续...
pause >nul

echo.
echo [步骤2] 运行诊断脚本...
python diagnose_data_sync.py
echo.

echo [步骤3] 是否需要重启服务？(Y/N)
set /p restart="请输入: "

if /i "%restart%"=="Y" (
    echo.
    echo [步骤4] 启动服务...
    call start_services.bat
    echo.
    echo 等待服务启动（10秒）...
    timeout /t 10 /nobreak >nul
    
    echo.
    echo [步骤5] 再次运行诊断...
    python diagnose_data_sync.py
)

echo.
echo ========================================
echo 修复完成！
echo ========================================
pause
