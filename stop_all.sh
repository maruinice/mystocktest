#!/bin/bash
# ===================================================================
# 一键关闭整个项目服务脚本
# 功能：停止所有后端和前端服务
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
BACKEND_DIR="${PROJECT_ROOT}/stock_ai_trading"
FRONTEND_DIR="${PROJECT_ROOT}/stock-ai-frontend"
PID_DIR="${BACKEND_DIR}/.pids"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 停止进程（通过PID文件）
stop_by_pid_file() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            log_info "停止 ${service_name} (PID: ${pid})..."
            kill $pid 2>/dev/null || kill -9 $pid 2>/dev/null || true
            sleep 1
            if ! ps -p $pid > /dev/null 2>&1; then
                log_info "✓ ${service_name} 已停止"
                rm -f "$pid_file"
            else
                log_warn "✗ ${service_name} 停止失败，强制终止..."
                kill -9 $pid 2>/dev/null || true
                rm -f "$pid_file"
            fi
        else
            log_warn "${service_name} 进程不存在，清理PID文件"
            rm -f "$pid_file"
        fi
    else
        log_warn "${service_name} PID文件不存在"
    fi
}

# 停止进程（通过进程名）
stop_by_process_name() {
    local pattern=$1
    local service_name=$2
    
    local pids=$(pgrep -f "$pattern" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        log_info "停止 ${service_name}..."
        echo "$pids" | xargs kill 2>/dev/null || true
        sleep 2
        # 如果还在运行，强制终止
        local remaining=$(pgrep -f "$pattern" 2>/dev/null || true)
        if [ -n "$remaining" ]; then
            log_warn "强制终止 ${service_name}..."
            echo "$remaining" | xargs kill -9 2>/dev/null || true
        fi
        log_info "✓ ${service_name} 已停止"
    else
        log_info "✓ ${service_name} 未运行"
    fi
}

# 主函数
main() {
    echo "==================================================================="
    echo "🛑 迅龙AI股票交易系统 - 一键停止所有服务"
    echo "==================================================================="
    echo ""
    
    # 切换到项目根目录
    cd "${PROJECT_ROOT}"
    
    # 步骤1: 停止前端服务
    log_step "步骤 1/4: 停止前端服务..."
    cd "${FRONTEND_DIR}"
    
    # 通过PID文件停止
    stop_by_pid_file "${PID_DIR}/frontend.pid" "前端服务"
    
    # 通过进程名停止（备用方案）
    stop_by_process_name "npm run dev" "前端服务（进程名）"
    stop_by_process_name "vite" "Vite 开发服务器"
    
    # 步骤2: 停止后端 Python 服务
    log_step "步骤 2/4: 停止后端 Python 服务..."
    cd "${BACKEND_DIR}"
    
    # 停止 Flask API
    stop_by_pid_file "${PID_DIR}/flask.pid" "Flask API"
    stop_by_process_name "run_flask.py" "Flask API（进程名）"
    
    # 停止 WebSocket
    stop_by_pid_file "${PID_DIR}/websocket.pid" "WebSocket"
    stop_by_process_name "start_websocket.py" "WebSocket（进程名）"
    
    # 停止 Celery Worker
    stop_by_pid_file "${PID_DIR}/celery_worker.pid" "Celery Worker"
    stop_by_process_name "celery.*worker" "Celery Worker（进程名）"
    
    # 停止 Celery Beat
    stop_by_pid_file "${PID_DIR}/celery_beat.pid" "Celery Beat"
    stop_by_process_name "celery.*beat" "Celery Beat（进程名）"
    
    # 停止 Flower
    stop_by_process_name "celery.*flower" "Flower 监控"
    
    # 步骤3: 停止 Docker Compose 服务
    log_step "步骤 3/4: 停止 Docker Compose 服务..."
    cd "${BACKEND_DIR}"
    
    if docker info > /dev/null 2>&1; then
        log_info "停止 Docker Compose 服务..."
        docker compose down
        
        if [ $? -eq 0 ]; then
            log_info "✓ Docker Compose 服务已停止"
        else
            log_warn "✗ Docker Compose 服务停止时出现警告"
        fi
    else
        log_warn "Docker 未运行，跳过 Docker Compose 停止"
    fi
    
    # 步骤4: 清理PID文件
    log_step "步骤 4/4: 清理临时文件..."
    
    if [ -d "${PID_DIR}" ]; then
        rm -rf "${PID_DIR}"
        log_info "✓ PID 文件已清理"
    fi
    
    # 显示停止结果
    echo ""
    echo "==================================================================="
    echo "✅ 所有服务已停止"
    echo "==================================================================="
    echo ""
    echo "💡 提示："
    echo "  - 使用 ./start_all.sh 启动所有服务"
    echo "  - 使用 ./restart_all.sh 重启所有服务"
    echo "==================================================================="
}

# 执行主函数
main "$@"

