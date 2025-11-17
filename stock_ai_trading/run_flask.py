#!/usr/bin/env python3
"""
Flask API服务器启动脚本

独立运行Flask版本的API服务器
"""

import os
import sys
from pathlib import Path
try:
    # 优先加载 .env 以确保环境变量（DATABASE_URL 等）在导入蓝图前生效
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=str(env_path), override=True)
        print(f"[INFO] 已加载环境变量文件: {env_path}")
    else:
        print("[INFO] 未找到 .env 文件，使用系统环境变量")
except Exception as e:
    print(f"[WARN] 加载 .env 失败，将使用系统环境变量: {e}")
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
import logging
import traceback
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.auth_api import auth_bp
from app.api.data_api import data_bp
from app.api.trade_api import trade_bp
from app.api.strategy_api import strategy_bp, strategies_alias_bp
from app.api.system_api import system_bp
from app.api.risk_control_api import risk_bp
from app.api.ai_decision_flask import ai_decision_bp
from app.api.portfolio_flask import portfolio_bp
from app.api.data_management_api import data_mgmt_bp
from app.api.screening_api import screening_bp
from app.api.data_sync_api import data_sync_bp  # 数据同步API
# 尝试加载模型管理相关蓝图，失败时回退到占位接口以保证核心服务可启动
try:
    from app.api.model_management_flask import model_mgmt_bp
    _enable_model_mgmt = True
except Exception as e:
    print(f"[WARN] 模型管理模块加载失败，改用占位接口: {e}")
    try:
        from app.api.model_management_stub import model_mgmt_bp as model_mgmt_bp
        _enable_model_mgmt = True
        print("[INFO] 已加载模型管理占位接口，提供基本端点")
    except Exception as e2:
        print(f"[WARN] 占位接口加载失败，跳过注册: {e2}")
        model_mgmt_bp = None
        _enable_model_mgmt = False

try:
    from app.api.model_test_api import model_test_bp
    _enable_model_test = True
except Exception as e:
    print(f"[WARN] 模型测试模块加载失败，跳过注册: {e}")
    model_test_bp = None
    _enable_model_test = False
from app.middleware.auth import AuthMiddleware
from app.utils.jwt_utils import jwt_manager
from app.config.config import get_config


def create_app(config_name='development'):
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 加载配置
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    
    # 配置CORS - 修复跨域问题
    CORS(app, 
         origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://192.168.205.248:3000"],
         methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "X-API-Key", "Accept", "Origin", "X-Requested-With"],
         supports_credentials=True,
         expose_headers=["Content-Type", "Authorization"],
         max_age=86400)  # 预检请求缓存24小时
    
    # 配置日志
    setup_logging(app)
    
    # JWT管理器已经在utils中初始化，无需再次初始化
    
    # 注册中间件
    register_middleware(app)
    
    # 注册蓝图
    register_blueprints(app)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 注册请求钩子
    register_request_hooks(app)
    
    # 初始化LLM网关
    try:
        from app.services.llm_gateway import initialize_gateway
        initialize_gateway()
        app.logger.info("LLM网关初始化成功")
    except Exception as e:
        app.logger.warning(f"LLM网关初始化失败: {e}")
    
    return app


