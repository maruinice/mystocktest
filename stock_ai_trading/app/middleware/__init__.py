"""
中间件包

提供认证、验证、错误处理和速率限制等中间件功能
"""

from .auth import AuthMiddleware, require_auth
from .validation import (
    ValidationMiddleware, ValidationError, Validator,
    StringValidator, IntegerValidator, FloatValidator, BooleanValidator,
    EmailValidator, DateTimeValidator, ListValidator, DictValidator,
    validate_json, validate_query_params, validate_form,
    CommonValidators
)
from .error_handler import (
    ErrorHandler, error_handler,
    APIError, ValidationError as ValidationAPIError, AuthenticationError,
    AuthorizationError, NotFoundError, ConflictError, RateLimitError,
    InternalServerError, ServiceUnavailableError,
    handle_errors, safe_execute,
    bad_request, unauthorized, forbidden, not_found, conflict,
    rate_limit_exceeded, internal_error, service_unavailable
)
from .rate_limiter import (
    RateLimiter, rate_limiter, rate_limit, add_rate_limit_headers,
    RateLimitConfig, auth_rate_limit, trading_rate_limit,
    data_rate_limit, strategy_rate_limit
)

__all__ = [
    # 认证相关
    'AuthMiddleware',
    'require_auth',
    
    # 验证中间件
    'ValidationMiddleware',
    'ValidationError',
    'Validator',
    'StringValidator',
    'IntegerValidator',
    'FloatValidator',
    'BooleanValidator',
    'EmailValidator',
    'DateTimeValidator',
    'ListValidator',
    'DictValidator',
    'validate_json',
    'validate_query_params',
    'validate_form',
    'CommonValidators',
    
    # 错误处理中间件
    'ErrorHandler',
    'error_handler',
    'APIError',
    'ValidationAPIError',
    'AuthenticationError',
    'AuthorizationError',
    'NotFoundError',
    'ConflictError',
    'RateLimitError',
    'InternalServerError',
    'ServiceUnavailableError',
    'handle_errors',
    'safe_execute',
    'bad_request',
    'unauthorized',
    'forbidden',
    'not_found',
    'conflict',
    'rate_limit_exceeded',
    'internal_error',
    'service_unavailable',
    
    # 速率限制中间件
    'RateLimiter',
    'rate_limiter',
    'rate_limit',
    'add_rate_limit_headers',
    'RateLimitConfig',
    'auth_rate_limit',
    'trading_rate_limit',
    'data_rate_limit',
    'strategy_rate_limit',
]