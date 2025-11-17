"""
Flask应用配置

包含JWT、数据库、缓存等配置
"""

import os
from datetime import timedelta


class Config:
    """基础配置"""
    
    # 应用配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_ALGORITHM = 'HS256'
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    
    # 数据库配置
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///stock_trading.db'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Redis配置（用于缓存和会话）
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300
    
    # 会话配置
    SESSION_TYPE = 'redis'
    SESSION_REDIS = REDIS_URL
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'stock_trading:'
    
    # API配置
    API_TITLE = 'Stock AI Trading API'
    API_VERSION = '1.0.0'
    API_DESCRIPTION = 'AI驱动的股票交易系统API'
    
    # 速率限制配置
    RATELIMIT_STORAGE_URL = REDIS_URL
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_HEADERS_ENABLED = True
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # 安全配置
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    
    # 邮件配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # 股票数据API配置
    TUSHARE_TOKEN = os.environ.get('TUSHARE_TOKEN')
    AKSHARE_ENABLED = os.environ.get('AKSHARE_ENABLED', 'true').lower() == 'true'
    
    # 交易配置
    TRADING_ENABLED = os.environ.get('TRADING_ENABLED', 'false').lower() == 'true'
    TRADING_MODE = os.environ.get('TRADING_MODE', 'simulation')  # simulation, live
    
    # AI模型配置
    AI_MODEL_PATH = os.environ.get('AI_MODEL_PATH', 'models')
    AI_MODEL_UPDATE_INTERVAL = int(os.environ.get('AI_MODEL_UPDATE_INTERVAL', 3600))  # 秒
    
    # 监控配置
    MONITORING_ENABLED = os.environ.get('MONITORING_ENABLED', 'true').lower() == 'true'
    METRICS_PORT = int(os.environ.get('METRICS_PORT', 9090))
    
    # 备份配置
    BACKUP_ENABLED = os.environ.get('BACKUP_ENABLED', 'true').lower() == 'true'
    BACKUP_INTERVAL = int(os.environ.get('BACKUP_INTERVAL', 86400))  # 秒
    BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', 30))
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        pass


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False
    
    # 开发环境使用SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dev.db')
    
    # 开发环境日志级别
    LOG_LEVEL = 'DEBUG'
    
    # 开发环境禁用CSRF
    WTF_CSRF_ENABLED = False


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    
    # 测试环境使用内存数据库
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # 测试环境禁用CSRF
    WTF_CSRF_ENABLED = False
    
    # 测试环境使用简单缓存
    CACHE_TYPE = 'simple'
    
    # 测试环境JWT配置
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(hours=1)


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False
    
    # 生产环境必须设置的环境变量
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # 检查必要的环境变量
        required_vars = [
            'SECRET_KEY',
            'JWT_SECRET_KEY',
            'DATABASE_URL'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"生产环境缺少必要的环境变量: {', '.join(missing_vars)}")
        
        # 生产环境日志配置
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug:
            # 创建日志目录
            log_dir = os.path.dirname(cls.LOG_FILE)
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # 配置文件日志
            file_handler = RotatingFileHandler(
                cls.LOG_FILE,
                maxBytes=cls.LOG_MAX_BYTES,
                backupCount=cls.LOG_BACKUP_COUNT,
                encoding='utf-8'
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('Stock Trading API startup')


# 配置映射
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """获取配置类"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return config.get(config_name, DevelopmentConfig)