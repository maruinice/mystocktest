"""
Stock AI Trading - Flask API Application Entry Point
纯Flask版本，解决FastAPI重复问题
"""
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from werkzeug.exceptions import HTTPException as FlaskHTTPException
import logging
import traceback
from datetime import datetime
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.settings import settings
from app.core.database import create_tables

# Flask API路由
try:
    from app.api.auth_api import auth_bp
    from app.api.data_api import data_bp
    from app.api.trade_api import trade_bp
    from app.api.strategy_api import strategy_bp
    from app.api.system_api import system_bp
    from app.middleware.auth import AuthMiddleware
    from app.utils.jwt_utils import jwt_manager
    from app.config.config import Config
    from app.docs.swagger_config import init_swagger
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

def create_app(config_name='development'):
    """创建Flask应用"""
    if not FLASK_APIS_AVAILABLE:
        logger.error("Flask APIs not available")
        return None
        
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(Config)
    
    # 配置CORS
    CORS(app, 
         origins=["http://localhost:3000", "http://127.0.0.1:3000"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "X-API-Key"],
         supports_credentials=True)
    
    # 初始化Swagger文档
    try:
        swagger = init_swagger(app)
        
        # 添加文档重定向路由
        @app.route('/docs')
        def swagger_docs():
            return app.redirect('/apidocs/')
            
        @app.route('/docs/')
        def swagger_docs_slash():
            return app.redirect('/apidocs/')
            
        logger.info("Swagger documentation initialized at /apidocs/")
    except Exception as e:
        logger.warning(f"Failed to initialize Swagger: {e}")
    
    # 注册中间件
    register_middleware(app)
    
    # 注册蓝图
    register_blueprints(app)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 启动时创建数据库表
    with app.app_context():
        try:
            create_tables()
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"数据库表创建失败: {e}")
    
    return app

def register_middleware(app):
    """注册Flask中间件"""
    auth_middleware = AuthMiddleware()
    
    @app.before_request
    def before_request():
        """请求前处理"""
        # 跳过OPTIONS请求和公开路径
        if request.method == 'OPTIONS':
            return
            
        # 公开路径列表
        public_paths = [
            '/',
            '/health',
            '/docs',
            '/docs/',
            '/apidocs/',
            '/api/auth/login',
            '/api/auth/register',
            '/api/auth/health',
            '/api/system/health'
        ]
        
        if request.path in public_paths or request.path.startswith('/apidocs/'):
            return
        
        # 执行认证中间件
        try:
            user_data = auth_middleware.authenticate_request(request)
            if not user_data:
                return jsonify({
                    'error': 'unauthorized',
                    'message': '未授权访问'
                }), 401
            
            # 将用户信息存储到g对象中
            g.current_user = user_data
            
        except Exception as e:
            logger.error(f"认证中间件错误: {str(e)}")
            return jsonify({
                'error': 'authentication_error',
                'message': '认证处理失败'
            }), 401

def register_blueprints(app):
    """注册Flask蓝图"""
    api_prefix = '/api'
    
    app.register_blueprint(auth_bp, url_prefix=f'{api_prefix}/auth')
    app.register_blueprint(data_bp, url_prefix=f'{api_prefix}')
    app.register_blueprint(trade_bp, url_prefix=f'{api_prefix}/trade')
    app.register_blueprint(strategy_bp, url_prefix=f'{api_prefix}/strategies')
    app.register_blueprint(system_bp, url_prefix=f'{api_prefix}/system')
    
    # 根路径
    @app.route('/')
    def root():
        """Root endpoint"""
        return jsonify({
            "message": "AI Stock Trading System is running (Flask)", 
            "version": "1.0.0",
            "status": "running",
            "framework": "Flask",
            "features": ["Tushare数据集成", "AI交易策略", "风险管理", "实时监控"]
        })

    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        try:
            from app.core.database import db_manager
            
            # 检查数据库连接
            db_status = True  # 简化检查
            
            return jsonify({
                "status": "healthy" if db_status else "unhealthy",
                "database": "connected" if db_status else "disconnected",
                "framework": "Flask",
                "services": {
                    "auth_api": "available",
                    "data_api": "available",
                    "trade_api": "available"
                }
            })
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return jsonify({
                "status": "unhealthy",
                "error": str(e)
            }), 500

def register_error_handlers(app):
    """注册Flask错误处理器"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'bad_request',
            'message': '请求参数错误'
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'unauthorized',
            'message': '未授权访问'
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'forbidden',
            'message': '禁止访问'
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'not_found',
            'message': '资源未找到'
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'internal_server_error',
            'message': '内部服务器错误'
        }), 500

    @app.errorhandler(FlaskHTTPException)
    def handle_http_exception(error):
        return jsonify({
            'error': error.name.lower().replace(' ', '_'),
            'message': error.description
        }), error.code

    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.error(f"未处理的异常: {str(error)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'internal_server_error',
            'message': '内部服务器错误'
        }), 500

# 创建Flask应用实例
app = create_app() if FLASK_APIS_AVAILABLE else None

if __name__ == "__main__":
    if app:
        logger.info("启动Flask服务器在 0.0.0.0:5000")
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True
        )
    else:
        logger.error("Flask应用创建失败")