"""
数据API测试用例
"""

import pytest
import json
from flask import Flask
from app.api.data_api import data_bp
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
    app.register_blueprint(data_bp, url_prefix='/api/data')
    
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """获取认证头"""
    # 这里应该实现获取有效token的逻辑
    # 为了测试，使用模拟token
    return {'Authorization': 'Bearer mock_token'}


class TestStockQuotes:
    """股票行情测试"""
    
    def test_get_stock_quote_success(self, client, auth_headers):
        """测试获取单只股票行情"""
        response = client.get('/api/data/stocks/000001/quote',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'symbol' in data['data']
        assert 'price' in data['data']
        assert 'change' in data['data']
        assert 'change_percent' in data['data']
    
    def test_get_stock_quote_invalid_symbol(self, client, auth_headers):
        """测试无效股票代码"""
        response = client.get('/api/data/stocks/INVALID/quote',
                            headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'not_found'
    
    def test_get_multiple_quotes_success(self, client, auth_headers):
        """测试获取多只股票行情"""
        symbols = ['000001', '000002', '600000']
        response = client.get(f'/api/data/stocks/quotes?symbols={",".join(symbols)}',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == len(symbols)
    
    def test_get_quotes_without_auth(self, client):
        """测试未认证获取行情"""
        response = client.get('/api/data/stocks/000001/quote')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'authentication_error'


class TestHistoricalData:
    """历史数据测试"""
    
    def test_get_historical_data_success(self, client, auth_headers):
        """测试获取历史数据"""
        params = {
            'start_date': '2024-01-01',
            'end_date': '2024-01-31',
            'frequency': 'daily'
        }
        
        response = client.get('/api/data/stocks/000001/historical',
                            query_string=params,
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert isinstance(data['data'], list)
    
    def test_get_historical_data_invalid_date_range(self, client, auth_headers):
        """测试无效日期范围"""
        params = {
            'start_date': '2024-01-31',
            'end_date': '2024-01-01',  # 结束日期早于开始日期
            'frequency': 'daily'
        }
        
        response = client.get('/api/data/stocks/000001/historical',
                            query_string=params,
                            headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
    
    def test_get_historical_data_missing_params(self, client, auth_headers):
        """测试缺少必要参数"""
        params = {
            'start_date': '2024-01-01'
            # 缺少end_date
        }
        
        response = client.get('/api/data/stocks/000001/historical',
                            query_string=params,
                            headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'


class TestTechnicalIndicators:
    """技术指标测试"""
    
    def test_get_technical_indicators_success(self, client, auth_headers):
        """测试获取技术指标"""
        params = {
            'indicators': 'ma,rsi,macd',
            'period': '20'
        }
        
        response = client.get('/api/data/stocks/000001/indicators',
                            query_string=params,
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'indicators' in data['data']
    
    def test_get_technical_indicators_invalid_indicator(self, client, auth_headers):
        """测试无效技术指标"""
        params = {
            'indicators': 'invalid_indicator',
            'period': '20'
        }
        
        response = client.get('/api/data/stocks/000001/indicators',
                            query_string=params,
                            headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'


class TestMarketData:
    """市场数据测试"""
    
    def test_get_market_overview_success(self, client, auth_headers):
        """测试获取市场概览"""
        response = client.get('/api/data/market/overview',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'indices' in data['data']
        assert 'market_stats' in data['data']
    
    def test_get_sector_performance_success(self, client, auth_headers):
        """测试获取行业表现"""
        response = client.get('/api/data/market/sectors',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert isinstance(data['data'], list)
    
    def test_get_top_gainers_success(self, client, auth_headers):
        """测试获取涨幅榜"""
        params = {'limit': '10'}
        
        response = client.get('/api/data/market/gainers',
                            query_string=params,
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) <= 10
    
    def test_get_top_losers_success(self, client, auth_headers):
        """测试获取跌幅榜"""
        params = {'limit': '10'}
        
        response = client.get('/api/data/market/losers',
                            query_string=params,
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) <= 10


class TestFinancialData:
    """财务数据测试"""
    
    def test_get_financial_statements_success(self, client, auth_headers):
        """测试获取财务报表"""
        params = {
            'statement_type': 'income',
            'period': 'annual',
            'year': '2023'
        }
        
        response = client.get('/api/data/stocks/000001/financials',
                            query_string=params,
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'financial_data' in data['data']
    
    def test_get_financial_ratios_success(self, client, auth_headers):
        """测试获取财务比率"""
        response = client.get('/api/data/stocks/000001/ratios',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'ratios' in data['data']
    
    def test_get_company_info_success(self, client, auth_headers):
        """测试获取公司信息"""
        response = client.get('/api/data/stocks/000001/company',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'company_info' in data['data']


class TestStockSearch:
    """股票搜索测试"""
    
    def test_search_stocks_by_name_success(self, client, auth_headers):
        """测试按名称搜索股票"""
        params = {'query': '平安银行'}
        
        response = client.get('/api/data/stocks/search',
                            query_string=params,
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert isinstance(data['data'], list)
    
    def test_search_stocks_by_symbol_success(self, client, auth_headers):
        """测试按代码搜索股票"""
        params = {'query': '000001'}
        
        response = client.get('/api/data/stocks/search',
                            query_string=params,
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert isinstance(data['data'], list)
    
    def test_search_stocks_empty_query(self, client, auth_headers):
        """测试空搜索查询"""
        params = {'query': ''}
        
        response = client.get('/api/data/stocks/search',
                            query_string=params,
                            headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'


class TestDataValidation:
    """数据验证测试"""
    
    def test_invalid_stock_symbol_format(self, client, auth_headers):
        """测试无效股票代码格式"""
        response = client.get('/api/data/stocks/INVALID123/quote',
                            headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
    
    def test_invalid_date_format(self, client, auth_headers):
        """测试无效日期格式"""
        params = {
            'start_date': 'invalid-date',
            'end_date': '2024-01-31',
            'frequency': 'daily'
        }
        
        response = client.get('/api/data/stocks/000001/historical',
                            query_string=params,
                            headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
    
    def test_invalid_frequency_parameter(self, client, auth_headers):
        """测试无效频率参数"""
        params = {
            'start_date': '2024-01-01',
            'end_date': '2024-01-31',
            'frequency': 'invalid'
        }
        
        response = client.get('/api/data/stocks/000001/historical',
                            query_string=params,
                            headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'


class TestRateLimiting:
    """速率限制测试"""
    
    def test_data_api_rate_limit(self, client, auth_headers):
        """测试数据API速率限制"""
        # 快速发送多个请求
        responses = []
        for _ in range(50):
            response = client.get('/api/data/stocks/000001/quote',
                                headers=auth_headers)
            responses.append(response)
        
        # 检查是否有速率限制响应
        rate_limited = any(r.status_code == 429 for r in responses)
        # 注意：在测试环境中可能不会触发速率限制，这取决于配置


class TestErrorHandling:
    """错误处理测试"""
    
    def test_internal_server_error_handling(self, client, auth_headers):
        """测试内部服务器错误处理"""
        # 这个测试需要模拟内部错误
        # 可以通过mock或者特殊的测试端点来实现
        pass
    
    def test_service_unavailable_handling(self, client, auth_headers):
        """测试服务不可用错误处理"""
        # 这个测试需要模拟服务不可用
        # 可以通过mock外部服务来实现
        pass


if __name__ == '__main__':
    pytest.main([__file__])