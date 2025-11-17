@echo off
chcp 65001 >nul
cls
echo.
echo ================================================================
echo              数据自动同步处理
echo ================================================================
echo.

:check_data
echo [1/4] 检查当前数据状态...
echo ----------------------------------------------------------------
python check_data.py
echo.

echo ----------------------------------------------------------------
echo.
echo 检测到表是空的，开始自动同步...
echo.
timeout /t 2 /nobreak >nul

:sync_data
echo [2/4] 开始同步数据（这可能需要1-2分钟）...
echo ----------------------------------------------------------------
echo.
python force_sync.py
echo.

:verify_data
echo [3/4] 验证同步结果...
echo ----------------------------------------------------------------
python check_data.py
echo.

:summary
echo [4/4] 同步完成！
echo ----------------------------------------------------------------
echo.
echo 数据同步处理完成
echo.
echo 请查看上面的结果：
echo    - 如果看到"记录数: 31"等数字，说明同步成功
echo    - 如果还是"记录数: 0"，请查看错误信息
echo.
echo 常见问题：
echo    1. Tushare Token未配置 - 检查 .env 文件
echo    2. 积分不足 - 访问 tushare.pro 查看积分
echo    3. 今天是非交易日 - 涨跌停数据为空是正常的
echo.
echo 详细日志位置: logs\flask_api.log
echo.

pause
