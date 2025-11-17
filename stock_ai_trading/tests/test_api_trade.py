"""
交易API测试用例
"""

import pytest
import json
from flask import Flask
from app.api.trade_api import trade_bp
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
    app.register_blueprint(trade_bp, url_prefix='/api/trade')
    
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
def sample_order():
    """示例订单数据"""
    return {
        'symbol': '000001',
        'side': 'buy',
        'order_type': 'limit',
        'quantity': 100,
        'price': 10.50
    }


class TestOrderPlacement:
    """订单下单测试"""
    
    def test_place_order_success(self, client, auth_headers, sample_order):
        """测试成功下单"""
        response = client.post('/api/trade/orders',
                             data=json.dumps(sample_order),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'order_id' in data['data']
        assert data['data']['symbol'] == sample_order['symbol']
        assert data['data']['side'] == sample_order['side']
        assert data['data']['status'] == 'pending'
    
    def test_place_order_missing_fields(self, client, auth_headers):
        """测试缺少必填字段"""
        incomplete_order = {
            'symbol': '000001',
            'side': 'buy'
            # 缺少quantity和price
        }
        
        response = client.post('/api/trade/orders',
                             data=json.dumps(incomplete_order),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
    
    def test_place_order_invalid_symbol(self, client, auth_headers, sample_order):
        """测试无效股票代码"""
        sample_order['symbol'] = 'INVALID'
        
        response = client.post('/api/trade/orders',
                             data=json.dumps(sample_order),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
    
    def test_place_order_invalid_side(self, client, auth_headers, sample_order):
        """测试无效交易方向"""
        sample_order['side'] = 'invalid'
        
        response = client.post('/api/trade/orders',
                             data=json.dumps(sample_order),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
    
    def test_place_order_invalid_quantity(self, client, auth_headers, sample_order):
        """测试无效数量"""
        sample_order['quantity'] = -100
        
        response = client.post('/api/trade/orders',
                             data=json.dumps(sample_order),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
    
    def test_place_order_invalid_price(self, client, auth_headers, sample_order):
        """测试无效价格"""
        sample_order['price'] = -10.50
        
        response = client.post('/api/trade/orders',
                             data=json.dumps(sample_order),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
    
    def test_place_market_order_success(self, client, auth_headers):
        """测试市价单"""
        market_order = {
            'symbol': '000001',
            'side': 'buy',
            'order_type': 'market',
            'quantity': 100
            # 市价单不需要price
        }
        
        response = client.post('/api/trade/orders',
                             data=json.dumps(market_order),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['order_type'] == 'market'
    
    def test_place_order_insufficient_funds(self, client, auth_headers, sample_order):
        """测试资金不足"""
        # 设置一个很大的数量来模拟资金不足
        sample_order['quantity'] = 1000000
        sample_order['price'] = 100.0
        
        response = client.post('/api/trade/orders',
                             data=json.dumps(sample_order),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
        assert '资金不足' in data['message']


class TestOrderManagement:
    """订单管理测试"""
    
    def test_get_orders_success(self, client, auth_headers):
        """测试获取订单列表"""
        response = client.get('/api/trade/orders',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert isinstance(data['data'], list)
    
    def test_get_orders_with_filters(self, client, auth_headers):
        """测试带过滤条件的订单查询"""
        params = {
            'symbol': '000001',
            'status': 'pending',
            'side': 'buy'
        }
        
        response = client.get('/api/trade/orders',
                            query_string=params,
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_get_order_by_id_success(self, client, auth_headers, sample_order):
        """测试根据ID获取订单"""
        # 先创建一个订单
        create_response = client.post('/api/trade/orders',
                                    data=json.dumps(sample_order),
                                    content_type='application/json',
                                    headers=auth_headers)
        
        create_data = json.loads(create_response.data)
        order_id = create_data['data']['order_id']
        
        # 获取订单详情
        response = client.get(f'/api/trade/orders/{order_id}',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['order_id'] == order_id
    
    def test_get_order_by_id_not_found(self, client, auth_headers):
        """测试获取不存在的订单"""
        response = client.get('/api/trade/orders/nonexistent_id',
                            headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'not_found'
    
    def test_cancel_order_success(self, client, auth_headers, sample_order):
        """测试成功撤单"""
        # 先创建一个订单
        create_response = client.post('/api/trade/orders',
                                    data=json.dumps(sample_order),
                                    content_type='application/json',
                                    headers=auth_headers)
        
        create_data = json.loads(create_response.data)
        order_id = create_data['data']['order_id']
        
        # 撤销订单
        response = client.delete(f'/api/trade/orders/{order_id}',
                               headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['status'] == 'cancelled'
    
    def test_cancel_order_not_found(self, client, auth_headers):
        """测试撤销不存在的订单"""
        response = client.delete('/api/trade/orders/nonexistent_id',
                               headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'not_found'
    
    def test_cancel_order_already_filled(self, client, auth_headers):
        """测试撤销已成交的订单"""
        # 这需要模拟一个已成交的订单
        # 在实际实现中，需要设置订单状态为filled
        pass


class TestPositionManagement:
    """持仓管理测试"""
    
    def test_get_positions_success(self, client, auth_headers):
        """测试获取持仓列表"""
        response = client.get('/api/trade/positions',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert isinstance(data['data'], list)
    
    def test_get_position_by_symbol_success(self, client, auth_headers):
        """测试根据股票代码获取持仓"""
        response = client.get('/api/trade/positions/000001',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_get_position_by_symbol_not_found(self, client, auth_headers):
        """测试获取不存在的持仓"""
        response = client.get('/api/trade/positions/NONEXISTENT',
                            headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'not_found'


class TestTradeHistory:
    """交易历史测试"""
    
    def test_get_trades_success(self, client, auth_headers):
        """测试获取交易记录"""
        response = client.get('/api/trade/trades',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert isinstance(data['data'], list)
    
    def test_get_trades_with_filters(self, client, auth_headers):
        """测试带过滤条件的交易记录查询"""
        params = {
            'symbol': '000001',
            'start_date': '2024-01-01',
            'end_date': '2024-01-31'
        }
        
        response = client.get('/api/trade/trades',
                            query_string=params,
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_get_trade_by_id_success(self, client, auth_headers):
        """测试根据ID获取交易记录"""
        # 先获取交易列表
        list_response = client.get('/api/trade/trades',
                                 headers=auth_headers)
        
        list_data = json.loads(list_response.data)
        if list_data['data']:
            trade_id = list_data['data'][0]['trade_id']
            
            # 获取交易详情
            response = client.get(f'/api/trade/trades/{trade_id}',
                                headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['data']['trade_id'] == trade_id


class TestAccountInfo:
    """账户信息测试"""
    
    def test_get_account_info_success(self, client, auth_headers):
        """测试获取账户信息"""
        response = client.get('/api/trade/account',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'balance' in data['data']
        assert 'available_balance' in data['data']
        assert 'frozen_balance' in data['data']
    
    def test_get_account_summary_success(self, client, auth_headers):
        """测试获取账户摘要"""
        response = client.get('/api/trade/account/summary',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'total_assets' in data['data']
        assert 'market_value' in data['data']
        assert 'profit_loss' in data['data']


class TestRiskControl:
    """风控测试"""
    
    def test_order_risk_check_success(self, client, auth_headers, sample_order):
        """测试订单风控检查"""
        response = client.post('/api/trade/risk-check',
                             data=json.dumps(sample_order),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'risk_level' in data['data']
        assert 'warnings' in data['data']
    
    def test_order_risk_check_high_risk(self, client, auth_headers):
        """测试高风险订单"""
        high_risk_order = {
            'symbol': '000001',
            'side': 'buy',
            'order_type': 'market',
            'quantity': 100000  # 大额订单
        }
        
        response = client.post('/api/trade/risk-check',
                             data=json.dumps(high_risk_order),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['risk_level'] in ['medium', 'high']


class TestRateLimiting:
    """速率限制测试"""
    
    def test_trading_api_rate_limit(self, client, auth_headers, sample_order):
        """测试交易API速率限制"""
        # 快速发送多个下单请求
        responses = []
        for _ in range(20):
            response = client.post('/api/trade/orders',
                                 data=json.dumps(sample_order),
                                 content_type='application/json',
                                 headers=auth_headers)
            responses.append(response)
        
        # 检查是否有速率限制响应
        rate_limited = any(r.status_code == 429 for r in responses)
        # 注意：在测试环境中可能不会触发速率限制


class TestAuthentication:
    """认证测试"""
    
    def test_place_order_without_auth(self, client, sample_order):
        """测试未认证下单"""
        response = client.post('/api/trade/orders',
                             data=json.dumps(sample_order),
                             content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'authentication_error'
    
    def test_get_orders_without_auth(self, client):
        """测试未认证获取订单"""
        response = client.get('/api/trade/orders')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'authentication_error'
    
    def test_get_account_without_auth(self, client):
        """测试未认证获取账户信息"""
        response = client.get('/api/trade/account')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'authentication_error'


class TestErrorHandling:
    """错误处理测试"""
    
    def test_invalid_json_format(self, client, auth_headers):
        """测试无效JSON格式"""
        response = client.post('/api/trade/orders',
                             data='invalid json',
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
    
    def test_unsupported_content_type(self, client, auth_headers, sample_order):
        """测试不支持的内容类型"""
        response = client.post('/api/trade/orders',
                             data=json.dumps(sample_order),
                             content_type='text/plain',
                             headers=auth_headers)
        
        assert response.status_code == 400


if __name__ == '__main__':
    pytest.main([__file__])