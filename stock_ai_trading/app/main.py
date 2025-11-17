"""
Stock AI Trading - Flask API Application Entry Point
统一使用Flask，移除FastAPI重复
"""
# 注释掉FastAPI相关导入
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from werkzeug.exceptions import HTTPException as FlaskHTTPException
import logging
# import uvicorn
import traceback
from contextlib import asynccontextmanager
from datetime import datetime
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.settings import settings
from app.core.database import create_tables

# 注释掉FastAPI路由
# from app.api.tushare_api import router as tushare_router
# from app.api.technical_indicators import router as indicators_router
# from app.api.performance import router as performance_router
# from app.api.scheduler import router as scheduler_router
# from app.api.llm_gateway import router as llm_gateway_router
# from app.api.ai_decision import router as ai_decision_router
# from app.api.trading import router as trading_router

# 新增的Flask API路由
try:
    from app.api.auth_api import auth_bp
    from app.api.data_api import data_bp
    from app.api.trade_api import trade_bp
    from app.api.strategy_api import strategy_bp
    from app.api.system_api import system_bp
    from app.api.data_sync_api import data_sync_bp  # 新增数据同步API
    from app.middleware.auth import AuthMiddleware
    from app.utils.jwt_utils import jwt_manager
    from app.config.config import Config
    from app.docs.swagger_config import init_swagger  # 添加Swagger配置导入
    FLASK_APIS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Flask APIs not available: {e}")
    FLASK_APIS_AVAILABLE = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 注释掉FastAPI相关代码
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """应用生命周期管理"""
#     # 启动时执行
#     logger.info("应用启动中...")
#     
#     # 创建数据库表
#     try:
#         create_tables()
#         logger.info("数据库表创建成功")
#     except Exception as e:
#         logger.error(f"数据库表创建失败: {e}")
#     
#     yield
#     
#     # 关闭时执行
#     logger.info("应用关闭中...")

# app = FastAPI(
#     title="AI Stock Trading System",
#     description="AI-powered automated stock trading system for A-shares with Tushare integration",
#     version="1.0.0",
#     docs_url="/docs",
#     redoc_url="/redoc",
#     lifespan=lifespan
# )

