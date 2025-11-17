"""
Redis client configuration and utilities
"""
import redis
import json
import pickle
import logging
from typing import Optional, Any, Union, Dict, List
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis client wrapper"""
    
    def __init__(self):
        # 从环境变量获取Redis配置
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_db = int(os.getenv('REDIS_DB', 0))
        redis_password = os.getenv('REDIS_PASSWORD')
        
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=False,  # 保持二进制模式以支持pickle
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # 测试连接
        try:
            self.redis_client.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            # 不抛出异常，允许应用继续运行
    
    def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            
            # 尝试解码为字符串
            if isinstance(value, bytes):
                return value.decode('utf-8')
            return value
        except Exception as e:
            logger.error(f"Redis获取失败: key={key}, error={e}")
            return None
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set key-value pair with optional expiration"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            elif not isinstance(value, str):
                value = str(value)
            
            return self.redis_client.set(key, value, ex=expire)
        except Exception as e:
            logger.error(f"Redis设置失败: key={key}, error={e}")
            return False
    
    def delete(self, key: str) -> int:
        """Delete key"""
        try:
            return self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Redis删除失败: key={key}, error={e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Redis检查存在失败: key={key}, error={e}")
            return False
    
    def get_json(self, key: str) -> Optional[dict]:
        """Get JSON value by key"""
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            
            if isinstance(value, bytes):
                value = value.decode('utf-8')
            
            return json.loads(value)
        except Exception as e:
            logger.error(f"Redis获取JSON失败: key={key}, error={e}")
            return None
    
    def set_json(self, key: str, value: dict, expire: Optional[int] = None) -> bool:
        """Set JSON value with optional expiration"""
        try:
            json_str = json.dumps(value, ensure_ascii=False)
            return self.redis_client.set(key, json_str, ex=expire)
        except Exception as e:
            logger.error(f"Redis设置JSON失败: key={key}, error={e}")
            return False
    
    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """递增计数器"""
        try:
            return self.redis_client.incr(key, amount)
        except Exception as e:
            logger.error(f"Redis递增失败: key={key}, error={e}")
            return None
    
    def expire(self, key: str, seconds: int) -> bool:
        """设置键过期时间"""
        try:
            return bool(self.redis_client.expire(key, seconds))
        except Exception as e:
            logger.error(f"Redis设置过期时间失败: key={key}, error={e}")
            return False
    
    def ttl(self, key: str) -> int:
        """获取键剩余生存时间"""
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Redis获取TTL失败: key={key}, error={e}")
            return -1
    
    def hset(self, name: str, key: str, value: Any) -> bool:
        """设置哈希字段"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            return bool(self.redis_client.hset(name, key, value))
        except Exception as e:
            logger.error(f"Redis哈希设置失败: name={name}, key={key}, error={e}")
            return False
    
    def hget(self, name: str, key: str) -> Optional[Any]:
        """获取哈希字段"""
        try:
            value = self.redis_client.hget(name, key)
            if value is None:
                return None
            
            if isinstance(value, bytes):
                value = value.decode('utf-8')
            
            # 尝试JSON反序列化
            try:
                return json.loads(value)
            except:
                return value
        except Exception as e:
            logger.error(f"Redis哈希获取失败: name={name}, key={key}, error={e}")
            return None
    
    def lpush(self, key: str, *values: Any) -> Optional[int]:
        """从左侧推入列表"""
        try:
            serialized_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    serialized_values.append(json.dumps(value, ensure_ascii=False))
                else:
                    serialized_values.append(str(value))
            return self.redis_client.lpush(key, *serialized_values)
        except Exception as e:
            logger.error(f"Redis列表推入失败: key={key}, error={e}")
            return None
    
    def rpop(self, key: str) -> Optional[Any]:
        """从右侧弹出列表元素"""
        try:
            value = self.redis_client.rpop(key)
            if value is None:
                return None
            
            if isinstance(value, bytes):
                value = value.decode('utf-8')
            
            try:
                return json.loads(value)
            except:
                return value
        except Exception as e:
            logger.error(f"Redis列表弹出失败: key={key}, error={e}")
            return None
    
    def ping(self) -> bool:
        """检查连接"""
        try:
            return self.redis_client.ping()
        except Exception as e:
            logger.error(f"Redis ping失败: {e}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """获取Redis信息"""
        try:
            return self.redis_client.info()
        except Exception as e:
            logger.error(f"获取Redis信息失败: {e}")
            return {}

# Global Redis client instance
redis_client = RedisClient()