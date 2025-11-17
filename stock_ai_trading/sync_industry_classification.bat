@echo off
echo.
echo ================================================================
echo Sync Industry Classification Data (SW2021)
echo ================================================================
echo.
echo This will sync Shenwan industry classification for all stocks.
echo Classification levels: L1 (Primary), L2 (Secondary), L3 (Tertiary)
echo.
echo Method: Get industry list, then fetch members for each industry
echo API Calls: ~200 calls (31 L1 + 134 L2 + 346 L3 industries)
echo Estimated time: 5-10 minutes
echo.
pause
echo.
python sync_industry_classification.py
echo.
pause
