#!/bin/bash
# ===================================================================
# 一键启动整个项目服务脚本
# 功能：启动所有后端和前端服务
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
CONDA_ENV="stock_trading"

# PID文件目录
PID_DIR="${BACKEND_DIR}/.pids"
mkdir -p "${PID_DIR}"

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

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 未安装，请先安装"
        exit 1
    fi
}

# 检查端口是否被占用
check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :${port} -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        log_warn "端口 ${port} 已被占用（${service}），尝试停止..."
        # 尝试停止占用端口的进程
        lsof -ti:${port} | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# 检查服务是否运行
is_service_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            return 0
        else
            rm -f "$pid_file"
            return 1
        fi
    fi
    return 1
}

# 主函数
main() {
    echo "==================================================================="
    echo "🚀 迅龙AI股票交易系统 - 一键启动所有服务"
    echo "==================================================================="
    echo ""
    
    # 检查必要的命令
    log_step "检查系统环境..."
    check_command docker
    check_command conda
    check_command node
    check_command npm
    
    # 切换到项目根目录
    cd "${PROJECT_ROOT}"
    
    # 步骤1: 启动 Docker Compose 服务
    log_step "步骤 1/6: 启动 Docker Compose 服务（MySQL、Redis、Celery等）..."
    cd "${BACKEND_DIR}"
    
    # 检查 Docker 是否运行
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker 未运行，请先启动 Docker"
        exit 1
    fi
    
    # 启动 Docker Compose 服务（使用新版写法，不带连字符）
    # 注意：只启动基础设施服务（MySQL、Redis），Celery 服务可选
    log_info "启动 Docker 基础设施服务（MySQL、Redis）..."
    docker compose up -d mysql redis
    
    # 可选：启动 Celery 相关服务（如果需要在 Docker 中运行）
    # 默认情况下，为了开发调试方便，Celery 在本地 Conda 环境中运行
    if [ "${USE_DOCKER_CELERY:-false}" = "true" ]; then
        log_info "启动 Docker Celery 服务（Worker、Beat、Flower）..."
        docker compose up -d celery-worker celery-beat flower
    else
        log_info "跳过 Docker Celery 服务（将在本地 Conda 环境中启动）"
    fi
    
    if [ $? -eq 0 ]; then
        log_info "✓ Docker Compose 服务启动成功"
    else
        log_error "✗ Docker Compose 服务启动失败"
        exit 1
    fi
    
    # 等待服务就绪
    log_info "等待 Docker 服务就绪（10秒）..."
    sleep 10
    
    # 步骤2: 初始化并激活 Conda 环境
    log_step "步骤 2/6: 初始化 Conda 环境..."
    
    # 初始化 conda（尝试多种方式以确保兼容性）
    if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
        source "$HOME/miniconda3/etc/profile.d/conda.sh"
        log_info "✓ 从 miniconda3 初始化 Conda"
    elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
        source "$HOME/anaconda3/etc/profile.d/conda.sh"
        log_info "✓ 从 anaconda3 初始化 Conda"
    elif [ -f "/opt/conda/etc/profile.d/conda.sh" ]; then
        source "/opt/conda/etc/profile.d/conda.sh"
        log_info "✓ 从 /opt/conda 初始化 Conda"
    else
        # 尝试使用 conda shell hook
        eval "$(conda shell.bash hook 2>/dev/null)" || {
            log_error "无法初始化 Conda，请确保 Conda 已正确安装"
            exit 1
        }
        log_info "✓ 使用 conda shell hook 初始化"
    fi
    
    # 检查 conda 环境是否存在
    if ! conda env list | grep -q "^${CONDA_ENV} "; then
        log_error "Conda 环境 '${CONDA_ENV}' 不存在，请先创建："
        log_error "  conda create -n ${CONDA_ENV} python=3.10 -y"
        exit 1
    fi
    
    # 激活 conda 环境
    log_info "激活 Conda 环境: ${CONDA_ENV}..."
    conda activate ${CONDA_ENV}
    
    if [ $? -ne 0 ]; then
        log_error "激活 Conda 环境失败"
        exit 1
    fi
    
    # 验证 Python 路径
    PYTHON_PATH=$(which python)
    log_info "✓ Conda 环境已激活，Python 路径: ${PYTHON_PATH}"
    
    # 步骤3: 启动 Flask API 服务
    log_step "步骤 3/6: 启动 Flask API 服务（端口 5000）..."
    cd "${BACKEND_DIR}"
    
    check_port 5000 "Flask API"
    
    # 启动 Flask API（使用 conda 环境中的 Python）
    log_info "启动 Flask API 服务..."
    nohup python run_flask.py --host 0.0.0.0 --port 5000 > flask.log 2>&1 &
    FLASK_PID=$!
    echo $FLASK_PID > "${PID_DIR}/flask.pid"
    
    if is_service_running "${PID_DIR}/flask.pid"; then
        log_info "✓ Flask API 启动成功 (PID: ${FLASK_PID})"
    else
        log_error "✗ Flask API 启动失败，请查看日志: ${BACKEND_DIR}/flask.log"
        exit 1
    fi
    
    # 等待 Flask 启动
    sleep 5
    
    # 步骤4: 启动 WebSocket 服务
    log_step "步骤 4/6: 启动 WebSocket 服务（端口 8765）..."
    check_port 8765 "WebSocket"
    
    log_info "启动 WebSocket 服务..."
    nohup python start_websocket.py > websocket.log 2>&1 &
    WS_PID=$!
    echo $WS_PID > "${PID_DIR}/websocket.pid"
    
    if is_service_running "${PID_DIR}/websocket.pid"; then
        log_info "✓ WebSocket 启动成功 (PID: ${WS_PID})"
    else
        log_warn "✗ WebSocket 启动失败（可能未配置，继续执行）"
    fi
    
    sleep 2
    
    # 步骤5: 启动 Celery Worker 和 Beat
    log_step "步骤 5/6: 启动 Celery 服务（Worker、Beat）..."
    
    # 检查是否在 Docker 中运行 Celery
    if docker compose ps | grep -q "celery-worker.*Up"; then
        log_info "✓ Celery Worker 已在 Docker 中运行"
    else
        # 在本地 Conda 环境中启动 Celery Worker
        log_info "启动 Celery Worker（本地 Conda 环境）..."
        nohup celery -A app.tasks.celery_app worker --loglevel=info > celery_worker.log 2>&1 &
        CELERY_WORKER_PID=$!
        echo $CELERY_WORKER_PID > "${PID_DIR}/celery_worker.pid"
        
        if is_service_running "${PID_DIR}/celery_worker.pid"; then
            log_info "✓ Celery Worker 启动成功 (PID: ${CELERY_WORKER_PID})"
        else
            log_warn "✗ Celery Worker 启动失败（可能未配置，继续执行）"
        fi
    fi
    
    # 检查是否在 Docker 中运行 Celery Beat
    if docker compose ps | grep -q "celery-beat.*Up"; then
        log_info "✓ Celery Beat 已在 Docker 中运行"
    else
        # 在本地 Conda 环境中启动 Celery Beat
        log_info "启动 Celery Beat（本地 Conda 环境）..."
        nohup celery -A app.tasks.celery_app beat --loglevel=info > celery_beat.log 2>&1 &
        CELERY_BEAT_PID=$!
        echo $CELERY_BEAT_PID > "${PID_DIR}/celery_beat.pid"
        
        if is_service_running "${PID_DIR}/celery_beat.pid"; then
            log_info "✓ Celery Beat 启动成功 (PID: ${CELERY_BEAT_PID})"
        else
            log_warn "✗ Celery Beat 启动失败（可能未配置，继续执行）"
        fi
    fi
    
    # 步骤6: 启动前端服务
    log_step "步骤 6/6: 启动前端服务（Vue3）..."
    cd "${FRONTEND_DIR}"
    
    # 检查前端依赖
    if [ ! -d "node_modules" ]; then
        log_warn "前端依赖未安装，正在安装..."
        npm install
    fi
    
    check_port 5173 "前端服务"
    check_port 3000 "前端服务"
    
    log_info "启动前端开发服务器..."
    nohup npm run dev > frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "${PID_DIR}/frontend.pid"
    
    if is_service_running "${PID_DIR}/frontend.pid"; then
        log_info "✓ 前端服务启动成功 (PID: ${FRONTEND_PID})"
    else
        log_error "✗ 前端服务启动失败"
        exit 1
    fi
    
    # 等待前端启动
    sleep 5
    
    # 显示启动结果
    echo ""
    echo "==================================================================="
    echo "🎉 所有服务启动完成！"
    echo "==================================================================="
    echo ""
    echo "📊 服务访问地址："
    echo "  🌐 前端应用:     http://localhost:5173 或 http://localhost:3000"
    echo "  🔧 Flask API:    http://localhost:5000"
    echo "  📖 API 文档:     http://localhost:5000/apidocs/"
    echo "  📡 WebSocket:    ws://localhost:8765"
    echo "  🌸 Flower 监控:   http://localhost:5555"
    echo "  🗄️  MySQL:        localhost:3306"
    echo "  📦 Redis:        localhost:6379"
    echo ""
    echo "📝 日志文件位置："
    echo "  Flask API:       ${BACKEND_DIR}/flask.log"
    echo "  WebSocket:       ${BACKEND_DIR}/websocket.log"
    echo "  Celery Worker:   ${BACKEND_DIR}/celery_worker.log"
    echo "  Celery Beat:     ${BACKEND_DIR}/celery_beat.log"
    echo "  前端服务:        ${FRONTEND_DIR}/frontend.log"
    echo ""
    echo "💡 提示："
    echo "  - 使用 ./stop_all.sh 停止所有服务"
    echo "  - 使用 ./restart_all.sh 重启所有服务"
    echo "  - 查看日志: tail -f ${BACKEND_DIR}/flask.log"
    echo "==================================================================="
}

# 执行主函数
main "$@"

