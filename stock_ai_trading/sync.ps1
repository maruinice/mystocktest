# Data Sync Script
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "数据同步工具" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "正在同步数据..." -ForegroundColor Yellow
Write-Host ""

python force_sync.py

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "检查结果..." -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

python check_data.py

Write-Host ""
Write-Host "完成！" -ForegroundColor Green
Write-Host ""
Read-Host "按回车键退出"
