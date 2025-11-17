@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Stock AI - Stop Services

echo ===== Stop All Services =====
echo.

REM Use PowerShell to kill processes bound to ports and by command line
powershell -NoProfile -Command "$ports=(5000..5002)+(8765..8767); foreach($p in $ports){ try{ $pids=Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue | Where-Object { $_.State -in @('Listen','Established') } | Select-Object -ExpandProperty OwningProcess | Sort-Object -Unique; foreach($pid in $pids){ try{ Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue }catch{} } }catch{} }"
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and (($_.CommandLine -like '*run_flask.py*') -or ($_.CommandLine -like '*start_flask_only.py*') -or ($_.CommandLine -like '*start_websocket.py*')) } | ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {} }"
powershell -NoProfile -Command "Get-Process python,flask,websockets -ErrorAction SilentlyContinue | ForEach-Object { try { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue } catch {} }"

echo.
echo ===== Stop Commands Executed =====
echo.

echo Port status:
powershell -NoProfile -Command "foreach($p in 5000..5002){ if(Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue){ Write-Host ('Port ' + $p + ' occupied') } else { Write-Host ('Port ' + $p + ' free') } }"
powershell -NoProfile -Command "foreach($p in 8765..8767){ if(Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue){ Write-Host ('Port ' + $p + ' occupied') } else { Write-Host ('Port ' + $p + ' free') } }"

echo.
pause
exit /b 0