@echo off
chcp 65001 >nul
echo.
echo ================================================================
echo   数据找不到？一键解决
echo ================================================================
echo.

echo [步骤1] 检查当前数据状态...
echo.
python check_data.py
echo.

echo ================================================================
echo.
echo 看到上面的结果了吗？
echo.
echo 如果显示"表是空的"或"记录数: 0"，
echo 说明需要同步数据。
echo.
set /p continue="是否继续同步数据？(Y/N): "

if /i not "%continue%"=="Y" (
    echo.
    echo 已取消。
    pause
    exit /b
)

echo.
echo [步骤2] 强制同步数据...
echo.
echo 这可能需要1-2分钟，请耐心等待...
echo.
python force_sync.py
echo.

echo ================================================================
echo.
echo [步骤3] 再次检查数据...
echo.
python check_data.py
echo.

echo ================================================================
echo.
echo 完成！
echo.
echo 如果现在看到有数据了，说明同步成功。
echo 如果还是没有数据，请查看上面的错误信息。
echo.
echo 常见问题：
echo 1. Tushare Token未配置或无效
echo 2. 积分不足
echo 3. 今天是非交易日（涨跌停、停复牌数据为空是正常的）
echo.
pause
