"""
统一错误处理中间件

提供统一的异常处理和错误响应格式
"""

from functools import wraps
from flask import jsonify, request, current_app, g
import traceback
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import uuid


class APIError(Exception):
    """API错误基类"""
    
    def __init__(self, message: str, code: str = None, status_code: int = 400, 
                 details: Dict[str, Any] = None):
        self.message = message
        self.code = code or 'api_error'
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            'error': self.code,
            'message': self.message,
            'timestamp': datetime.now().isoformat()
        }
        
        if self.details:
            result['details'] = self.details
        
        if hasattr(g, 'request_id'):
            result['request_id'] = g.request_id
        
        return result


class ValidationError(APIError):
    """验证错误"""
    
    def __init__(self, message: str, field: str = None, **kwargs):
        super().__init__(message, code='validation_error', status_code=400, **kwargs)
        if field:
            self.details['field'] = field


class AuthenticationError(APIError):
    """认证错误"""
    
    def __init__(self, message: str = "认证失败", **kwargs):
        super().__init__(message, code='authentication_error', status_code=401, **kwargs)


class AuthorizationError(APIError):
    """授权错误"""
    
    def __init__(self, message: str = "权限不足", **kwargs):
        super().__init__(message, code='authorization_error', status_code=403, **kwargs)


class NotFoundError(APIError):
    """资源未找到错误"""
    
    def __init__(self, message: str = "资源未找到", resource: str = None, **kwargs):
        super().__init__(message, code='not_found', status_code=404, **kwargs)
        if resource:
            self.details['resource'] = resource


class ConflictError(APIError):
    """冲突错误"""
    
    def __init__(self, message: str = "资源冲突", **kwargs):
        super().__init__(message, code='conflict', status_code=409, **kwargs)


class RateLimitError(APIError):
    """速率限制错误"""
    
    def __init__(self, message: str = "请求频率超限", retry_after: int = None, **kwargs):
        super().__init__(message, code='rate_limit_exceeded', status_code=429, **kwargs)
        if retry_after:
            self.details['retry_after'] = retry_after


class InternalServerError(APIError):
    """内部服务器错误"""
    
    def __init__(self, message: str = "内部服务器错误", **kwargs):
        super().__init__(message, code='internal_server_error', status_code=500, **kwargs)


