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