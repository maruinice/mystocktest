@echo off
echo.
echo ================================================================
echo Sync Financial Indicators Data (3 Years)
echo ================================================================
echo.
echo This will sync financial indicators for all stocks.
echo Estimated time: 30-60 minutes
echo.
echo Usage:
echo   - Full sync: sync_financial_indicators.bat
echo   - Continue from position: sync_financial_indicators.bat 670
echo   - Quick continue: continue_sync_financial.bat
echo.
pause
echo.
python sync_financial_indicators.py %1
echo.
pause