def setup_logging(app):
    """配置日志"""
    if not app.debug:
        # 创建日志目录
        log_dir = os.path.join(os.path.dirname(app.root_path), 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 配置文件日志
        file_handler = logging.FileHandler(
            os.path.join(log_dir, 'flask_api.log'),
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Flask API服务启动')


def register_middleware(app):
    """注册中间件"""
    # 认证中间件
    auth_middleware = AuthMiddleware()
    
    @app.before_request
    def before_request():
        """请求前处理"""
        # 记录请求开始时间
        g.start_time = datetime.now()
        
        # 记录请求信息
        app.logger.info(f"请求: {request.method} {request.path} - IP: {request.remote_addr}")
        
        # ==========================================
        # 临时关闭所有权限验证（用于调试）
        # ==========================================
        app.logger.warning("⚠️  权限验证已临时关闭！")
        return  # 直接返回，跳过所有认证逻辑
        
        # 以下代码被临时禁用
        # ==========================================
        
        # # 跳过OPTIONS请求的认证
        # if request.method == 'OPTIONS':
        #     return
        
        # # 跳过健康检查和公开端点的认证
        # public_endpoints = [
        #     '/api/auth/login',
        #     '/api/auth/register',
        #     '/api/auth/logout',  # logout也应该是公开的，因为可能token已过期
        #     '/api/system/health',
        #     '/api/system/status',
        #     '/api/risk/health',  # 风控健康检查
        #     '/api/trade/health',  # 交易健康检查
        #     '/api/strategy/health',  # 策略健康检查
        #     '/api/strategy/test',  # 测试接口
        #     '/api/strategy/list',  # 策略列表接口
        #     '/api/strategy/ai-generate',  # AI策略生成接口
        #     '/api/strategies/ai-generate',  # 兼容旧路径：AI策略生成
        #     '/api/strategy/batch-delete',  # 批量删除接口
        #     '/api/strategy',  # 策略CRUD接口（包括创建）
        #     '/api/ai-decision/health',  # AI决策健康检查
        #     '/api/screening/strategies',  # 选股策略列表
        #     '/api/screening/indicators',  # 选股指标列表
        #     '/api/screening/execute',  # 执行选股
        #     '/api/screening/data/sync-three-years',  # 同步三年历史数据
        #     '/api/screening/data/sync-daily-history',  # 同步每日历史行情
        #     '/api/screening/data/sync-stock-basic',  # 同步股票基础信息
        #     '/api/screening/data/sync-quotes',  # 同步行情数据
        #     '/api/screening/data/sync-financial',  # 同步财务数据
        #     '/api/screening/data/calculate-technical',  # 计算技术指标
        #     '/api/screening/strategies/custom',  # 创建自定义策略
        #     '/api/screening/history',  # 选股历史
        #     '/api/screening/preferences',  # 用户偏好
        #     '/docs',
        #     '/swagger',
        #     '/'
        # ]
        
        # # 检查是否为数据同步API（临时设为公开，用于调试）
        # if request.path.startswith('/api/data-sync/'):
        #     return
        
        # # 检查是否为策略删除接口（单个删除）
        # if request.path.startswith('/api/strategy/') and request.method == 'DELETE':
        #     return
        
        # # 检查是否为选股API的动态路由
        # if request.path.startswith('/api/screening/'):
        #     # 允许所有选股相关的路由
        #     if (request.path.startswith('/api/screening/results/') or 
        #         request.path.startswith('/api/screening/strategies/') and request.method in ['PUT', 'DELETE']):
        #         return
        
        # if request.path in public_endpoints or request.path.startswith('/static'):
        #     return
        
        # # 执行认证中间件
        # try:
        #     is_authenticated, user_data, error_msg = auth_middleware.authenticate_request()
        #     if not is_authenticated:
        #         return jsonify({
        #             'error': 'authentication_error',
        #             'message': error_msg or '认证失败'
        #         }), 401
            
        #     # 将用户信息存储到g对象中
        #     g.current_user = user_data
            
        # except Exception as e:
        #     app.logger.error(f"认证中间件错误: {str(e)}")
        #     return jsonify({
        #         'error': 'authentication_error',
        #         'message': '认证处理失败'
        #     }), 401


def register_blueprints(app):
    """注册蓝图"""
    # API版本前缀
    api_prefix = '/api'
    
    # 注册各个API蓝图
    app.register_blueprint(auth_bp, url_prefix=f'{api_prefix}/auth')
    app.register_blueprint(data_bp)  # data_bp已经有自己的url_prefix='/api/data'
    app.register_blueprint(trade_bp, url_prefix=f'{api_prefix}/trade')
    app.register_blueprint(strategy_bp, url_prefix=f'{api_prefix}/strategy')
    # 兼容旧路径（前端有些模块使用 /api/strategies/*）
    app.register_blueprint(strategies_alias_bp, url_prefix=f'{api_prefix}/strategies')
    app.register_blueprint(system_bp, url_prefix=f'{api_prefix}/system')
    app.register_blueprint(risk_bp, url_prefix=f'{api_prefix}/risk')
    app.register_blueprint(ai_decision_bp, url_prefix=f'{api_prefix}/ai-decision')
    app.register_blueprint(portfolio_bp)
    app.register_blueprint(data_mgmt_bp)  # data_mgmt_bp已经有自己的url_prefix='/api/data-management'
    app.register_blueprint(screening_bp, url_prefix=f'{api_prefix}/screening')  # 选股API
    app.register_blueprint(data_sync_bp, url_prefix=f'{api_prefix}/data-sync')  # 数据同步API
    if model_mgmt_bp is not None:
        app.register_blueprint(model_mgmt_bp)
    if model_test_bp is not None:
        app.register_blueprint(model_test_bp)
    
    # 根路径
    @app.route('/')
    def index():
        """API根路径"""
        return jsonify({
            'name': 'Stock AI Trading API (Flask)',
            'version': '1.0.0',
            'description': 'AI驱动的股票交易系统API - Flask版本',
            'status': 'running',
            'timestamp': datetime.now().isoformat(),
            'framework': 'Flask',
            'endpoints': {
                'auth': f'{api_prefix}/auth',
                'data': f'{api_prefix}/stocks',
                'trade': f'{api_prefix}/trade',
                'strategy': f'{api_prefix}/strategies',
                'system': f'{api_prefix}/system',
                'docs': '/docs'
            }
        })
    
    # API文档路径
    @app.route('/docs')
    def docs():
        """API文档"""
        return jsonify({
            'message': 'Stock AI Trading API 文档',
            'version': '1.0.0',
            'framework': 'Flask',
            'endpoints': {
                '认证API': {
                    'POST /api/auth/login': '用户登录',
                    'POST /api/auth/register': '用户注册',
                    'GET /api/auth/profile': '获取用户信息',
                    'PUT /api/auth/profile': '更新用户信息',
                    'POST /api/auth/refresh': '刷新令牌',
                    'POST /api/auth/logout': '用户登出'
                },
                '数据API': {
                    'GET /api/stocks/list': '获取股票列表',
                    'GET /api/stocks/{code}/quotes': '获取股票行情',
                    'GET /api/stocks/{code}/realtime': '获取实时行情',
                    'GET /api/stocks/{code}/financials': '获取财务数据',
                    'GET /api/market/indicators': '获取市场指标',
                    'GET /api/market/overview': '获取市场概览'
                },
                '交易API': {
                    'POST /api/trade/order': '创建订单',
                    'DELETE /api/trade/order/{order_id}': '撤销订单',
                    'GET /api/trade/orders': '获取订单列表',
                    'GET /api/trade/positions': '获取持仓列表',
                    'GET /api/trade/account': '获取账户信息',
                    'GET /api/trade/trades': '获取成交记录'
                },
                '策略API': {
                    'POST /api/strategies/backtest': '运行策略回测',
                    'GET /api/strategies/signals': '获取交易信号',
                    'POST /api/strategies/select': '选择交易策略',
                    'GET /api/strategies/active': '获取活跃策略',
                    'GET /api/strategies/performance': '获取策略表现'
                },
                '系统API': {
                    'GET /api/system/status': '获取系统状态',
                    'GET /api/system/health': '健康检查',
                    'POST /api/system/control': '系统控制',
                    'GET /api/system/metrics': '获取性能指标',
                    'GET /api/system/logs': '获取系统日志'
                }
            }
        })


def register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(400)
    def bad_request(error):
        """400错误处理"""
        return jsonify({
            'error': 'bad_request',
            'message': '请求参数错误',
            'details': str(error.description) if hasattr(error, 'description') else None
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """401错误处理"""
        return jsonify({
            'error': 'unauthorized',
            'message': '未授权访问',
            'details': str(error.description) if hasattr(error, 'description') else None
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """403错误处理"""
        return jsonify({
            'error': 'forbidden',
            'message': '访问被禁止',
            'details': str(error.description) if hasattr(error, 'description') else None
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """404错误处理"""
        return jsonify({
            'error': 'not_found',
            'message': '资源未找到',
            'path': request.path
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """405错误处理"""
        return jsonify({
            'error': 'method_not_allowed',
            'message': '请求方法不被允许',
            'method': request.method,
            'path': request.path
        }), 405
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """429错误处理"""
        return jsonify({
            'error': 'rate_limit_exceeded',
            'message': '请求频率超限',
            'details': str(error.description) if hasattr(error, 'description') else None
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        """500错误处理"""
        app.logger.error(f"内部服务器错误: {str(error)}")
        app.logger.error(traceback.format_exc())
        
        return jsonify({
            'error': 'internal_server_error',
            'message': '内部服务器错误',
            'request_id': getattr(g, 'request_id', None)
        }), 500
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """HTTP异常处理"""
        return jsonify({
            'error': error.name.lower().replace(' ', '_'),
            'message': error.description,
            'code': error.code
        }), error.code
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """通用异常处理"""
        app.logger.error(f"未处理的异常: {str(error)}")
        app.logger.error(traceback.format_exc())
        
        return jsonify({
            'error': 'unexpected_error',
            'message': '发生意外错误',
            'type': type(error).__name__
        }), 500


def register_request_hooks(app):
    """注册请求钩子"""
    
    @app.before_request
    def before_request():
        """请求前处理"""
        # 记录请求开始时间
        g.start_time = datetime.now()
        
        # 跳过静态文件和健康检查的日志
        if request.endpoint and not request.endpoint.startswith('static'):
            app.logger.info(f"请求: {request.method} {request.path} - IP: {request.remote_addr}")
    
    @app.before_request
    def handle_options():
        """处理OPTIONS预检请求"""
        if request.method == 'OPTIONS':
            response = app.make_default_options_response()
            headers = response.headers
            origin = request.headers.get('Origin')
            if origin:
                headers['Access-Control-Allow-Origin'] = origin
            else:
                headers['Access-Control-Allow-Origin'] = '*'
            headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS'
            headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-API-Key, Accept, Origin, X-Requested-With'
            headers['Access-Control-Allow-Credentials'] = 'true'
            headers['Access-Control-Max-Age'] = '86400'
            return response
    
    @app.after_request
    def after_request(response):
        """请求后处理"""
        # 添加CORS头
        origin = request.headers.get('Origin')
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        # 计算请求处理时间
        if hasattr(g, 'start_time'):
            duration = (datetime.now() - g.start_time).total_seconds()
            response.headers['X-Response-Time'] = f"{duration:.3f}s"
        
        # 添加安全头
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # 记录响应信息
        app.logger.info(
            f"响应: {request.method} {request.path} - "
            f"状态: {response.status_code} - "
            f"时间: {response.headers.get('X-Response-Time', 'N/A')}"
        )
        
        return response
    
    @app.teardown_appcontext
    def teardown_db(error):
        """清理应用上下文"""
        if error:
            app.logger.error(f"应用上下文错误: {str(error)}")


# 创建应用实例
app = create_app()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Stock AI Trading Flask API Server')
    parser.add_argument('--port', type=int, default=5000,
                       help='服务器端口 (默认: 5000)')
    parser.add_argument('--host', default='0.0.0.0',
                       help='服务器主机 (默认: 0.0.0.0)')
    parser.add_argument('--debug', action='store_true',
                       help='启用调试模式')
    parser.add_argument('--config', default='development',
                       choices=['development', 'testing', 'production'],
                       help='配置环境 (默认: development)')
    
    args = parser.parse_args()
    
    # 重新创建应用以使用指定配置
    app = create_app(args.config)
    
    print(f"启动Flask API服务器")
    print(f"地址: http://{args.host}:{args.port}")
    print(f"配置: {args.config}")
    print(f"调试模式: {args.debug}")
    print(f"API文档: http://{args.host}:{args.port}/docs")
    
    # 启动服务器
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug,
        threaded=True
    )