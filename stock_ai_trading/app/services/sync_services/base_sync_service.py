"""
同步服务基类
提供通用的同步功能：进度跟踪、断点续传、增量同步等
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
import tushare as ts

from app.config.settings import settings
from app.core.database import get_db

logger = logging.getLogger(__name__)


class BaseSyncService:
    """同步服务基类"""
    
    def __init__(self):
        """初始化同步服务"""
        self.token = settings.TUSHARE_TOKEN
        
        if not self.token:
            logger.warning("未配置Tushare Token")
            self.pro = None
        else:
            ts.set_token(self.token)
            self.pro = ts.pro_api()
        
        # 同步状态
        self.sync_status = {
            'is_running': False,
            'progress': 0,
            'total': 0,
            'current': 0,
            'message': '',
            'start_time': None,
            'end_time': None,
            'error': None
        }
    
    def get_sync_status(self) -> Dict[str, Any]:
        """获取同步状态"""
        return self.sync_status.copy()
    
    def update_progress(self, current: int, total: int, message: str = ''):
        """更新进度"""
        self.sync_status['current'] = current
        self.sync_status['total'] = total
        self.sync_status['progress'] = int((current / total * 100)) if total > 0 else 0
        self.sync_status['message'] = message
        logger.info(f"同步进度: {current}/{total} ({self.sync_status['progress']}%) - {message}")
    
    def start_sync(self):
        """开始同步"""
        self.sync_status['is_running'] = True
        self.sync_status['start_time'] = datetime.now().isoformat()
        self.sync_status['error'] = None
        self.sync_status['progress'] = 0
        self.sync_status['current'] = 0
        self.sync_status['total'] = 0
    
    def finish_sync(self, success: bool = True, error: str = None):
        """结束同步"""
        self.sync_status['is_running'] = False
        self.sync_status['end_time'] = datetime.now().isoformat()
        if error:
            self.sync_status['error'] = error
        if success:
            self.sync_status['progress'] = 100
    
    async def get_last_sync_date(self, table_name: str, date_field: str = 'trade_date') -> Optional[str]:
        """
        获取表中最新的同步日期
        
        Args:
            table_name: 表名
            date_field: 日期字段名
            
        Returns:
            最新日期（YYYYMMDD格式）
        """
        try:
            db = next(get_db())
            query = text(f"SELECT MAX({date_field}) as max_date FROM {table_name}")
            result = db.execute(query).fetchone()
            
            if result and result[0]:
                max_date = result[0]
                # 如果是datetime对象，转换为字符串
                if hasattr(max_date, 'strftime'):
                    return max_date.strftime('%Y%m%d')
            return None
            
        except Exception as e:
            logger.error(f"获取最新同步日期失败: {e}")
            return None
    
    async def get_record_count(self, table_name: str, condition: str = '') -> int:
        """
        获取表中记录数
        
        Args:
            table_name: 表名
            condition: WHERE条件（不包含WHERE关键字）
            
        Returns:
            记录数
        """
        try:
            db = next(get_db())
            where_clause = f" WHERE {condition}" if condition else ""
            query = text(f"SELECT COUNT(*) as count FROM {table_name}{where_clause}")
            result = db.execute(query).fetchone()
            return result[0] if result else 0
            
        except Exception as e:
            logger.error(f"获取记录数失败: {e}")
            return 0
    
    async def save_sync_position(self, sync_key: str, position: Any):
        """
        保存同步位置（用于断点续传）
        
        Args:
            sync_key: 同步任务唯一标识
            position: 当前位置（可以是索引、日期等）
        """
        try:
            db = next(get_db())
            
            # 创建同步位置表（如果不存在）
            create_table_sql = text("""
                CREATE TABLE IF NOT EXISTS sync_positions (
                    sync_key VARCHAR(100) PRIMARY KEY,
                    position VARCHAR(100),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            db.execute(create_table_sql)
            
            # 保存或更新位置
            upsert_sql = text("""
                INSERT INTO sync_positions (sync_key, position, updated_at)
                VALUES (:sync_key, :position, NOW())
                ON DUPLICATE KEY UPDATE position = :position, updated_at = NOW()
            """)
            db.execute(upsert_sql, {'sync_key': sync_key, 'position': str(position)})
            db.commit()
            
        except Exception as e:
            logger.error(f"保存同步位置失败: {e}")
    
    async def get_sync_position(self, sync_key: str) -> Optional[str]:
        """
        获取同步位置（用于断点续传）
        
        Args:
            sync_key: 同步任务唯一标识
            
        Returns:
            上次同步位置
        """
        try:
            db = next(get_db())
            query = text("SELECT position FROM sync_positions WHERE sync_key = :sync_key")
            result = db.execute(query, {'sync_key': sync_key}).fetchone()
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"获取同步位置失败: {e}")
            return None
    
    async def clear_sync_position(self, sync_key: str):
        """清除同步位置"""
        try:
            db = next(get_db())
            delete_sql = text("DELETE FROM sync_positions WHERE sync_key = :sync_key")
            db.execute(delete_sql, {'sync_key': sync_key})
            db.commit()
            
        except Exception as e:
            logger.error(f"清除同步位置失败: {e}")
    
    async def execute_with_retry(self, func: Callable, max_retries: int = 3, delay: float = 1.0):
        """
        带重试的执行函数
        
        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            delay: 重试延迟（秒）
        """
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"执行失败，{delay}秒后重试 ({attempt + 1}/{max_retries}): {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"执行失败，已达最大重试次数: {e}")
                    raise
    
    async def sync(self, **kwargs) -> Dict[str, Any]:
        """
        同步方法（子类需要实现）
        
        Returns:
            同步结果字典
        """
        raise NotImplementedError("子类必须实现sync方法")