class ServiceUnavailableError(APIError):
    """服务不可用错误"""
    
    def __init__(self, message: str = "服务暂时不可用", **kwargs):
        super().__init__(message, code='service_unavailable', status_code=503, **kwargs)


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用"""
        self.app = app
        
        # 注册错误处理器
        app.errorhandler(APIError)(self.handle_api_error)
        app.errorhandler(ValidationError)(self.handle_api_error)
        app.errorhandler(AuthenticationError)(self.handle_api_error)
        app.errorhandler(AuthorizationError)(self.handle_api_error)
        app.errorhandler(NotFoundError)(self.handle_api_error)
        app.errorhandler(ConflictError)(self.handle_api_error)
        app.errorhandler(RateLimitError)(self.handle_api_error)
        app.errorhandler(InternalServerError)(self.handle_api_error)
        app.errorhandler(ServiceUnavailableError)(self.handle_api_error)
        
        # 注册HTTP错误处理器
        app.errorhandler(400)(self.handle_bad_request)
        app.errorhandler(401)(self.handle_unauthorized)
        app.errorhandler(403)(self.handle_forbidden)
        app.errorhandler(404)(self.handle_not_found)
        app.errorhandler(405)(self.handle_method_not_allowed)
        app.errorhandler(429)(self.handle_rate_limit)
        app.errorhandler(500)(self.handle_internal_error)
        app.errorhandler(502)(self.handle_bad_gateway)
        app.errorhandler(503)(self.handle_service_unavailable)
        
        # 注册通用异常处理器
        app.errorhandler(Exception)(self.handle_generic_exception)
        
        # 注册请求钩子
        app.before_request(self.before_request)
    
    def before_request(self):
        """请求前处理"""
        # 生成请求ID
        g.request_id = str(uuid.uuid4())
        
        # 记录请求信息
        current_app.logger.info(
            f"请求开始 - ID: {g.request_id} - "
            f"方法: {request.method} - "
            f"路径: {request.path} - "
            f"IP: {request.remote_addr}"
        )
    
    def handle_api_error(self, error: APIError) -> Tuple[Dict[str, Any], int]:
        """处理API错误"""
        current_app.logger.warning(
            f"API错误 - ID: {getattr(g, 'request_id', 'unknown')} - "
            f"代码: {error.code} - "
            f"消息: {error.message}"
        )
        
        response = jsonify(error.to_dict())
        
        # 添加特殊头部
        if isinstance(error, RateLimitError) and 'retry_after' in error.details:
            response.headers['Retry-After'] = str(error.details['retry_after'])
        
        return response, error.status_code
    
    def handle_bad_request(self, error) -> Tuple[Dict[str, Any], int]:
        """处理400错误"""
        return self._create_error_response(
            'bad_request',
            '请求参数错误',
            400,
            {'description': str(error.description) if hasattr(error, 'description') else None}
        )
    
    def handle_unauthorized(self, error) -> Tuple[Dict[str, Any], int]:
        """处理401错误"""
        return self._create_error_response(
            'unauthorized',
            '未授权访问',
            401,
            {'description': str(error.description) if hasattr(error, 'description') else None}
        )
    
    def handle_forbidden(self, error) -> Tuple[Dict[str, Any], int]:
        """处理403错误"""
        return self._create_error_response(
            'forbidden',
            '访问被禁止',
            403,
            {'description': str(error.description) if hasattr(error, 'description') else None}
        )
    
    def handle_not_found(self, error) -> Tuple[Dict[str, Any], int]:
        """处理404错误"""
        return self._create_error_response(
            'not_found',
            '资源未找到',
            404,
            {
                'path': request.path,
                'method': request.method
            }
        )
    
    def handle_method_not_allowed(self, error) -> Tuple[Dict[str, Any], int]:
        """处理405错误"""
        return self._create_error_response(
            'method_not_allowed',
            '请求方法不被允许',
            405,
            {
                'method': request.method,
                'path': request.path,
                'allowed_methods': list(error.valid_methods) if hasattr(error, 'valid_methods') else None
            }
        )
    
    def handle_rate_limit(self, error) -> Tuple[Dict[str, Any], int]:
        """处理429错误"""
        response_data, status_code = self._create_error_response(
            'rate_limit_exceeded',
            '请求频率超限',
            429,
            {'description': str(error.description) if hasattr(error, 'description') else None}
        )
        
        response = jsonify(response_data)
        if hasattr(error, 'retry_after'):
            response.headers['Retry-After'] = str(error.retry_after)
        
        return response, status_code
    
    def handle_internal_error(self, error) -> Tuple[Dict[str, Any], int]:
        """处理500错误"""
        current_app.logger.error(
            f"内部服务器错误 - ID: {getattr(g, 'request_id', 'unknown')} - "
            f"错误: {str(error)}\n{traceback.format_exc()}"
        )
        
        return self._create_error_response(
            'internal_server_error',
            '内部服务器错误',
            500
        )
    
    def handle_bad_gateway(self, error) -> Tuple[Dict[str, Any], int]:
        """处理502错误"""
        return self._create_error_response(
            'bad_gateway',
            '网关错误',
            502
        )
    
    def handle_service_unavailable(self, error) -> Tuple[Dict[str, Any], int]:
        """处理503错误"""
        return self._create_error_response(
            'service_unavailable',
            '服务暂时不可用',
            503
        )
    
    def handle_generic_exception(self, error: Exception) -> Tuple[Dict[str, Any], int]:
        """处理通用异常"""
        current_app.logger.error(
            f"未处理的异常 - ID: {getattr(g, 'request_id', 'unknown')} - "
            f"类型: {type(error).__name__} - "
            f"消息: {str(error)}\n{traceback.format_exc()}"
        )
        
        # 在调试模式下返回详细错误信息
        if current_app.debug:
            return self._create_error_response(
                'unexpected_error',
                f'发生意外错误: {str(error)}',
                500,
                {
                    'type': type(error).__name__,
                    'traceback': traceback.format_exc().split('\n') if current_app.debug else None
                }
            )
        else:
            return self._create_error_response(
                'unexpected_error',
                '发生意外错误',
                500
            )
    
    def _create_error_response(self, code: str, message: str, status_code: int, 
                             details: Dict[str, Any] = None) -> Tuple[Dict[str, Any], int]:
        """创建错误响应"""
        response_data = {
            'error': code,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        if details:
            response_data['details'] = details
        
        if hasattr(g, 'request_id'):
            response_data['request_id'] = g.request_id
        
        return response_data, status_code


def handle_errors(func):
    """错误处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIError:
            # API错误直接抛出，由错误处理器处理
            raise
        except Exception as e:
            # 其他异常转换为内部服务器错误
            current_app.logger.error(f"函数 {func.__name__} 发生异常: {str(e)}")
            raise InternalServerError(f"执行 {func.__name__} 时发生错误")
    
    return wrapper


def safe_execute(func, *args, **kwargs):
    """安全执行函数"""
    try:
        return func(*args, **kwargs)
    except APIError:
        raise
    except Exception as e:
        current_app.logger.error(f"安全执行失败: {str(e)}")
        raise InternalServerError("操作执行失败")


# 创建全局错误处理器实例
error_handler = ErrorHandler()


# 常用错误快捷函数
def bad_request(message: str = "请求参数错误", **kwargs):
    """抛出400错误"""
    raise ValidationError(message, **kwargs)


def unauthorized(message: str = "认证失败", **kwargs):
    """抛出401错误"""
    raise AuthenticationError(message, **kwargs)


def forbidden(message: str = "权限不足", **kwargs):
    """抛出403错误"""
    raise AuthorizationError(message, **kwargs)


def not_found(message: str = "资源未找到", resource: str = None, **kwargs):
    """抛出404错误"""
    raise NotFoundError(message, resource=resource, **kwargs)


def conflict(message: str = "资源冲突", **kwargs):
    """抛出409错误"""
    raise ConflictError(message, **kwargs)


def rate_limit_exceeded(message: str = "请求频率超限", retry_after: int = None, **kwargs):
    """抛出429错误"""
    raise RateLimitError(message, retry_after=retry_after, **kwargs)


def internal_error(message: str = "内部服务器错误", **kwargs):
    """抛出500错误"""
    raise InternalServerError(message, **kwargs)


def service_unavailable(message: str = "服务暂时不可用", **kwargs):
    """抛出503错误"""
    raise ServiceUnavailableError(message, **kwargs)