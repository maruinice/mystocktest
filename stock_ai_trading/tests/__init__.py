"""
测试包初始化文件
"""

# 测试包版本
__version__ = '1.0.0'

# 测试配置
TEST_CONFIG = {
    'TESTING': True,
    'WTF_CSRF_ENABLED': False,
    'SECRET_KEY': 'test-secret-key',
    'JWT_SECRET_KEY': 'test-jwt-secret',
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'REDIS_URL': 'redis://localhost:6379/1',
    'CACHE_TYPE': 'simple',
    'RATELIMIT_STORAGE_URL': 'memory://',
}

# 测试常量
TEST_USER = {
    'username': 'testuser',
    'email': 'test@example.com',
    'password': 'Test123!@#'
}

TEST_ADMIN = {
    'username': 'admin',
    'email': 'admin@example.com',
    'password': 'Admin123!@#'
}

TEST_STOCK = {
    'symbol': '000001',
    'name': '平安银行'
}

# 测试工具函数
def get_test_config():
    """获取测试配置"""
    return TEST_CONFIG.copy()


def get_test_user():
    """获取测试用户"""
    return TEST_USER.copy()


def get_test_admin():
    """获取测试管理员"""
    return TEST_ADMIN.copy()


def get_test_stock():
    """获取测试股票"""
    return TEST_STOCK.copy()