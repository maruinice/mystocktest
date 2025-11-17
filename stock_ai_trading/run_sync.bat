@echo off
echo.
echo ================================================================
echo Data Sync Tool
echo ================================================================
echo.
echo Syncing data, please wait...
echo.

python force_sync.py

echo.
echo ================================================================
echo Checking results...
echo ================================================================
echo.

python check_data.py

echo.
echo Done!
echo.
pause
