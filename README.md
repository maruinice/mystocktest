# Stock AI Trading 系统

面向 A 股市场的 AI 驱动股票交易系统，包含 Python 后端（Flask）、Vue3 + TypeScript 前端，以及数据同步与实时推送能力。支持 Tushare 数据源、策略管理、交易模拟、风险控制与 AI 决策模块，并提供 Swagger 接口文档与 Docker 一键部署。

## 项目结构

- `stock_ai_trading/` 后端（Flask）与数据同步脚本、任务队列、Docker 配置
- `stock-ai-frontend/` 前端（Vue3 + Vite）
- `stock_ai_trading/.env.example` 后端环境变量示例（复制为 `.env`）
- `stock-ai-frontend/.env.development`、`.env.production` 前端环境变量示例

## 功能概述

- 用户认证与权限：JWT 令牌、登录注册、路由守卫
- 股票数据：基础信息、行情、财务数据、技术指标计算
- 策略管理：策略创建、信号生成、回测与性能评估
- 交易模拟：下单、撤单、持仓与订单管理
- AI 决策：调用 LLM（DeepSeek/OpenAI）生成策略与风险提示
- 数据同步：批量导入与增量更新（Tushare），定时任务（Celery Beat）
- 实时推送：WebSocket 推送行情、订单、风险告警
- 系统监控：健康检查、日志、速率限制、Swagger 文档

## 开发环境与依赖

- 后端：`Python >= 3.10`，`MySQL 8`，`Redis 7`（推荐 Docker）
- 前端：`Node.js >= 18`，`npm >= 8`

后端主要依赖（节选）：`flask`、`flasgger`、`sqlalchemy`、`pymysql`、`redis`、`celery`、`tushare`、`pandas`、`openai`、`langchain`

前端主要依赖：`vue`、`pinia`、`vue-router`、`element-plus`、`echarts`、`axios`、`vite`

## 快速启动（Windows）

### 1. 启动后端与 WebSocket（使用脚本）

- 进入后端目录：`cd stock_ai_trading`
- 首次运行准备：
  - 创建虚拟环境并安装依赖：`python -m venv .venv && .\\.venv\\Scripts\\pip install -r requirements.txt`
  - 复制环境变量示例：将 `.env.example` 复制为 `.env` 并按下文“环境变量与 Token 配置”填写
- 启动所有服务：运行 `start_services.bat`
- 停止所有服务：运行 `stop_services.bat`
- 接口文档：`http://localhost:5000/apidocs/` 或 `http://localhost:5000/docs/`

说明：脚本将分别启动 Flask API（端口 `5000`）与 WebSocket（端口 `8765`），并自动进行端口占用检查。

### 2. 启动前端（Vue3 + Vite）

- 进入前端目录并安装依赖：`cd stock-ai-frontend && npm install`
- 按需调整开发环境变量：
  - `stock-ai-frontend/.env.development` 中 `VITE_API_BASE_URL=http://localhost:5000/api`
  - `VITE_WS_URL=ws://localhost:8765`
- 启动开发服务器：`npm run dev`
- 访问地址：`http://localhost:5173`

## 快速启动（Linux/Ubuntu）

### 1. 系统准备

确保系统已安装以下软件：
- `conda`（Miniconda 或 Anaconda）
- `Docker` 和 `docker-compose`
- `MySQL` 客户端工具（可选，用于调试）

```bash
# 安装 Docker Compose（如果尚未安装）
sudo apt install docker-compose

# 确认安装
docker --version
docker-compose --version
```

### 2. 启动后端与 WebSocket

#### 步骤1：创建 Conda 环境并安装依赖

```bash
# 进入后端目录
cd /path/to/xl_ai_stock_trading/stock_ai_trading

# 创建 conda 环境
conda create -n stock_trading python=3.10 -y

# 激活环境
conda activate stock_trading

# 安装 Python 依赖
pip install -r requirements.txt

# 安装额外必需的包
pip install PyJWT psutil flask-jwt-extended flask-sqlalchemy flask-migrate
```

#### 步骤2：配置环境变量

