"""
API速率限制中间件

提供基于用户、IP和端点的速率限制功能
"""

import time
import json
from functools import wraps
from typing import Dict, Any, Optional, Tuple, Callable
from flask import request, g, current_app
from datetime import datetime, timedelta
import hashlib
import threading
from collections import defaultdict, deque

from .error_handler import RateLimitError


class RateLimiter:
    """速率限制器"""
    
    def __init__(self, app=None):
        self.app = app
        self.storage = {}  # 内存存储，生产环境建议使用Redis
        self.lock = threading.RLock()
        
        # 默认限制规则
        self.default_limits = {
            'global': {'requests': 1000, 'window': 3600},  # 全局限制：每小时1000次
            'per_ip': {'requests': 100, 'window': 3600},   # IP限制：每小时100次
            'per_user': {'requests': 500, 'window': 3600}, # 用户限制：每小时500次
            'auth': {'requests': 10, 'window': 900},       # 认证接口：每15分钟10次
            'trading': {'requests': 50, 'window': 60},     # 交易接口：每分钟50次
            'data': {'requests': 200, 'window': 3600},     # 数据接口：每小时200次
        }
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用"""
        self.app = app
        
        # 从配置中获取限制规则
        app_limits = app.config.get('RATE_LIMITS', {})
        self.default_limits.update(app_limits)
        
        # 注册请求前钩子
        app.before_request(self.check_rate_limit)
        
        # 启动清理任务
        self._start_cleanup_task()
    
    def _get_key(self, identifier: str, rule_name: str) -> str:
        """生成存储键"""
        return f"rate_limit:{rule_name}:{identifier}"
    
    def _get_window_start(self, window_seconds: int) -> int:
        """获取时间窗口开始时间"""
        now = int(time.time())
        return now - (now % window_seconds)
    
    def _is_rate_limited(self, key: str, limit: int, window: int) -> Tuple[bool, Dict[str, Any]]:
        """检查是否超过速率限制"""
        with self.lock:
            now = int(time.time())
            window_start = self._get_window_start(window)
            
            if key not in self.storage:
                self.storage[key] = {
                    'requests': deque(),
                    'window_start': window_start,
                    'count': 0
                }
            
            record = self.storage[key]
            
            # 如果窗口已过期，重置计数
            if record['window_start'] < window_start:
                record['requests'].clear()
                record['window_start'] = window_start
                record['count'] = 0
            
            # 清理过期的请求记录
            while record['requests'] and record['requests'][0] < window_start:
                record['requests'].popleft()
                record['count'] -= 1
            
            # 检查是否超限
            if record['count'] >= limit:
                # 计算重试时间
                retry_after = window_start + window - now
                return True, {
                    'limit': limit,
                    'remaining': 0,
                    'reset': window_start + window,
                    'retry_after': max(1, retry_after)
                }
            
            # 记录当前请求
            record['requests'].append(now)
            record['count'] += 1
            
            return False, {
                'limit': limit,
                'remaining': limit - record['count'],
                'reset': window_start + window,
                'retry_after': 0
            }
    
    def _get_identifier(self, rule_type: str) -> str:
        """获取标识符"""
        if rule_type == 'global':
            return 'global'
        elif rule_type == 'per_ip':
            return request.remote_addr or 'unknown'
        elif rule_type == 'per_user':
            user_id = getattr(g, 'current_user_id', None)
            if user_id:
                return f"user:{user_id}"
            else:
                return f"ip:{request.remote_addr or 'unknown'}"
        else:
            # 端点特定限制
            user_id = getattr(g, 'current_user_id', None)
            if user_id:
                return f"user:{user_id}:{rule_type}"
            else:
                return f"ip:{request.remote_addr or 'unknown'}:{rule_type}"
    
    def _get_endpoint_category(self, endpoint: str) -> str:
        """获取端点类别"""
        if '/auth/' in endpoint:
            return 'auth'
        elif '/trade/' in endpoint:
            return 'trading'
        elif any(x in endpoint for x in ['/stocks/', '/market/']):
            return 'data'
        else:
            return 'general'
    
    def check_rate_limit(self):
        """检查速率限制"""
        # 跳过静态文件和健康检查
        if request.endpoint in ['static', 'health_check'] or request.path.startswith('/static/'):
            return
        
        endpoint = request.endpoint or request.path
        category = self._get_endpoint_category(endpoint)
        
        # 要检查的限制规则
        rules_to_check = [
            ('global', 'global'),
            ('per_ip', 'per_ip'),
            ('per_user', 'per_user'),
        ]
        
        # 添加端点特定规则
        if category in self.default_limits:
            rules_to_check.append((category, category))
        
        # 检查每个规则
        for rule_name, rule_type in rules_to_check:
            if rule_name not in self.default_limits:
                continue
            
            limit_config = self.default_limits[rule_name]
            identifier = self._get_identifier(rule_type)
            key = self._get_key(identifier, rule_name)
            
            is_limited, info = self._is_rate_limited(
                key,
                limit_config['requests'],
                limit_config['window']
            )
            
            if is_limited:
                current_app.logger.warning(
                    f"速率限制触发 - 规则: {rule_name} - "
                    f"标识符: {identifier} - "
                    f"端点: {endpoint} - "
                    f"IP: {request.remote_addr}"
                )
                
                raise RateLimitError(
                    f"请求频率超限 ({rule_name})",
                    retry_after=info['retry_after']
                )
            
            # 设置响应头信息（使用最严格的限制）
            if not hasattr(g, 'rate_limit_info') or info['remaining'] < g.rate_limit_info['remaining']:
                g.rate_limit_info = info
    
    def _start_cleanup_task(self):
        """启动清理任务"""
        def cleanup():
            while True:
                try:
                    time.sleep(300)  # 每5分钟清理一次
                    self._cleanup_expired_records()
                except Exception as e:
                    current_app.logger.error(f"清理速率限制记录失败: {str(e)}")
        
        import threading
        cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_expired_records(self):
        """清理过期记录"""
        with self.lock:
            now = int(time.time())
            keys_to_remove = []
            
            for key, record in self.storage.items():
                # 如果记录超过1小时没有活动，删除它
                if record['requests'] and now - record['requests'][-1] > 3600:
                    keys_to_remove.append(key)
                elif not record['requests'] and now - record['window_start'] > 3600:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.storage[key]
            
            if keys_to_remove:
                current_app.logger.info(f"清理了 {len(keys_to_remove)} 个过期的速率限制记录")


# 全局速率限制器实例
rate_limiter = RateLimiter()


def rate_limit(requests: int, window: int, per: str = 'user', 
               key_func: Optional[Callable] = None):
    """
    速率限制装饰器
    
    Args:
        requests: 允许的请求数
        window: 时间窗口（秒）
        per: 限制类型 ('user', 'ip', 'endpoint')
        key_func: 自定义键生成函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成限制键
            if key_func:
                identifier = key_func()
            elif per == 'user':
                user_id = getattr(g, 'current_user_id', None)
                identifier = f"user:{user_id}" if user_id else f"ip:{request.remote_addr}"
            elif per == 'ip':
                identifier = f"ip:{request.remote_addr}"
            elif per == 'endpoint':
                identifier = f"endpoint:{request.endpoint}"
            else:
                identifier = f"custom:{per}"
            
            key = rate_limiter._get_key(identifier, func.__name__)
            
            # 检查限制
            is_limited, info = rate_limiter._is_rate_limited(key, requests, window)
            
            if is_limited:
                raise RateLimitError(
                    f"请求频率超限",
                    retry_after=info['retry_after']
                )
            
            # 设置响应头信息
            g.rate_limit_info = info
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def add_rate_limit_headers(response):
    """添加速率限制响应头"""
    if hasattr(g, 'rate_limit_info'):
        info = g.rate_limit_info
        response.headers['X-RateLimit-Limit'] = str(info['limit'])
        response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
        response.headers['X-RateLimit-Reset'] = str(info['reset'])
    
    return response


