#!/bin/bash
# ===================================================================
# 一键重启整个项目服务脚本
# 功能：先停止所有服务，再启动所有服务
# 创建时间：2025-11-20
# ===================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_ROOT="/home/meiming/source_code/xl_ai_stock_trading"
STOP_SCRIPT="${PROJECT_ROOT}/stop_all.sh"
START_SCRIPT="${PROJECT_ROOT}/start_all.sh"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 主函数
main() {
    echo "==================================================================="
    echo "🔄 股票AI交易系统 - 一键重启所有服务"
    echo "==================================================================="
    echo ""
    
    # 切换到项目根目录
    cd "${PROJECT_ROOT}"
    
    # 步骤1: 停止所有服务
    log_step "步骤 1/2: 停止所有服务..."
    if [ -f "${STOP_SCRIPT}" ]; then
        bash "${STOP_SCRIPT}"
    else
        log_info "停止脚本不存在，手动停止服务..."
        # 手动停止逻辑
        pkill -f "run_flask.py" 2>/dev/null || true
        pkill -f "start_websocket.py" 2>/dev/null || true
        pkill -f "celery.*worker" 2>/dev/null || true
        pkill -f "celery.*beat" 2>/dev/null || true
        pkill -f "celery.*flower" 2>/dev/null || true
        pkill -f "npm run dev" 2>/dev/null || true
        cd "${PROJECT_ROOT}/stock_ai_trading"
        docker compose down 2>/dev/null || true
    fi
    
    # 等待服务完全停止
    log_info "等待服务完全停止（5秒）..."
    sleep 5
    
    # 步骤2: 启动所有服务
    log_step "步骤 2/2: 启动所有服务..."
    if [ -f "${START_SCRIPT}" ]; then
        bash "${START_SCRIPT}"
    else
        log_info "启动脚本不存在，请手动启动服务"
        exit 1
    fi
    
    echo ""
    echo "==================================================================="
    echo "🎉 服务重启完成！"
    echo "==================================================================="
}

# 执行主函数
main "$@"