```bash
# 复制环境变量示例
cp .env.example .env

# 编辑 .env 文件，至少配置以下项：
# - DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/stock_trading
# - REDIS_URL=redis://localhost:6379/0
# - SECRET_KEY（设置强密码）
# - JWT_SECRET_KEY（设置强密码）
# - DEEPSEEK_API_KEY（从 DeepSeek 平台获取）
# - TUSHARE_TOKEN（从 Tushare 获取）
```

#### 步骤3：启动 MySQL 和 Redis

```bash
# 使用 Docker Compose 启动 MySQL 和 Redis
docker-compose up -d mysql redis

# 等待服务启动（约10秒）
sleep 10

# 验证服务状态
docker-compose ps
```

#### 步骤4：创建测试用户

```bash
# 运行以下 Python 脚本创建测试用户
python -c "
import pymysql
import hashlib
import secrets

# 连接数据库
conn = pymysql.connect(host='localhost', user='root', password='YOUR_PASSWORD', database='stock_trading')
cursor = conn.cursor()

# 生成密码哈希
password = 'admin123456'
salt = secrets.token_hex(16)
password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
full_hash = salt + password_hash.hex()

# 删除旧用户（如果存在）
cursor.execute('DELETE FROM users WHERE email = \"admin@example.com\"')

# 创建新用户
cursor.execute('''
    INSERT INTO users (username, email, password_hash, full_name, role, status)
    VALUES (\"admin\", \"admin@example.com\", %s, \"Admin User\", \"admin\", \"active\")
''', (full_hash,))

conn.commit()
conn.close()

print('✓ 测试用户已创建: username=admin, email=admin@example.com, password=admin123')
"
```

#### 步骤5：启动 Flask API 和 WebSocket 服务

```bash
# 使用后台方式启动 Flask API
nohup python run_flask.py --host 0.0.0.0 --port 5000 > flask.log 2>&1 &
echo "Flask API started, PID: $!"

# 等待 Flask 启动
sleep 3

# 启动 WebSocket 服务
nohup python start_websocket.py > websocket.log 2>&1 &
echo "WebSocket started, PID: $!"

# 验证服务
curl http://localhost:5000/
echo "Backend services are running"
```

**提示**: 您也可以使用提供的便捷脚本 `start_backend_linux.sh`：

```bash
# 赋予执行权限
chmod +x start_backend_linux.sh

# 运行脚本
./start_backend_linux.sh
```

#### 查看日志

```bash
# 查看 Flask API 日志
tail -f flask.log

# 查看 WebSocket 日志
tail -f websocket.log

# 查看 Docker 服务日志
docker-compose logs -f mysql redis
```

### 3. 启动前端（Vue3 + Vite）

```bash
# 进入前端目录
cd /path/to/xl_ai_stock_trading/stock-ai-frontend

# 安装依赖
npm install

# 启动开发服务器（后台运行）
nohup npm run dev > frontend.log 2>&1 &

# 查看日志确认端口
tail -n 20 frontend.log
```

**注意**: 前端可能在端口 `3000` 或 `5173` 上运行，请查看日志确认实际端口。

访问地址：`http://localhost:3000` 或 `http://localhost:5173`

### 4. 访问系统

- **前端应用**: `http://localhost:3000` 或 `http://localhost:5173`
- **API 文档**: `http://localhost:5000/apidocs/` 或 `http://localhost:5000/docs/`
- **测试账号**: 
  - 邮箱: `admin@example.com`
  - 密码: `admin123`

### 5. 停止服务

```bash
# 停止后端服务（记录启动时的 PID）
kill PID_OF_FLASK PID_OF_WEBSOCKET

# 或者查找并停止所有相关进程
pkill -f run_flask.py
pkill -f start_websocket.py

# 停止前端服务
pkill -f "npm run dev"

# 停止 Docker 服务
cd stock_ai_trading
docker-compose down
```

### 常见问题

1. **端口被占用**: 检查是否有其他服务占用 5000、8765、3000 端口
   ```bash
   sudo lsof -i :5000
   sudo lsof -i :8765
   sudo lsof -i :3000
   ```