# Configure CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Configure this properly in production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# 全局异常处理器
# @app.exception_handler(HTTPException)
# async def http_exception_handler(request, exc):
#     """HTTP异常处理"""
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={
#             "success": False,
#             "message": exc.detail,
#             "error_code": exc.status_code
#         }
#     )

# @app.exception_handler(Exception)
# async def general_exception_handler(request, exc):
#     """通用异常处理"""
#     logger.error(f"未处理的异常: {exc}")
#     return JSONResponse(
#         status_code=500,
#         content={
#             "success": False,
#             "message": "服务器内部错误",
#             "error_code": 500
#         }
#     )

# 注册路由 - 注释掉FastAPI路由
# app.include_router(tushare_router)
# app.include_router(indicators_router)
# app.include_router(performance_router)
# app.include_router(scheduler_router)
# app.include_router(llm_gateway_router, prefix="/api/llm", tags=["LLM Gateway"])
# app.include_router(ai_decision_router, prefix="/api/decision", tags=["AI Decision"])
# app.include_router(trading_router, prefix="/api/trading", tags=["Trading Engine"])


def create_flask_app(config_name='development'):
    """创建Flask应用（新的API接口）"""
    if not FLASK_APIS_AVAILABLE:
        return None
        
    flask_app = Flask(__name__)
    
    # 加载配置
    flask_app.config.from_object(Config)
    
    # 配置CORS
    CORS(flask_app, 
         origins=["http://localhost:3000", "http://127.0.0.1:3000"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "X-API-Key"],
         supports_credentials=True)
    
    # 初始化JWT管理器 (使用自定义JWT管理器，无需init_app)
    # jwt_manager.init_app(flask_app)
    
    # 初始化Swagger文档
    try:
        swagger = init_swagger(flask_app)
        
        # 添加文档重定向路由
        @flask_app.route('/docs')
        def swagger_docs():
            return flask_app.redirect('/apidocs/')
            
        @flask_app.route('/docs/')
        def swagger_docs_slash():
            return flask_app.redirect('/apidocs/')
            
        logger.info("Swagger documentation initialized at /apidocs/")
    except Exception as e:
        logger.warning(f"Failed to initialize Swagger: {e}")
    
    # 注册中间件
    register_flask_middleware(flask_app)
    
    # 注册蓝图
    register_flask_blueprints(flask_app)
    
    # 注册错误处理器
    register_flask_error_handlers(flask_app)
    
    return flask_app


def register_flask_middleware(flask_app):
    """注册Flask中间件"""
    auth_middleware = AuthMiddleware()
    
    @flask_app.before_request
    def before_request():
        """请求前处理"""
        g.start_time = datetime.now()
        
        if request.method == 'OPTIONS':
            return
        
        # 跳过公开端点的认证
        public_endpoints = [
            '/api/auth/login',
            '/api/auth/register',
            '/api/system/health',
            '/api/system/status',
            '/docs',
            '/apidocs',
            '/'
        ]
        
        # 跳过以下路径前缀的认证
        public_prefixes = [
            '/static',
            '/apidocs',
            '/flasgger_static',
            '/api/data-sync'  # 临时：数据同步API不需要认证（用于调试）
        ]
        
        if request.path in public_endpoints:
            return
            
        for prefix in public_prefixes:
            if request.path.startswith(prefix):
                return
        
        try:
            auth_middleware.process_request()
        except Exception as e:
            flask_app.logger.error(f"认证中间件错误: {str(e)}")
            return jsonify({
                'error': 'authentication_error',
                'message': str(e)
            }), 401


def register_flask_blueprints(flask_app):
    """注册Flask蓝图"""
    api_prefix = '/api'
    
    flask_app.register_blueprint(auth_bp, url_prefix=f'{api_prefix}/auth')
    flask_app.register_blueprint(data_bp, url_prefix=f'{api_prefix}')
    flask_app.register_blueprint(trade_bp, url_prefix=f'{api_prefix}/trade')
    flask_app.register_blueprint(strategy_bp, url_prefix=f'{api_prefix}/strategies')
    flask_app.register_blueprint(system_bp, url_prefix=f'{api_prefix}/system')
    flask_app.register_blueprint(data_sync_bp, url_prefix=f'{api_prefix}/data-sync')


def register_flask_error_handlers(flask_app):
    """注册Flask错误处理器"""
    
    @flask_app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'bad_request',
            'message': '请求参数错误'
        }), 400
    
    @flask_app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'unauthorized',
            'message': '未授权访问'
        }), 401
    
    @flask_app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'not_found',
            'message': '资源未找到'
        }), 404
    
    @flask_app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'internal_server_error',
            'message': '内部服务器错误'
        }), 500


# 创建Flask应用实例
flask_app = create_flask_app() if FLASK_APIS_AVAILABLE else None

# 注释掉FastAPI路由，改为Flask路由
# @app.get("/")
# async def root():
#     """Root endpoint"""
#     return {
#         "message": "AI Stock Trading System is running", 
#         "version": "1.0.0",
#         "status": "running",
#         "features": ["Tushare数据集成", "AI交易策略", "风险管理", "实时监控"]
#     }

# @app.get("/health")
# async def health_check():
#     """Health check endpoint"""
#     try:
#         from app.core.database import db_manager
#         from app.core.redis_client import redis_client
#         
#         # 检查数据库连接
#         db_status = db_manager.check_connection()
#         
#         # 检查Redis连接
#         redis_status = redis_client.ping()
#         
#         return {
#             "status": "healthy" if db_status and redis_status else "unhealthy",
#             "database": "connected" if db_status else "disconnected",
#             "redis": "connected" if redis_status else "disconnected",
#             "services": {
#                 "tushare_api": "available",
#                 "celery_worker": "running",
#                 "data_sync": "active"
#             }
#         }
#     except Exception as e:
#         logger.error(f"健康检查失败: {e}")
#         return {
#             "status": "unhealthy",
#             "error": str(e)
#         }

if __name__ == "__main__":
    if flask_app:
        logger.info("启动Flask服务器在 0.0.0.0:5000")
        flask_app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True
        )
    else:
        logger.error("Flask应用创建失败，请检查依赖")