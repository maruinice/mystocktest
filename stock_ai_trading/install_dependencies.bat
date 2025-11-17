@echo off
chcp 65001 >nul
title 安装项目依赖

echo ========================================
echo 📦 安装股票AI交易系统依赖包
echo ========================================
echo.

:: 切换到脚本目录
cd /d "%~dp0"

:: 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python
    pause
    exit /b 1
)

echo ✅ Python环境检查通过
python --version
echo.

:: 激活虚拟环境（如果存在）
if exist "%~dp0.venv\Scripts\activate.bat" (
    echo 🔧 激活虚拟环境...
    call "%~dp0.venv\Scripts\activate.bat"
) else if exist "%~dp0..\.venv\Scripts\activate.bat" (
    echo 🔧 激活上级目录虚拟环境...
    call "%~dp0..\.venv\Scripts\activate.bat"
) else (
    echo ⚠️ 未检测到虚拟环境
    echo.
    set /p CREATE_VENV="是否创建虚拟环境? (y/n): "
    if /i "%CREATE_VENV%"=="y" (
        echo 📦 创建虚拟环境...
        python -m venv .venv
        call "%~dp0.venv\Scripts\activate.bat"
        echo ✅ 虚拟环境创建成功
    )
)
echo.

:: 升级pip
echo 📦 升级pip...
python -m pip install --upgrade pip
echo.

:: 安装依赖
echo 📦 安装项目依赖...
echo.

if exist "%~dp0requirements.txt" (
    echo 正在安装 requirements.txt 中的依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 安装失败，请检查错误信息
        pause
        exit /b 1
    )
    echo ✅ requirements.txt 依赖安装完成
) else (
    echo ⚠️ 未找到 requirements.txt
)

echo.
echo ========================================
echo 🎉 依赖安装完成!
echo ========================================
echo.
echo 现在可以运行 start_services.bat 启动服务
echo.

pause
