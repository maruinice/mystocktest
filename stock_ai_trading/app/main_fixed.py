"""
Stock AI Trading - API Application Entry Point
使用FastAPI + WSGIMiddleware挂载Flask应用，解决重复问题
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.responses import JSONResponse
import logging
import uvicorn
import traceback
from contextlib import asynccontextmanager
from datetime import datetime
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.settings import settings
from app.core.database import create_tables
from app.api.tushare_api import router as tushare_router
from app.api.technical_indicators import router as indicators_router
from app.api.performance import router as performance_router
from app.api.scheduler import router as scheduler_router
from app.api.llm_gateway import router as llm_gateway_router
from app.api.ai_decision import router as ai_decision_router
from app.api.trading import router as trading_router

# Flask应用相关导入
try:
    from flask import Flask
    from flask_cors import CORS
    from app.api.auth_api import auth_bp
    from app.api.data_api import data_bp
    from app.api.trade_api import trade_bp
    from app.api.strategy_api import strategy_bp
    from app.api.system_api import system_bp
    from app.middleware.auth import AuthMiddleware
    from app.utils.jwt_utils import jwt_manager
    from app.config.config import Config
    FLASK_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Flask components not available: {e}")
    FLASK_AVAILABLE = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def create_flask_app():
    """创建Flask应用用于认证等API"""
    if not FLASK_AVAILABLE:
        return None
        
    flask_app = Flask(__name__)
    
    # 配置Flask
    flask_app.config['SECRET_KEY'] = 'your-secret-key'
    
    # 配置CORS
    CORS(flask_app, 
         origins=["http://localhost:3000", "http://127.0.0.1:3000"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "X-API-Key"],
         supports_credentials=True)
    
    # 注册蓝图
    flask_app.register_blueprint(auth_bp, url_prefix='/api/auth')
    flask_app.register_blueprint(data_bp, url_prefix='/api')
    flask_app.register_blueprint(trade_bp, url_prefix='/api/trade')
    flask_app.register_blueprint(strategy_bp, url_prefix='/api/strategies')
    flask_app.register_blueprint(system_bp, url_prefix='/api/system')
    
    return flask_app

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("应用启动中...")
    
    # 创建数据库表
    try:
        create_tables()
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"数据库表创建失败: {e}")
    
    yield
    
    # 关闭时执行
    logger.info("应用关闭中...")

# 创建FastAPI应用
app = FastAPI(
    title="AI Stock Trading System",
    description="AI-powered automated stock trading system for A-shares with Tushare integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建Flask应用并挂载
flask_app = create_flask_app()
if flask_app:
    # 使用WSGIMiddleware挂载Flask应用
    app.mount("/", WSGIMiddleware(flask_app))
    logger.info("Flask应用已挂载到FastAPI")
else:
    logger.warning("Flask应用创建失败，将只使用FastAPI路由")

# 全局异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "error_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理"""
    logger.error(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "服务器内部错误",
            "error_code": 500
        }
    )

# 注册FastAPI路由
app.include_router(tushare_router)
app.include_router(indicators_router)
app.include_router(performance_router)
app.include_router(scheduler_router)
app.include_router(llm_gateway_router, prefix="/api/llm", tags=["LLM Gateway"])
app.include_router(ai_decision_router, prefix="/api/decision", tags=["AI Decision"])
app.include_router(trading_router, prefix="/api/trading", tags=["Trading Engine"])

@app.get("/fastapi")
async def fastapi_root():
    """FastAPI根路径"""
    return {
        "message": "AI Stock Trading System is running (FastAPI)", 
        "version": "1.0.0",
        "status": "running",
        "framework": "FastAPI + Flask",
        "features": ["Tushare数据集成", "AI交易策略", "风险管理", "实时监控"]
    }

@app.get("/fastapi/health")
async def fastapi_health_check():
    """FastAPI健康检查"""
    try:
        return {
            "status": "healthy",
            "framework": "FastAPI",
            "flask_mounted": flask_app is not None,
            "services": {
                "tushare_api": "available",
                "ai_decision": "available",
                "trading_engine": "available"
            }
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    logger.info("启动混合服务器 (FastAPI + Flask) 在 0.0.0.0:5000")
    uvicorn.run(
        "app.main_fixed:app",
        host='0.0.0.0',
        port=5000,
        reload=True,
        log_level="info"
    )