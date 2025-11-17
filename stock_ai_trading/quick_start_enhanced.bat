@echo off
echo ========================================
echo   AI Stock Trading - Enhanced Setup
echo ========================================
echo.

echo [1/4] Creating enhanced database tables...
python init_enhanced_tables.py
if %errorlevel% neq 0 (
    echo ERROR: Failed to create tables
    pause
    exit /b 1
)
echo SUCCESS: Tables created
echo.

echo [2/4] Starting Flask service...
start "Flask Service" cmd /k "python app/main.py"
timeout /t 5 /nobreak > nul
echo SUCCESS: Service started at http://127.0.0.1:5000
echo.

echo [3/4] Syncing industry classification...
curl -X POST http://127.0.0.1:5000/api/data-sync/sync/industry -H "Content-Type: application/json" -d "{\"src\":\"SW2021\",\"level\":\"L1\"}"
echo.

echo [4/4] Syncing limit prices (last 30 days)...
curl -X POST http://127.0.0.1:5000/api/data-sync/sync/limit-prices -H "Content-Type: application/json" -d "{}"
echo.

echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Service URLs:
echo   - API: http://127.0.0.1:5000
echo   - Docs: http://127.0.0.1:5000/apidocs/
echo   - Sync Status: http://127.0.0.1:5000/api/data-sync/sync/status
echo.
echo Next Steps:
echo   1. Check sync status in browser
echo   2. Review DATA_SYNC_GUIDE.md for more info
echo   3. Set up scheduled tasks for daily sync
echo.
pause