2. **数据库连接失败**: 确认 MySQL 服务已启动且 `.env` 中的密码正确
   ```bash
   docker-compose ps
   ```

3. **前端无法连接后端**: 检查 `.env.development` 中的 API 地址是否正确

4. **登录失败**: 确保已正确创建测试用户，密码哈希格式匹配

详细问题和解决方案请参考：`issue/solution.md`

## 部署（Docker Compose，可选）

- 进入后端目录：`cd stock_ai_trading`
- 根据需要将 `.env.example` 复制为 `.env` 并填写必要变量
- 启动：`docker-compose up -d`

包含服务：`Flask API (5000)`、`MySQL (3306)`、`Redis (6379)`、`Celery Worker/Beat`、`Flower (5555)`

## 环境变量与 Token 配置

后端环境变量文件：`stock_ai_trading/.env`（参考 `.env.example`）

- 基础配置：
  - `DATABASE_URL` 示例：`mysql+pymysql://root:123456@localhost:3306/stock_trading`
  - `REDIS_URL` 示例：`redis://localhost:6379/0`
  - `SECRET_KEY`、`JWT_SECRET_KEY` 请设置为高强度随机字符串

- LLM/AI：
  - `DEEPSEEK_API_KEY`（必选用于主模型）
    - 申请地址：登录 DeepSeek 平台的 API Keys 页面（示例入口：https://www.deepseek.com 或 https://platform.deepseek.com）
    - 默认 Base URL：`https://api.deepseek.com/v1`
  - `OPENAI_API_KEY`（可选）
    - 申请地址：`https://platform.openai.com/account/api-keys`

- 行情与数据源：
  - `TUSHARE_TOKEN`（必选用于 Tushare 数据同步）
    - 申请地址：`https://tushare.pro`（登录后“个人中心”获取 Token）
  - `STOCK_API_KEY`、`STOCK_API_BASE_URL`（可选第三方数据源，默认 `https://api.deepseek.com/v1`）

- WebSocket：
  - `WS_PORT`（默认 `8765`）与前端 `VITE_WS_URL` 对应

前端环境变量文件：

- `stock-ai-frontend/.env.development`
  - `VITE_API_BASE_URL=http://localhost:5000/api`
  - `VITE_WS_URL=ws://localhost:8765`
- `stock-ai-frontend/.env.production`（生产构建时使用，可根据部署地址调整）

安全建议：请勿将 `.env`、真实 Token 与密钥提交到 Git 仓库。

## 数据库初始化与同步

- 初始建库：`stock_ai_trading/init.sql`（Docker Compose 已自动挂载执行）
- 迁移脚本：`run_migration.py`、`run_core_migration.py`
- Tushare 同步：可使用 `quick_start.py`、`init_screening_data.py`、`continue_sync_audit.py` 等脚本按需同步

## 常用端点

- 认证：`/api/auth/*`（登录、注册、刷新、登出、用户信息）
- 数据：`/api/data/*` 或 `/api/stocks/*`（基础、行情、财务、技术指标）
- 交易：`/api/trade/*`（下单、撤单、订单与持仓）
- 策略：`/api/strategies/*` 或 `/api/strategy/*`（信号、回测、管理）
- 系统：`/api/system/*`（健康、状态、日志、指标）
- 文档：`/apidocs/` 或 `/docs/`（Swagger UI）

## Git 初始化与提交建议

- 初始化：`git init && git add . && git commit -m "init: stock ai trading"`
- 建议在根目录添加 `.gitignore`，确保忽略：
  - `.env`、`*.env*`、`logs/`、`__pycache__/`、`.venv/`、`node_modules/`、`dist/`

## 生产部署提示

- 使用 `Production` 配置并确保设置：`SECRET_KEY`、`JWT_SECRET_KEY`、`DATABASE_URL`
- 反向代理：建议使用 Nginx/Tengine，对 `/api` 与 WebSocket 做转发
- 证书与安全：开启 HTTPS，妥善保管密钥；限制管理接口的访问来源

## 许可证

MIT