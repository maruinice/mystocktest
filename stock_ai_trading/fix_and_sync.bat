@echo off
echo.
echo ================================================================
echo Step 1: Check table structure
echo ================================================================
echo.
python check_table_structure.py
echo.
echo.
echo ================================================================
echo Step 2: Run sync again
echo ================================================================
echo.
python force_sync.py
echo.
echo.
echo ================================================================
echo Step 3: Check data
echo ================================================================
echo.
python check_data.py
echo.
pause
