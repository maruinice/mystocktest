@echo off
echo.
echo ================================================================
echo Setup Industry Classification Sync
echo ================================================================
echo.
echo This will setup and start the industry classification sync.
echo.
echo Step 1: Create database table
echo Step 2: Start sync process
echo.
pause
echo.

echo ================================================================
echo Step 1: Creating database table...
echo ================================================================
echo.
echo Please run the following SQL in your MySQL database:
echo.
type create_industry_table.sql
echo.
echo.
pause
echo.

echo ================================================================
echo Step 2: Starting sync process...
echo ================================================================
echo.
python sync_industry_classification.py
echo.
pause
