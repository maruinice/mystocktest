"""
认证中间件

用于API请求的身份验证和权限检查
"""

from functools import wraps
from typing import Optional, List, Callable, Any
from flask import request, jsonify, g
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta

from app.utils.jwt_utils import verify_and_decode_token, JWTError
from app.models.user_db import db_user_manager
from app.config.config import Config


class AuthMiddleware:
    """认证中间件"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
    
    def extract_token_from_request(self) -> Optional[str]:
        """从请求中提取令牌"""
        # 从Authorization头提取
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header[7:]  # 移除 'Bearer ' 前缀
        
        # 从查询参数提取
        token = request.args.get('token')
        if token:
            return token
        
        # 从表单数据提取
        token = request.form.get('token')
        if token:
            return token
        
        return None
    
    def authenticate_request(self) -> tuple[bool, Optional[dict], Optional[str]]:
        """认证请求"""
        token = self.extract_token_from_request()
        if not token:
            return False, None, "缺少认证令牌"
        
        try:
            # 使用数据库用户管理器验证token
            user = db_user_manager.verify_token(token)
            
            if not user:
                return False, None, "无效的认证令牌"
            
            if user.get('status') != 'active':
                return False, None, "用户已被禁用"
            
            # 检查token是否需要续期（剩余时间少于阈值时）
            try:
                payload = verify_and_decode_token(token)
                if payload and 'exp' in payload:
                    exp_time = datetime.fromtimestamp(payload['exp'])
                    now = datetime.now()
                    remaining_time = exp_time - now
                    
                    # 如果剩余时间少于阈值，生成新token并添加到响应头
                    threshold = Config.JWT_AUTO_REFRESH_THRESHOLD
                    if remaining_time < threshold:
                        new_token = db_user_manager.create_token(user)
                        g.new_token = new_token  # 存储新token，供after_request使用
            except Exception as e:
                # 续期失败不影响当前请求
                pass
            
            # 将用户信息存储到请求上下文
            g.current_user = user
            g.token = token
            
            return True, user, None
            
        except Exception as e:
            return False, None, f"认证失败: {str(e)}"
    
    def check_permission(self, required_permission: str) -> bool:
        """检查权限"""
        if not hasattr(g, 'current_user') or not g.current_user:
            return False
        
        return g.current_user.has_permission(required_permission)
    
    def check_rate_limit(self, identifier: str, limit: int, window: int) -> tuple[bool, dict]:
        """检查速率限制"""
        return self.rate_limiter.is_allowed(identifier, limit, window)


class RateLimiter:
    """速率限制器"""
    
    def __init__(self):
        self.requests = defaultdict(deque)
        self.cleanup_interval = 300  # 5分钟清理一次
        self.last_cleanup = time.time()
    
    def is_allowed(self, identifier: str, limit: int, window: int) -> tuple[bool, dict]:
        """检查是否允许请求"""
        now = time.time()
        
        # 定期清理过期记录
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup_expired_records(now)
            self.last_cleanup = now
        
        # 获取时间窗口内的请求记录
        requests = self.requests[identifier]
        
        # 移除过期的请求记录
        while requests and requests[0] <= now - window:
            requests.popleft()
        
        # 检查是否超过限制
        current_count = len(requests)
        if current_count >= limit:
            # 计算重置时间
            reset_time = requests[0] + window
            return False, {
                'allowed': False,
                'limit': limit,
                'remaining': 0,
                'reset_time': reset_time,
                'retry_after': int(reset_time - now)
            }
        
        # 记录当前请求
        requests.append(now)
        
        return True, {
            'allowed': True,
            'limit': limit,
            'remaining': limit - current_count - 1,
            'reset_time': now + window,
            'retry_after': 0
        }
    
    def _cleanup_expired_records(self, now: float):
        """清理过期的请求记录"""
        expired_keys = []
        for identifier, requests in self.requests.items():
            # 移除1小时前的记录
            while requests and requests[0] <= now - 3600:
                requests.popleft()
            
            # 如果队列为空，标记为待删除
            if not requests:
                expired_keys.append(identifier)
        
        # 删除空的记录
        for key in expired_keys:
            del self.requests[key]


# 全局中间件实例
auth_middleware = AuthMiddleware()


def require_auth(f: Callable) -> Callable:
    """需要认证的装饰器（生产级）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 进行真实的认证
        success, payload, error = auth_middleware.authenticate_request()
        if not success:
            # 如果认证失败，尝试使用默认用户（仅用于开发环境）
            import os
            if os.getenv('FLASK_ENV') == 'development':
                # 开发环境：使用默认用户
                if not hasattr(g, 'current_user') or not g.current_user:
                    g.current_user = {
                        'id': '1',
                        'user_id': '1',
                        'username': 'admin',
                        'email': 'admin@example.com',
                        'role': 'admin',
                        'permissions': ['user:read', 'user:write', 'user:delete',
                                      'trade:read', 'trade:write', 'trade:delete',
                                      'strategy:read', 'strategy:write', 'strategy:delete',
                                      'risk:read', 'risk:write',
                                      'system:read', 'system:write', 'system:control',
                                      'data:read']
                    }
            else:
                # 生产环境：返回401错误
                return jsonify({
                    'error': 'Authentication failed',
                    'message': error,
                    'code': 401
                }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_permission(permission: str):
    """需要特定权限的装饰器"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 先检查认证
            success, payload, error = auth_middleware.authenticate_request()
            if not success:
                return jsonify({
                    'error': 'Authentication failed',
                    'message': error,
                    'code': 401
                }), 401
            
            # 再检查权限
            if not auth_middleware.check_permission(permission):
                return jsonify({
                    'error': 'Permission denied',
                    'message': f'需要权限: {permission}',
                    'code': 403
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_permissions(permissions: List[str], require_all: bool = True):
    """需要多个权限的装饰器"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 先检查认证
            success, payload, error = auth_middleware.authenticate_request()
            if not success:
                return jsonify({
                    'error': 'Authentication failed',
                    'message': error,
                    'code': 401
                }), 401
            
            # 检查权限
            user_permissions = g.current_user.permissions
            if require_all:
                # 需要所有权限
                missing_permissions = [p for p in permissions if p not in user_permissions]
                if missing_permissions:
                    return jsonify({
                        'error': 'Permission denied',
                        'message': f'缺少权限: {", ".join(missing_permissions)}',
                        'code': 403
                    }), 403
            else:
                # 需要任一权限
                has_permission = any(p in user_permissions for p in permissions)
                if not has_permission:
                    return jsonify({
                        'error': 'Permission denied',
                        'message': f'需要以下权限之一: {", ".join(permissions)}',
                        'code': 403
                    }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def rate_limit(limit: int, window: int = 60, per: str = 'ip'):
    """速率限制装饰器"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 确定限制标识符
            if per == 'ip':
                identifier = request.remote_addr
            elif per == 'user':
                if hasattr(g, 'current_user') and g.current_user:
                    identifier = g.current_user.user_id
                else:
                    identifier = request.remote_addr
            else:
                identifier = request.remote_addr
            
            # 检查速率限制
            allowed, info = auth_middleware.check_rate_limit(identifier, limit, window)
            
            if not allowed:
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'请求过于频繁，请在 {info["retry_after"]} 秒后重试',
                    'code': 429,
                    'retry_after': info['retry_after']
                })
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(int(info['reset_time']))
                response.headers['Retry-After'] = str(info['retry_after'])
                return response, 429
            
            # 添加速率限制头部
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(int(info['reset_time']))
            
            return response
        
        return decorated_function
    return decorator


def optional_auth(f: Callable) -> Callable:
    """可选认证的装饰器（认证失败不会返回错误）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        success, payload, error = auth_middleware.authenticate_request()
        # 不管认证是否成功都继续执行
        return f(*args, **kwargs)
    
    return decorated_function


class APIKeyAuth:
    """API密钥认证"""
    
    @staticmethod
    def authenticate_api_key() -> tuple[bool, Optional[dict], Optional[str]]:
        """API密钥认证"""
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return False, None, "缺少API密钥"
        
        # 查找具有该API密钥的用户
        for user in user_manager.list_users():
            if user.api_key == api_key and user.is_active():
                g.current_user = user
                return True, {'sub': user.user_id, 'username': user.username}, None
        
        return False, None, "无效的API密钥"


def require_api_key(f: Callable) -> Callable:
    """需要API密钥的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        success, payload, error = APIKeyAuth.authenticate_api_key()
        if not success:
            return jsonify({
                'error': 'API key authentication failed',
                'message': error,
                'code': 401
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function