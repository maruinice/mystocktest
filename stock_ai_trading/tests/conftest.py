"""
pytest配置文件
提供通用的测试配置和fixture
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch
from flask import Flask

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.config.config import get_config


@pytest.fixture(scope='session')
def test_config():
    """测试配置"""
    return get_config('testing')


@pytest.fixture
def mock_database():
    """模拟数据库"""
    with patch('app.database.db') as mock_db:
        # 模拟数据库连接
        mock_db.session = Mock()
        mock_db.session.add = Mock()
        mock_db.session.commit = Mock()
        mock_db.session.rollback = Mock()
        mock_db.session.query = Mock()
        yield mock_db


@pytest.fixture
def mock_redis():
    """模拟Redis"""
    with patch('app.cache.redis_client') as mock_redis:
        mock_redis.get = Mock(return_value=None)
        mock_redis.set = Mock(return_value=True)
        mock_redis.delete = Mock(return_value=True)
        mock_redis.exists = Mock(return_value=False)
        yield mock_redis


@pytest.fixture
def mock_jwt():
    """模拟JWT"""
    with patch('app.middleware.auth.jwt_manager') as mock_jwt:
        mock_jwt.decode_token = Mock(return_value={'user_id': 1, 'username': 'testuser'})
        mock_jwt.create_access_token = Mock(return_value='mock_access_token')
        mock_jwt.create_refresh_token = Mock(return_value='mock_refresh_token')
        yield mock_jwt


@pytest.fixture
def mock_tushare():
    """模拟Tushare API"""
    with patch('tushare.pro_api') as mock_ts:
        # 模拟股票数据
        mock_ts.return_value.daily.return_value = Mock()
        mock_ts.return_value.stock_basic.return_value = Mock()
        mock_ts.return_value.trade_cal.return_value = Mock()
        yield mock_ts


@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'Test123!@#',
        'full_name': '测试用户'
    }


@pytest.fixture
def sample_stock_data():
    """示例股票数据"""
    return {
        'symbol': '000001',
        'name': '平安银行',
        'price': 12.50,
        'change': 0.15,
        'change_pct': 1.22,
        'volume': 1000000,
        'turnover': 12500000
    }


@pytest.fixture
def sample_order_data():
    """示例订单数据"""
    return {
        'symbol': '000001',
        'side': 'buy',
        'order_type': 'limit',
        'quantity': 1000,
        'price': 12.50
    }


@pytest.fixture
def sample_strategy_data():
    """示例策略数据"""
    return {
        'strategy_id': 'ma_crossover',
        'name': '移动平均线交叉策略',
        'description': '基于短期和长期移动平均线交叉的交易策略',
        'parameters': {
            'short_window': 5,
            'long_window': 20
        }
    }


@pytest.fixture
def authenticated_user():
    """认证用户信息"""
    return {
        'user_id': 1,
        'username': 'testuser',
        'email': 'test@example.com',
        'role': 'user'
    }


@pytest.fixture
def admin_user():
    """管理员用户信息"""
    return {
        'user_id': 2,
        'username': 'admin',
        'email': 'admin@example.com',
        'role': 'admin'
    }


@pytest.fixture
def mock_auth_middleware():
    """模拟认证中间件"""
    with patch('app.middleware.auth.AuthMiddleware') as mock_auth:
        mock_auth.verify_token = Mock(return_value=True)
        mock_auth.get_current_user = Mock(return_value={'user_id': 1, 'username': 'testuser'})
        yield mock_auth


@pytest.fixture
def mock_rate_limiter():
    """模拟速率限制器"""
    with patch('app.middleware.rate_limiter.RateLimiter') as mock_limiter:
        mock_limiter.is_allowed = Mock(return_value=True)
        mock_limiter.get_remaining = Mock(return_value=100)
        yield mock_limiter


@pytest.fixture
def mock_validation():
    """模拟验证中间件"""
    with patch('app.middleware.validation.ValidationMiddleware') as mock_validation:
        mock_validation.validate = Mock(return_value=True)
        yield mock_validation


@pytest.fixture
def mock_external_apis():
    """模拟外部API"""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post:
        
        # 模拟成功响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True, 'data': {}}
        
        mock_get.return_value = mock_response
        mock_post.return_value = mock_response
        
        yield mock_get, mock_post


@pytest.fixture
def mock_file_operations():
    """模拟文件操作"""
    with patch('builtins.open', create=True) as mock_open, \
         patch('os.path.exists') as mock_exists, \
         patch('os.makedirs') as mock_makedirs:
        
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = 'mock file content'
        
        yield mock_open, mock_exists, mock_makedirs


@pytest.fixture
def mock_email():
    """模拟邮件发送"""
    with patch('app.utils.email.send_email') as mock_send:
        mock_send.return_value = True
        yield mock_send


@pytest.fixture
def mock_scheduler():
    """模拟任务调度器"""
    with patch('app.scheduler.scheduler') as mock_scheduler:
        mock_scheduler.add_job = Mock()
        mock_scheduler.remove_job = Mock()
        mock_scheduler.get_jobs = Mock(return_value=[])
        yield mock_scheduler


class MockResponse:
    """模拟HTTP响应"""
    
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
        self.headers = {}
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


@pytest.fixture
def mock_http_response():
    """模拟HTTP响应工厂"""
    def _create_response(data=None, status_code=200):
        return MockResponse(data or {}, status_code)
    return _create_response


# 测试数据库配置
@pytest.fixture(scope='session')
def test_database_url():
    """测试数据库URL"""
    return 'sqlite:///:memory:'


# 清理函数
@pytest.fixture(autouse=True)
def cleanup():
    """自动清理fixture"""
    yield
    # 测试后清理工作
    pass


# 测试环境变量
@pytest.fixture(autouse=True)
def test_env_vars():
    """设置测试环境变量"""
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['SECRET_KEY'] = 'test-secret-key'
    os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret'
    yield
    # 清理环境变量
    for key in ['FLASK_ENV', 'SECRET_KEY', 'JWT_SECRET_KEY']:
        os.environ.pop(key, None)


# pytest配置
def pytest_configure(config):
    """pytest配置"""
    # 添加自定义标记
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )


# 测试收集钩子
def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    # 为没有标记的测试添加默认标记
    for item in items:
        if not any(item.iter_markers()):
            item.add_marker(pytest.mark.unit)


# 测试报告钩子
def pytest_runtest_makereport(item, call):
    """生成测试报告"""
    if "incremental" in item.keywords:
        if call.excinfo is not None:
            parent = item.parent
            parent._previousfailed = item


def pytest_runtest_setup(item):
    """测试设置"""
    if "incremental" in item.keywords:
        previousfailed = getattr(item.parent, "_previousfailed", None)
        if previousfailed is not None:
            pytest.xfail("previous test failed (%s)" % previousfailed.name)


# 参数化测试数据
@pytest.fixture(params=[
    {'symbol': '000001', 'name': '平安银行'},
    {'symbol': '000002', 'name': '万科A'},
    {'symbol': '600000', 'name': '浦发银行'},
])
def stock_symbols(request):
    """股票代码参数化"""
    return request.param


@pytest.fixture(params=['1d', '1w', '1M'])
def time_periods(request):
    """时间周期参数化"""
    return request.param


@pytest.fixture(params=['buy', 'sell'])
def order_sides(request):
    """订单方向参数化"""
    return request.param


@pytest.fixture(params=['limit', 'market'])
def order_types(request):
    """订单类型参数化"""
    return request.param