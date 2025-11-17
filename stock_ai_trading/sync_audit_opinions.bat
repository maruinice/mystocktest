@echo off
echo.
echo ================================================================
echo Sync Audit Opinions Data (3 Years)
echo ================================================================
echo.
echo This will sync audit opinions for the last 3 years.
echo Query by stock code from stock_basic table.
echo API Rate: 1.2 seconds per call (50 calls/minute)
echo Estimated time: 2 hours for 5000+ stocks
echo.
echo Usage:
echo   - Full sync: sync_audit_opinions.bat
echo   - Continue from position: sync_audit_opinions.bat 60
echo   - Quick continue: continue_sync_audit.bat
echo.
pause
echo.
python sync_audit_opinions.py %1
echo.
pause
