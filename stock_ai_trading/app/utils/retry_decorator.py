"""
重试装饰器
提供异常处理和重试机制
"""
import asyncio
import functools
import logging
import random
from typing import Callable, Any, Type, Tuple
import time

logger = logging.getLogger(__name__)

def retry_with_backoff(
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    max_backoff: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    jitter: bool = True
):
    """
    重试装饰器，支持指数退避和抖动
    
    Args:
        max_retries: 最大重试次数
        backoff_factor: 退避因子
        max_backoff: 最大退避时间
        exceptions: 需要重试的异常类型
        jitter: 是否添加随机抖动
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"函数 {func.__name__} 重试{max_retries}次后仍然失败: {str(e)}")
                        raise e
                    
                    # 计算退避时间
                    backoff_time = min(backoff_factor * (2 ** attempt), max_backoff)
                    
                    # 添加随机抖动
                    if jitter:
                        backoff_time *= (0.5 + random.random() * 0.5)
                    
                    logger.warning(f"函数 {func.__name__} 第{attempt + 1}次调用失败: {str(e)}, "
                                 f"{backoff_time:.2f}秒后重试")
                    
                    await asyncio.sleep(backoff_time)
            
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"函数 {func.__name__} 重试{max_retries}次后仍然失败: {str(e)}")
                        raise e
                    
                    # 计算退避时间
                    backoff_time = min(backoff_factor * (2 ** attempt), max_backoff)
                    
                    # 添加随机抖动
                    if jitter:
                        backoff_time *= (0.5 + random.random() * 0.5)
                    
                    logger.warning(f"函数 {func.__name__} 第{attempt + 1}次调用失败: {str(e)}, "
                                 f"{backoff_time:.2f}秒后重试")
                    
                    time.sleep(backoff_time)
            
            raise last_exception
        
        # 根据函数类型返回相应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: Type[Exception] = Exception
):
    """
    熔断器装饰器
    
    Args:
        failure_threshold: 失败阈值
        recovery_timeout: 恢复超时时间
        expected_exception: 预期的异常类型
    """
    def decorator(func: Callable) -> Callable:
        func._failure_count = 0
        func._last_failure_time = None
        func._state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            current_time = time.time()
            
            # 检查熔断器状态
            if func._state == 'OPEN':
                if current_time - func._last_failure_time < recovery_timeout:
                    raise Exception(f"熔断器开启，服务不可用")
                else:
                    func._state = 'HALF_OPEN'
                    logger.info(f"熔断器进入半开状态: {func.__name__}")
            
            try:
                result = await func(*args, **kwargs)
                
                # 成功调用，重置计数器
                if func._state == 'HALF_OPEN':
                    func._state = 'CLOSED'
                    func._failure_count = 0
                    logger.info(f"熔断器关闭: {func.__name__}")
                
                return result
                
            except expected_exception as e:
                func._failure_count += 1
                func._last_failure_time = current_time
                
                if func._failure_count >= failure_threshold:
                    func._state = 'OPEN'
                    logger.error(f"熔断器开启: {func.__name__}, 失败次数: {func._failure_count}")
                
                raise e
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            current_time = time.time()
            
            # 检查熔断器状态
            if func._state == 'OPEN':
                if current_time - func._last_failure_time < recovery_timeout:
                    raise Exception(f"熔断器开启，服务不可用")
                else:
                    func._state = 'HALF_OPEN'
                    logger.info(f"熔断器进入半开状态: {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                
                # 成功调用，重置计数器
                if func._state == 'HALF_OPEN':
                    func._state = 'CLOSED'
                    func._failure_count = 0
                    logger.info(f"熔断器关闭: {func.__name__}")
                
                return result
                
            except expected_exception as e:
                func._failure_count += 1
                func._last_failure_time = current_time
                
                if func._failure_count >= failure_threshold:
                    func._state = 'OPEN'
                    logger.error(f"熔断器开启: {func.__name__}, 失败次数: {func._failure_count}")
                
                raise e
        
        # 根据函数类型返回相应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def rate_limit(calls_per_second: float = 1.0):
    """
    限流装饰器
    
    Args:
        calls_per_second: 每秒允许的调用次数
    """
    def decorator(func: Callable) -> Callable:
        func._last_called = 0
        func._min_interval = 1.0 / calls_per_second
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            current_time = time.time()
            elapsed = current_time - func._last_called
            
            if elapsed < func._min_interval:
                sleep_time = func._min_interval - elapsed
                await asyncio.sleep(sleep_time)
            
            func._last_called = time.time()
            return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            current_time = time.time()
            elapsed = current_time - func._last_called
            
            if elapsed < func._min_interval:
                sleep_time = func._min_interval - elapsed
                time.sleep(sleep_time)
            
            func._last_called = time.time()
            return func(*args, **kwargs)
        
        # 根据函数类型返回相应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator