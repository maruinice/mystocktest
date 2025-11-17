"""
系统API测试用例
"""

import pytest
import json
from flask import Flask
from app.api.system_api import system_bp
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
    app.register_blueprint(system_bp, url_prefix='/api/system')
    
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def admin_headers(client):
    """获取管理员认证头"""
    return {'Authorization': 'Bearer admin_token'}


@pytest.fixture
def user_headers(client):
    """获取普通用户认证头"""
    return {'Authorization': 'Bearer user_token'}


class TestSystemHealth:
    """系统健康检查测试"""
    
    def test_health_check_success(self, client):
        """测试健康检查成功"""
        response = client.get('/api/system/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'status' in data['data']
        assert 'timestamp' in data['data']
        assert 'version' in data['data']
    
    def test_health_check_detailed(self, client, admin_headers):
        """测试详细健康检查"""
        response = client.get('/api/system/health?detailed=true',
                            headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'database' in data['data']
        assert 'redis' in data['data']
        assert 'external_apis' in data['data']
    
    def test_readiness_check(self, client):
        """测试就绪检查"""
        response = client.get('/api/system/ready')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'ready' in data['data']
    
    def test_liveness_check(self, client):
        """测试存活检查"""
        response = client.get('/api/system/live')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'alive' in data['data']


class TestSystemInfo:
    """系统信息测试"""
    
    def test_get_system_info_success(self, client, admin_headers):
        """测试获取系统信息"""
        response = client.get('/api/system/info',
                            headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'version' in data['data']
        assert 'environment' in data['data']
        assert 'uptime' in data['data']
        assert 'python_version' in data['data']
    
    def test_get_system_info_unauthorized(self, client, user_headers):
        """测试未授权获取系统信息"""
        response = client.get('/api/system/info',
                            headers=user_headers)
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['error'] == 'authorization_error'
    
    def test_get_system_stats_success(self, client, admin_headers):
        """测试获取系统统计"""
        response = client.get('/api/system/stats',
                            headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'cpu_usage' in data['data']
        assert 'memory_usage' in data['data']
        assert 'disk_usage' in data['data']
    
    def test_get_api_stats_success(self, client, admin_headers):
        """测试获取API统计"""
        response = client.get('/api/system/api-stats',
                            headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'total_requests' in data['data']
        assert 'requests_by_endpoint' in data['data']
        assert 'response_times' in data['data']


class TestSystemConfiguration:
    """系统配置测试"""
    
    def test_get_config_success(self, client, admin_headers):
        """测试获取系统配置"""
        response = client.get('/api/system/config',
                            headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'database' in data['data']
        assert 'redis' in data['data']
        assert 'logging' in data['data']
    
    def test_update_config_success(self, client, admin_headers):
        """测试更新系统配置"""
        config_update = {
            'logging': {
                'level': 'INFO'
            },
            'rate_limiting': {
                'enabled': True,
                'default_limit': '100/hour'
            }
        }
        
        response = client.put('/api/system/config',
                            data=json.dumps(config_update),
                            content_type='application/json',
                            headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_update_config_unauthorized(self, client, user_headers):
        """测试未授权更新配置"""
        config_update = {
            'logging': {
                'level': 'DEBUG'
            }
        }
        
        response = client.put('/api/system/config',
                            data=json.dumps(config_update),
                            content_type='application/json',
                            headers=user_headers)
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['error'] == 'authorization_error'
    
    def test_get_feature_flags_success(self, client, admin_headers):
        """测试获取功能开关"""
        response = client.get('/api/system/features',
                            headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert isinstance(data['data'], dict)
    
    def test_update_feature_flags_success(self, client, admin_headers):
        """测试更新功能开关"""
        features = {
            'ai_trading': True,
            'advanced_analytics': False,
            'paper_trading': True
        }
        
        response = client.put('/api/system/features',
                            data=json.dumps(features),
                            content_type='application/json',
                            headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True


class TestSystemMaintenance:
    """系统维护测试"""
    
    def test_enable_maintenance_mode(self, client, admin_headers):
        """测试启用维护模式"""
        maintenance_data = {
            'enabled': True,
            'message': '系统维护中，预计1小时后恢复',
            'estimated_duration': 3600
        }
        
        response = client.post('/api/system/maintenance',
                             data=json.dumps(maintenance_data),
                             content_type='application/json',
                             headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_disable_maintenance_mode(self, client, admin_headers):
        """测试禁用维护模式"""
        maintenance_data = {
            'enabled': False
        }
        
        response = client.post('/api/system/maintenance',
                             data=json.dumps(maintenance_data),
                             content_type='application/json',
                             headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_get_maintenance_status(self, client):
        """测试获取维护状态"""
        response = client.get('/api/system/maintenance')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'enabled' in data['data']
    
    def test_clear_cache_success(self, client, admin_headers):
        """测试清除缓存"""
        response = client.post('/api/system/cache/clear',
                             headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_clear_specific_cache_success(self, client, admin_headers):
        """测试清除特定缓存"""
        cache_data = {
            'keys': ['user_sessions', 'market_data']
        }
        
        response = client.post('/api/system/cache/clear',
                             data=json.dumps(cache_data),
                             content_type='application/json',
                             headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True


class TestSystemLogs:
    """系统日志测试"""
    
    def test_get_logs_success(self, client, admin_headers):
        """测试获取系统日志"""
        response = client.get('/api/system/logs',
                            headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert isinstance(data['data'], list)
    
    def test_get_logs_with_filters(self, client, admin_headers):
        """测试带过滤条件的日志查询"""
        params = {
            'level': 'ERROR',
            'start_time': '2024-01-01T00:00:00Z',
            'end_time': '2024-12-31T23:59:59Z',
            'limit': '50'
        }
        
        response = client.get('/api/system/logs',
                            query_string=params,
                            headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) <= 50
    
    def test_get_logs_unauthorized(self, client, user_headers):
        """测试未授权获取日志"""
        response = client.get('/api/system/logs',
                            headers=user_headers)
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['error'] == 'authorization_error'
    
    def test_get_error_logs_success(self, client, admin_headers):
        """测试获取错误日志"""
        response = client.get('/api/system/logs/errors',
                            headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert isinstance(data['data'], list)
    
    def test_export_logs_success(self, client, admin_headers):
        """测试导出日志"""
        params = {
            'format': 'csv',
            'start_time': '2024-01-01T00:00:00Z',
            'end_time': '2024-12-31T23:59:59Z'
        }
        
        response = client.get('/api/system/logs/export',
                            query_string=params,
                            headers=admin_headers)
        
        assert response.status_code == 200
        assert response.content_type == 'text/csv'


class TestSystemBackup:
    """系统备份测试"""
    
    def test_create_backup_success(self, client, admin_headers):
        """测试创建备份"""
        backup_data = {
            'type': 'full',
            'description': '定期全量备份'
        }
        
        response = client.post('/api/system/backup',
                             data=json.dumps(backup_data),
                             content_type='application/json',
                             headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'backup_id' in data['data']
    
    def test_create_incremental_backup(self, client, admin_headers):
        """测试创建增量备份"""
        backup_data = {
            'type': 'incremental',
            'description': '增量备份'
        }
        
        response = client.post('/api/system/backup',
                             data=json.dumps(backup_data),
                             content_type='application/json',
                             headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_get_backup_list_success(self, client, admin_headers):
        """测试获取备份列表"""
        response = client.get('/api/system/backup',
                            headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert isinstance(data['data'], list)
    
    def test_get_backup_status_success(self, client, admin_headers):
        """测试获取备份状态"""
        # 先创建一个备份
        backup_data = {'type': 'full'}
        backup_response = client.post('/api/system/backup',
                                    data=json.dumps(backup_data),
                                    content_type='application/json',
                                    headers=admin_headers)
        
        backup_result = json.loads(backup_response.data)
        backup_id = backup_result['data']['backup_id']
        
        # 获取备份状态
        response = client.get(f'/api/system/backup/{backup_id}',
                            headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'status' in data['data']
    
    def test_restore_backup_success(self, client, admin_headers):
        """测试恢复备份"""
        # 这需要先有一个可用的备份
        restore_data = {
            'backup_id': 'test_backup_id',
            'confirm': True
        }
        
        response = client.post('/api/system/restore',
                             data=json.dumps(restore_data),
                             content_type='application/json',
                             headers=admin_headers)
        
        # 在测试环境中可能返回404（备份不存在）
        assert response.status_code in [200, 404]


class TestSystemMonitoring:
    """系统监控测试"""
    
    def test_get_metrics_success(self, client, admin_headers):
        """测试获取系统指标"""
        response = client.get('/api/system/metrics',
                            headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'system' in data['data']
        assert 'application' in data['data']
    
    def test_get_alerts_success(self, client, admin_headers):
        """测试获取系统告警"""
        response = client.get('/api/system/alerts',
                            headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert isinstance(data['data'], list)
    
    def test_get_active_alerts_success(self, client, admin_headers):
        """测试获取活跃告警"""
        response = client.get('/api/system/alerts?status=active',
                            headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_acknowledge_alert_success(self, client, admin_headers):
        """测试确认告警"""
        alert_data = {
            'alert_id': 'test_alert_id',
            'acknowledged_by': 'admin'
        }
        
        response = client.post('/api/system/alerts/acknowledge',
                             data=json.dumps(alert_data),
                             content_type='application/json',
                             headers=admin_headers)
        
        # 在测试环境中可能返回404（告警不存在）
        assert response.status_code in [200, 404]


class TestSystemSecurity:
    """系统安全测试"""
    
    def test_get_security_events_success(self, client, admin_headers):
        """测试获取安全事件"""
        response = client.get('/api/system/security/events',
                            headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert isinstance(data['data'], list)
    
    def test_get_failed_logins_success(self, client, admin_headers):
        """测试获取登录失败记录"""
        response = client.get('/api/system/security/failed-logins',
                            headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert isinstance(data['data'], list)
    
    def test_block_ip_success(self, client, admin_headers):
        """测试封禁IP"""
        block_data = {
            'ip_address': '192.168.1.100',
            'reason': '恶意攻击',
            'duration': 3600  # 1小时
        }
        
        response = client.post('/api/system/security/block-ip',
                             data=json.dumps(block_data),
                             content_type='application/json',
                             headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_unblock_ip_success(self, client, admin_headers):
        """测试解封IP"""
        unblock_data = {
            'ip_address': '192.168.1.100'
        }
        
        response = client.post('/api/system/security/unblock-ip',
                             data=json.dumps(unblock_data),
                             content_type='application/json',
                             headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True


class TestParameterValidation:
    """参数验证测试"""
    
    def test_invalid_log_level_filter(self, client, admin_headers):
        """测试无效日志级别过滤"""
        params = {
            'level': 'INVALID_LEVEL'
        }
        
        response = client.get('/api/system/logs',
                            query_string=params,
                            headers=admin_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
    
    def test_invalid_backup_type(self, client, admin_headers):
        """测试无效备份类型"""
        backup_data = {
            'type': 'invalid_type'
        }
        
        response = client.post('/api/system/backup',
                             data=json.dumps(backup_data),
                             content_type='application/json',
                             headers=admin_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
    
    def test_invalid_ip_address_format(self, client, admin_headers):
        """测试无效IP地址格式"""
        block_data = {
            'ip_address': 'invalid_ip',
            'reason': '测试'
        }
        
        response = client.post('/api/system/security/block-ip',
                             data=json.dumps(block_data),
                             content_type='application/json',
                             headers=admin_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'


class TestAuthentication:
    """认证测试"""
    
    def test_system_info_without_auth(self, client):
        """测试未认证获取系统信息"""
        response = client.get('/api/system/info')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'authentication_error'
    
    def test_config_update_without_auth(self, client):
        """测试未认证更新配置"""
        config_update = {
            'logging': {
                'level': 'DEBUG'
            }
        }
        
        response = client.put('/api/system/config',
                            data=json.dumps(config_update),
                            content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'authentication_error'
    
    def test_backup_without_auth(self, client):
        """测试未认证创建备份"""
        backup_data = {
            'type': 'full'
        }
        
        response = client.post('/api/system/backup',
                             data=json.dumps(backup_data),
                             content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'authentication_error'


class TestErrorHandling:
    """错误处理测试"""
    
    def test_invalid_json_format(self, client, admin_headers):
        """测试无效JSON格式"""
        response = client.post('/api/system/backup',
                             data='invalid json',
                             content_type='application/json',
                             headers=admin_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
    
    def test_missing_content_type(self, client, admin_headers):
        """测试缺少内容类型"""
        backup_data = {
            'type': 'full'
        }
        
        response = client.post('/api/system/backup',
                             data=json.dumps(backup_data),
                             headers=admin_headers)
        
        assert response.status_code == 400


if __name__ == '__main__':
    pytest.main([__file__])