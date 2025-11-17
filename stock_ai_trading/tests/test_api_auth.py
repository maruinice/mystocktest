"""
认证API测试用例
"""

import pytest
import json
from flask import Flask
from app.api.auth_api import auth_bp
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
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def sample_user():
    """示例用户数据"""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'Test123456',
        'phone': '13800138000'
    }


class TestUserRegistration:
    """用户注册测试"""
    
    def test_register_success(self, client, sample_user):
        """测试成功注册"""
        response = client.post('/api/auth/register', 
                             data=json.dumps(sample_user),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'user_id' in data['data']
        assert data['data']['username'] == sample_user['username']
    
    def test_register_missing_fields(self, client):
        """测试缺少必填字段"""
        incomplete_user = {
            'username': 'testuser',
            'email': 'test@example.com'
            # 缺少password
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(incomplete_user),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
    
    def test_register_invalid_email(self, client, sample_user):
        """测试无效邮箱格式"""
        sample_user['email'] = 'invalid-email'
        
        response = client.post('/api/auth/register',
                             data=json.dumps(sample_user),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
    
    def test_register_weak_password(self, client, sample_user):
        """测试弱密码"""
        sample_user['password'] = '123'
        
        response = client.post('/api/auth/register',
                             data=json.dumps(sample_user),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'
    
    def test_register_duplicate_username(self, client, sample_user):
        """测试重复用户名"""
        # 第一次注册
        client.post('/api/auth/register',
                   data=json.dumps(sample_user),
                   content_type='application/json')
        
        # 第二次注册相同用户名
        response = client.post('/api/auth/register',
                             data=json.dumps(sample_user),
                             content_type='application/json')
        
        assert response.status_code == 409
        data = json.loads(response.data)
        assert data['error'] == 'conflict'


class TestUserLogin:
    """用户登录测试"""
    
    def test_login_success(self, client, sample_user):
        """测试成功登录"""
        # 先注册用户
        client.post('/api/auth/register',
                   data=json.dumps(sample_user),
                   content_type='application/json')
        
        # 登录
        login_data = {
            'username': sample_user['username'],
            'password': sample_user['password']
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'access_token' in data['data']
        assert 'refresh_token' in data['data']
        assert 'expires_in' in data['data']
    
    def test_login_invalid_credentials(self, client, sample_user):
        """测试无效凭据"""
        # 先注册用户
        client.post('/api/auth/register',
                   data=json.dumps(sample_user),
                   content_type='application/json')
        
        # 使用错误密码登录
        login_data = {
            'username': sample_user['username'],
            'password': 'wrongpassword'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'authentication_error'
    
    def test_login_nonexistent_user(self, client):
        """测试不存在的用户"""
        login_data = {
            'username': 'nonexistent',
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'authentication_error'
    
    def test_login_missing_fields(self, client):
        """测试缺少登录字段"""
        login_data = {
            'username': 'testuser'
            # 缺少password
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'


class TestTokenOperations:
    """令牌操作测试"""
    
    def test_refresh_token_success(self, client, sample_user):
        """测试成功刷新令牌"""
        # 注册并登录
        client.post('/api/auth/register',
                   data=json.dumps(sample_user),
                   content_type='application/json')
        
        login_response = client.post('/api/auth/login',
                                   data=json.dumps({
                                       'username': sample_user['username'],
                                       'password': sample_user['password']
                                   }),
                                   content_type='application/json')
        
        login_data = json.loads(login_response.data)
        refresh_token = login_data['data']['refresh_token']
        
        # 刷新令牌
        response = client.post('/api/auth/refresh',
                             data=json.dumps({'refresh_token': refresh_token}),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'access_token' in data['data']
        assert 'expires_in' in data['data']
    
    def test_refresh_token_invalid(self, client):
        """测试无效刷新令牌"""
        response = client.post('/api/auth/refresh',
                             data=json.dumps({'refresh_token': 'invalid_token'}),
                             content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'authentication_error'
    
    def test_logout_success(self, client, sample_user):
        """测试成功登出"""
        # 注册并登录
        client.post('/api/auth/register',
                   data=json.dumps(sample_user),
                   content_type='application/json')
        
        login_response = client.post('/api/auth/login',
                                   data=json.dumps({
                                       'username': sample_user['username'],
                                       'password': sample_user['password']
                                   }),
                                   content_type='application/json')
        
        login_data = json.loads(login_response.data)
        access_token = login_data['data']['access_token']
        
        # 登出
        response = client.post('/api/auth/logout',
                             headers={'Authorization': f'Bearer {access_token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True


class TestUserProfile:
    """用户资料测试"""
    
    def test_get_profile_success(self, client, sample_user):
        """测试获取用户资料"""
        # 注册并登录
        client.post('/api/auth/register',
                   data=json.dumps(sample_user),
                   content_type='application/json')
        
        login_response = client.post('/api/auth/login',
                                   data=json.dumps({
                                       'username': sample_user['username'],
                                       'password': sample_user['password']
                                   }),
                                   content_type='application/json')
        
        login_data = json.loads(login_response.data)
        access_token = login_data['data']['access_token']
        
        # 获取资料
        response = client.get('/api/auth/profile',
                            headers={'Authorization': f'Bearer {access_token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['username'] == sample_user['username']
        assert data['data']['email'] == sample_user['email']
    
    def test_get_profile_unauthorized(self, client):
        """测试未授权获取资料"""
        response = client.get('/api/auth/profile')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'authentication_error'
    
    def test_update_profile_success(self, client, sample_user):
        """测试更新用户资料"""
        # 注册并登录
        client.post('/api/auth/register',
                   data=json.dumps(sample_user),
                   content_type='application/json')
        
        login_response = client.post('/api/auth/login',
                                   data=json.dumps({
                                       'username': sample_user['username'],
                                       'password': sample_user['password']
                                   }),
                                   content_type='application/json')
        
        login_data = json.loads(login_response.data)
        access_token = login_data['data']['access_token']
        
        # 更新资料
        update_data = {
            'email': 'newemail@example.com',
            'phone': '13900139000'
        }
        
        response = client.put('/api/auth/profile',
                            data=json.dumps(update_data),
                            content_type='application/json',
                            headers={'Authorization': f'Bearer {access_token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['email'] == update_data['email']
        assert data['data']['phone'] == update_data['phone']


class TestPasswordOperations:
    """密码操作测试"""
    
    def test_change_password_success(self, client, sample_user):
        """测试成功修改密码"""
        # 注册并登录
        client.post('/api/auth/register',
                   data=json.dumps(sample_user),
                   content_type='application/json')
        
        login_response = client.post('/api/auth/login',
                                   data=json.dumps({
                                       'username': sample_user['username'],
                                       'password': sample_user['password']
                                   }),
                                   content_type='application/json')
        
        login_data = json.loads(login_response.data)
        access_token = login_data['data']['access_token']
        
        # 修改密码
        password_data = {
            'old_password': sample_user['password'],
            'new_password': 'NewPassword123'
        }
        
        response = client.post('/api/auth/change-password',
                             data=json.dumps(password_data),
                             content_type='application/json',
                             headers={'Authorization': f'Bearer {access_token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_change_password_wrong_old_password(self, client, sample_user):
        """测试错误的旧密码"""
        # 注册并登录
        client.post('/api/auth/register',
                   data=json.dumps(sample_user),
                   content_type='application/json')
        
        login_response = client.post('/api/auth/login',
                                   data=json.dumps({
                                       'username': sample_user['username'],
                                       'password': sample_user['password']
                                   }),
                                   content_type='application/json')
        
        login_data = json.loads(login_response.data)
        access_token = login_data['data']['access_token']
        
        # 使用错误的旧密码
        password_data = {
            'old_password': 'wrongpassword',
            'new_password': 'NewPassword123'
        }
        
        response = client.post('/api/auth/change-password',
                             data=json.dumps(password_data),
                             content_type='application/json',
                             headers={'Authorization': f'Bearer {access_token}'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'validation_error'


class TestRateLimiting:
    """速率限制测试"""
    
    def test_login_rate_limit(self, client, sample_user):
        """测试登录速率限制"""
        # 注册用户
        client.post('/api/auth/register',
                   data=json.dumps(sample_user),
                   content_type='application/json')
        
        login_data = {
            'username': sample_user['username'],
            'password': 'wrongpassword'  # 故意使用错误密码
        }
        
        # 快速发送多个登录请求
        responses = []
        for _ in range(10):
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            responses.append(response)
        
        # 检查是否有速率限制响应
        rate_limited = any(r.status_code == 429 for r in responses)
        assert rate_limited, "应该触发速率限制"


if __name__ == '__main__':
    pytest.main([__file__])