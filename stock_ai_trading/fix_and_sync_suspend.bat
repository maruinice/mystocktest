@echo off
echo.
echo ================================================================
echo Fix and Sync Suspend Data
echo ================================================================
echo.
echo Step 1: Fix table structure
echo ----------------------------------------------------------------
python fix_suspend_table.py
echo.
echo.
echo Step 2: Sync suspend data (3 years)
echo ----------------------------------------------------------------
python sync_suspend_only.py
echo.
pause
