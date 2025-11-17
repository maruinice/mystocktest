@echo off
echo ========================================
echo   404错误修复脚本
echo ========================================
echo.

echo [步骤1/5] 检查数据库表...
python -c "from sqlalchemy import create_engine, text; from app.config.settings import settings; engine = create_engine(settings.DATABASE_URL); conn = engine.connect(); result = conn.execute(text('SHOW TABLES LIKE \"industry_classification\"')); print('表存在' if result.fetchone() else '表不存在'); conn.close()"
if %errorlevel% neq 0 (
    echo 数据库表不存在，正在创建...
    python init_enhanced_tables.py
    if %errorlevel% neq 0 (
        echo ERROR: 创建表失败
        pause
        exit /b 1
    )
)
echo SUCCESS: 数据库表检查完成
echo.

echo [步骤2/5] 验证Blueprint注册...
python -c "from app.main import create_flask_app; app = create_flask_app(); print('已注册的路由:'); [print(f'  {rule.rule}') for rule in app.url_map.iter_rules() if 'data-sync' in rule.rule]"
echo.

echo [步骤3/5] 测试API端点...
echo 启动临时服务器进行测试...
start "Temp Flask" cmd /k "python app/main.py"
timeout /t 5 /nobreak > nul

echo 测试API...
curl -s http://127.0.0.1:5000/api/system/health
echo.
curl -s http://127.0.0.1:5000/api/data-sync/sync/status
echo.

echo [步骤4/5] 检查前端配置...
echo 前端代理配置:
type ..\stock-ai-frontend\vite.config.ts | findstr /C:"proxy" /C:"target"
echo.

echo [步骤5/5] 生成诊断报告...
echo ========================================
echo   诊断报告
echo ========================================
echo.
echo 1. 数据库表: 已检查
echo 2. Blueprint: 已验证
echo 3. API端点: 已测试
echo 4. 前端配置: 已检查
echo.
echo 如果仍有问题，请检查:
echo - 后端服务是否在5000端口运行
echo - 前端服务是否在3000端口运行
echo - 是否已登录系统
echo - 浏览器控制台是否有错误
echo.
echo ========================================
pause