class RateLimitConfig:
    """速率限制配置"""
    
    # 认证相关接口限制
    AUTH_LIMITS = {
        'login': {'requests': 5, 'window': 300},      # 登录：5分钟5次
        'register': {'requests': 3, 'window': 3600},  # 注册：1小时3次
        'reset_password': {'requests': 3, 'window': 3600},  # 重置密码：1小时3次
    }
    
    # 交易相关接口限制
    TRADING_LIMITS = {
        'place_order': {'requests': 10, 'window': 60},     # 下单：1分钟10次
        'cancel_order': {'requests': 20, 'window': 60},    # 撤单：1分钟20次
        'query_orders': {'requests': 30, 'window': 60},    # 查询订单：1分钟30次
    }
    
    # 数据相关接口限制
    DATA_LIMITS = {
        'stock_quotes': {'requests': 100, 'window': 60},   # 股票行情：1分钟100次
        'market_data': {'requests': 50, 'window': 60},     # 市场数据：1分钟50次
        'financial_data': {'requests': 20, 'window': 60},  # 财务数据：1分钟20次
    }
    
    # 策略相关接口限制
    STRATEGY_LIMITS = {
        'backtest': {'requests': 5, 'window': 300},        # 回测：5分钟5次
        'signals': {'requests': 50, 'window': 60},         # 信号：1分钟50次
        'strategy_select': {'requests': 10, 'window': 300}, # 策略选择：5分钟10次
    }
    
    @classmethod
    def get_limit_for_endpoint(cls, endpoint: str) -> Optional[Dict[str, int]]:
        """获取端点的限制配置"""
        # 检查各个类别的限制
        for category_limits in [cls.AUTH_LIMITS, cls.TRADING_LIMITS, 
                               cls.DATA_LIMITS, cls.STRATEGY_LIMITS]:
            if endpoint in category_limits:
                return category_limits[endpoint]
        
        return None


# 预定义的速率限制装饰器
def auth_rate_limit(func):
    """认证接口速率限制"""
    endpoint = func.__name__
    limit_config = RateLimitConfig.get_limit_for_endpoint(endpoint)
    
    if limit_config:
        return rate_limit(
            limit_config['requests'],
            limit_config['window'],
            per='ip'
        )(func)
    else:
        return rate_limit(10, 900, per='ip')(func)  # 默认限制


def trading_rate_limit(func):
    """交易接口速率限制"""
    endpoint = func.__name__
    limit_config = RateLimitConfig.get_limit_for_endpoint(endpoint)
    
    if limit_config:
        return rate_limit(
            limit_config['requests'],
            limit_config['window'],
            per='user'
        )(func)
    else:
        return rate_limit(50, 60, per='user')(func)  # 默认限制


def data_rate_limit(func):
    """数据接口速率限制"""
    endpoint = func.__name__
    limit_config = RateLimitConfig.get_limit_for_endpoint(endpoint)
    
    if limit_config:
        return rate_limit(
            limit_config['requests'],
            limit_config['window'],
            per='user'
        )(func)
    else:
        return rate_limit(200, 3600, per='user')(func)  # 默认限制


def strategy_rate_limit(func):
    """策略接口速率限制"""
    endpoint = func.__name__
    limit_config = RateLimitConfig.get_limit_for_endpoint(endpoint)
    
    if limit_config:
        return rate_limit(
            limit_config['requests'],
            limit_config['window'],
            per='user'
        )(func)
    else:
        return rate_limit(30, 300, per='user')(func)  # 默认限制