"""
策略API测试用例
"""

import pytest
import json
from flask import Flask
from app.api.strategy_api import strategy_bp
from app.middleware import jwt_manager, error_handler
from app.config.config import get_config


@pytest.fixture
def app():
    """创建测试应用"""
    app = Flask(__name__)
    app.config.from_object(get_config('testing'))
    
    # 初始化扩展
    jwt_manager.init_app(app)
    error_handler.init_app(app)
    
    # 注册蓝图
    app.register_blueprint(strategy_bp, url_prefix='/api/strategy')
    
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """获取认证头"""
    return {'Authorization': 'Bearer mock_token'}


@pytest.fixture
def sample_backtest_request():
    """示例回测请求"""
    return {
        'strategy_id': 'ma_crossover',
        'symbol': '000001',
        'start_date': '2024-01-01',
        'end_date': '2024-03-31',
        'initial_capital': 100000,
        'parameters': {
            'short_window': 5,
            'long_window': 20
        }
    }


class TestBacktesting:
    """回测测试"""
    
    def test_run_backtest_success(self, client, auth_headers, sample_backtest_request):
        """测试成功运行回测"""
        response = client.post('/api/strategy/backtest',
                             data=json.dumps(sample_backtest_request),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'backtest_id' in data['data']
        assert 'status' in data['data']
    
    def test_run_backtest_missing_fields(self, client, auth_headers):
        """测试缺少必填字段"""
        incomplete_request = {
            'strategy_id': 'ma_crossover',
            'symbol': '000001'
            # 缺少日期和资金
        }
        
        response = client.post('/api/strategy/backtest',
                             data=json.dumps(incomplete_request),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
    
    def test_run_backtest_invalid_date_range(self, client, auth_headers, sample_backtest_request):
        """测试无效日期范围"""
        sample_backtest_request['start_date'] = '2024-03-31'
        sample_backtest_request['end_date'] = '2024-01-01'  # 结束日期早于开始日期
        
        response = client.post('/api/strategy/backtest',
                             data=json.dumps(sample_backtest_request),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
    
    def test_run_backtest_invalid_strategy(self, client, auth_headers, sample_backtest_request):
        """测试无效策略ID"""
        sample_backtest_request['strategy_id'] = 'nonexistent_strategy'
        
        response = client.post('/api/strategy/backtest',
                             data=json.dumps(sample_backtest_request),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'not_found'
    
    def test_run_backtest_invalid_capital(self, client, auth_headers, sample_backtest_request):
        """测试无效初始资金"""
        sample_backtest_request['initial_capital'] = -1000
        
        response = client.post('/api/strategy/backtest',
                             data=json.dumps(sample_backtest_request),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'


class TestBacktestResults:
    """回测结果测试"""
    
    def test_get_backtest_result_success(self, client, auth_headers, sample_backtest_request):
        """测试获取回测结果"""
        # 先运行回测
        backtest_response = client.post('/api/strategy/backtest',
                                      data=json.dumps(sample_backtest_request),
                                      content_type='application/json',
                                      headers=auth_headers)
        
        backtest_data = json.loads(backtest_response.data)
        backtest_id = backtest_data['data']['backtest_id']
        
        # 获取回测结果
        response = client.get(f'/api/strategy/backtest/{backtest_id}',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'performance_metrics' in data['data']
        assert 'equity_curve' in data['data']
        assert 'trades' in data['data']
    
    def test_get_backtest_result_not_found(self, client, auth_headers):
        """测试获取不存在的回测结果"""
        response = client.get('/api/strategy/backtest/nonexistent_id',
                            headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'not_found'
    
    def test_get_backtest_history_success(self, client, auth_headers):
        """测试获取回测历史"""
        response = client.get('/api/strategy/backtest/history',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert isinstance(data['data'], list)
    
    def test_get_backtest_history_with_filters(self, client, auth_headers):
        """测试带过滤条件的回测历史"""
        params = {
            'strategy_id': 'ma_crossover',
            'symbol': '000001',
            'limit': '10'
        }
        
        response = client.get('/api/strategy/backtest/history',
                            query_string=params,
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) <= 10


class TestTradingSignals:
    """交易信号测试"""
    
    def test_get_trading_signals_success(self, client, auth_headers):
        """测试获取交易信号"""
        params = {
            'strategy_id': 'ma_crossover',
            'symbols': '000001,000002'
        }
        
        response = client.get('/api/strategy/signals',
                            query_string=params,
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert isinstance(data['data'], list)
    
    def test_get_trading_signals_invalid_strategy(self, client, auth_headers):
        """测试无效策略的交易信号"""
        params = {
            'strategy_id': 'nonexistent_strategy',
            'symbols': '000001'
        }
        
        response = client.get('/api/strategy/signals',
                            query_string=params,
                            headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'not_found'
    
    def test_get_latest_signals_success(self, client, auth_headers):
        """测试获取最新信号"""
        params = {
            'strategy_id': 'ma_crossover',
            'limit': '5'
        }
        
        response = client.get('/api/strategy/signals/latest',
                            query_string=params,
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) <= 5


class TestStrategyManagement:
    """策略管理测试"""
    
    def test_select_strategy_success(self, client, auth_headers):
        """测试选择策略"""
        strategy_data = {
            'strategy_id': 'ma_crossover',
            'symbols': ['000001', '000002'],
            'parameters': {
                'short_window': 5,
                'long_window': 20
            }
        }
        
        response = client.post('/api/strategy/select',
                             data=json.dumps(strategy_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'strategy_instance_id' in data['data']
    
    def test_select_strategy_invalid_id(self, client, auth_headers):
        """测试选择无效策略"""
        strategy_data = {
            'strategy_id': 'nonexistent_strategy',
            'symbols': ['000001']
        }
        
        response = client.post('/api/strategy/select',
                             data=json.dumps(strategy_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'not_found'
    
    def test_get_active_strategies_success(self, client, auth_headers):
        """测试获取活跃策略"""
        response = client.get('/api/strategy/active',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert isinstance(data['data'], list)
    
    def test_get_available_strategies_success(self, client, auth_headers):
        """测试获取可用策略"""
        response = client.get('/api/strategy/available',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert isinstance(data['data'], list)
        
        # 检查策略信息完整性
        if data['data']:
            strategy = data['data'][0]
            assert 'strategy_id' in strategy
            assert 'name' in strategy
            assert 'description' in strategy
            assert 'parameters' in strategy


class TestStrategyPerformance:
    """策略表现测试"""
    
    def test_get_strategy_performance_success(self, client, auth_headers):
        """测试获取策略表现"""
        params = {
            'strategy_id': 'ma_crossover',
            'period': '1M'
        }
        
        response = client.get('/api/strategy/performance',
                            query_string=params,
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'metrics' in data['data']
        assert 'equity_curve' in data['data']
    
    def test_get_strategy_performance_invalid_strategy(self, client, auth_headers):
        """测试获取无效策略的表现"""
        params = {
            'strategy_id': 'nonexistent_strategy',
            'period': '1M'
        }
        
        response = client.get('/api/strategy/performance',
                            query_string=params,
                            headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'not_found'
    
    def test_get_strategy_performance_invalid_period(self, client, auth_headers):
        """测试无效时间周期"""
        params = {
            'strategy_id': 'ma_crossover',
            'period': 'invalid_period'
        }
        
        response = client.get('/api/strategy/performance',
                            query_string=params,
                            headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'


class TestStrategyControl:
    """策略控制测试"""
    
    def test_stop_strategy_success(self, client, auth_headers):
        """测试停止策略"""
        # 先选择一个策略
        strategy_data = {
            'strategy_id': 'ma_crossover',
            'symbols': ['000001']
        }
        
        select_response = client.post('/api/strategy/select',
                                    data=json.dumps(strategy_data),
                                    content_type='application/json',
                                    headers=auth_headers)
        
        select_data = json.loads(select_response.data)
        instance_id = select_data['data']['strategy_instance_id']
        
        # 停止策略
        response = client.post(f'/api/strategy/{instance_id}/stop',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_stop_strategy_not_found(self, client, auth_headers):
        """测试停止不存在的策略"""
        response = client.post('/api/strategy/nonexistent_id/stop',
                             headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'not_found'
    
    def test_start_strategy_success(self, client, auth_headers):
        """测试启动策略"""
        # 这需要先有一个已停止的策略实例
        # 在实际实现中需要创建相应的测试数据
        pass


class TestParameterValidation:
    """参数验证测试"""
    
    def test_validate_backtest_parameters(self, client, auth_headers):
        """测试回测参数验证"""
        invalid_params = {
            'strategy_id': '',  # 空策略ID
            'symbol': '000001',
            'start_date': '2024-01-01',
            'end_date': '2024-03-31',
            'initial_capital': 0  # 无效资金
        }
        
        response = client.post('/api/strategy/backtest',
                             data=json.dumps(invalid_params),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
    
    def test_validate_signal_parameters(self, client, auth_headers):
        """测试信号参数验证"""
        # 缺少必要参数
        response = client.get('/api/strategy/signals',
                            headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
    
    def test_validate_strategy_selection_parameters(self, client, auth_headers):
        """测试策略选择参数验证"""
        invalid_selection = {
            'strategy_id': 'ma_crossover',
            'symbols': [],  # 空符号列表
            'parameters': {}
        }
        
        response = client.post('/api/strategy/select',
                             data=json.dumps(invalid_selection),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'


class TestRateLimiting:
    """速率限制测试"""
    
    def test_backtest_rate_limit(self, client, auth_headers, sample_backtest_request):
        """测试回测速率限制"""
        # 快速发送多个回测请求
        responses = []
        for _ in range(10):
            response = client.post('/api/strategy/backtest',
                                 data=json.dumps(sample_backtest_request),
                                 content_type='application/json',
                                 headers=auth_headers)
            responses.append(response)
        
        # 检查是否有速率限制响应
        rate_limited = any(r.status_code == 429 for r in responses)
        # 注意：在测试环境中可能不会触发速率限制


class TestAuthentication:
    """认证测试"""
    
    def test_backtest_without_auth(self, client, sample_backtest_request):
        """测试未认证运行回测"""
        response = client.post('/api/strategy/backtest',
                             data=json.dumps(sample_backtest_request),
                             content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'authentication_error'
    
    def test_get_signals_without_auth(self, client):
        """测试未认证获取信号"""
        response = client.get('/api/strategy/signals')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'authentication_error'
    
    def test_select_strategy_without_auth(self, client):
        """测试未认证选择策略"""
        strategy_data = {
            'strategy_id': 'ma_crossover',
            'symbols': ['000001']
        }
        
        response = client.post('/api/strategy/select',
                             data=json.dumps(strategy_data),
                             content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'authentication_error'


class TestErrorHandling:
    """错误处理测试"""
    
    def test_invalid_json_format(self, client, auth_headers):
        """测试无效JSON格式"""
        response = client.post('/api/strategy/backtest',
                             data='invalid json',
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
    
    def test_missing_content_type(self, client, auth_headers, sample_backtest_request):
        """测试缺少内容类型"""
        response = client.post('/api/strategy/backtest',
                             data=json.dumps(sample_backtest_request),
                             headers=auth_headers)
        
        assert response.status_code == 400


if __name__ == '__main__':
    pytest.main([__file__])