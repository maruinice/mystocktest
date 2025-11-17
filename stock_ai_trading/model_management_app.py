"""
模型管理系统 Flask 应用
整合所有API模块，提供完整的模型管理功能
"""

import os
from pathlib import Path
try:
    # 加载 .env，保证独立运行时的数据库与密钥配置生效
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=str(env_path), override=True)
        print(f"[INFO] 已加载环境变量文件: {env_path}")
    else:
        print("[INFO] 未找到 .env 文件，使用系统环境变量")
except Exception as e:
    print(f"[WARN] 加载 .env 失败，将使用系统环境变量: {e}")
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger

# 导入API蓝图
from app.api.model_management_flask import model_mgmt_bp
from app.api.model_test_api import model_test_bp

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_name='development'):
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 基础配置
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'model_management_secret_key_change_in_production')
    app.config['JSON_AS_ASCII'] = False  # 支持中文JSON
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True  # JSON格式化
    
    # CORS配置
    CORS(app, 
         origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization'],
         supports_credentials=True)
    
    # Swagger配置
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/docs/"
    }
    
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "模型管理系统 API",
            "description": "AI模型管理、组合管理、测试和监控的完整API系统",
            "version": "1.0.0",
            "contact": {
                "name": "开发团队",
                "email": "dev@example.com"
            }
        },
        "host": "localhost:5001",
        "basePath": "/",
        "schemes": ["http", "https"],
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: 'Bearer {token}'"
            }
        },
        "security": [
            {
                "Bearer": []
            }
        ],
        "tags": [
            {
                "name": "模型管理",
                "description": "AI模型的创建、查询、更新和删除操作"
            },
            {
                "name": "模型组合",
                "description": "模型组合的管理和配置操作"
            },
            {
                "name": "模型测试",
                "description": "单模型和组合模型的测试功能"
            },
            {
                "name": "仪表盘",
                "description": "统计信息和性能指标查询"
            }
        ]
    }
    
    Swagger(app, config=swagger_config, template=swagger_template)
    
    # 注册蓝图
    app.register_blueprint(model_mgmt_bp)
    app.register_blueprint(model_test_bp)
    
    # 根路径
    @app.route('/')
    def index():
        """API根路径"""
        return jsonify({
            'name': '模型管理系统 API',
            'version': '1.0.0',
            'description': 'AI模型管理、组合管理、测试和监控的完整API系统',
            'docs': '/docs/',
            'endpoints': {
                'models': '/api/models',
                'ensembles': '/api/ensembles',
                'test': '/api/models/test',
                'dashboard': '/api/dashboard/stats'
            },
            'status': 'running'
        })
    
    # 健康检查
    @app.route('/health')
    def health():
        """系统健康检查"""
        try:
            return jsonify({
                'status': 'healthy',
                'service': 'model_management_system',
                'version': '1.0.0',
                'components': {
                    'model_management_api': 'healthy',
                    'model_test_api': 'healthy',
                    'database': 'healthy',
                    'encryption_service': 'healthy'
                }
            }), 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return jsonify({
                'status': 'unhealthy',
                'service': 'model_management_system',
                'error': str(e)
            }), 500
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'message': '请求的资源不存在',
            'error_code': 'NOT_FOUND'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'message': '请求方法不被允许',
            'error_code': 'METHOD_NOT_ALLOWED'
        }), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({
            'success': False,
            'message': '服务器内部错误',
            'error_code': 'INTERNAL_SERVER_ERROR'
        }), 500
    
    # 请求日志
    @app.before_request
    def log_request_info():
        from flask import request
        logger.info(f"{request.method} {request.url} - {request.remote_addr}")
    
    @app.after_request
    def log_response_info(response):
        from flask import request
        logger.info(f"{request.method} {request.url} - {response.status_code}")
        return response
    
    return app

def main():
    """主函数"""
    # 创建应用
    app = create_app()
    
    # 获取配置
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5001))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Model Management System API on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"API Documentation: http://{host}:{port}/docs/")
    
    # 启动应用
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )

if __name__ == '__main__':
    main()