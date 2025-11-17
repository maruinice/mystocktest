"""
数据存储优化服务
提供批量插入、去重、归档等功能
"""
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from sqlalchemy.dialects.mysql import insert
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json

from app.core.database import get_db, engine
from app.core.redis_client import redis_client
from app.models.stock_models import *
from app.utils.data_validator import DataValidator

logger = logging.getLogger(__name__)

class DataStorageService:
    """数据存储优化服务类"""
    
    def __init__(self):
        """初始化存储服务"""
        self.validator = DataValidator()
        self.batch_size = 1000  # 批量插入大小
        self.max_workers = 4    # 最大工作线程数
        
        # 去重配置
        self.dedup_config = {
            'stock_quotes': ['ts_code', 'trade_date'],
            'financial_data': ['ts_code', 'ann_date', 'end_date'],
            'stock_basic': ['ts_code'],
            'trade_records': ['portfolio_id', 'ts_code', 'trade_time'],
        }
        
        # 归档配置
        self.archive_config = {
            'stock_quotes': {'days': 365 * 2},      # 2年后归档
            'financial_data': {'days': 365 * 5},    # 5年后归档
            'trade_records': {'days': 365 * 3},     # 3年后归档
            'llm_decisions': {'days': 365 * 1},     # 1年后归档
        }
    
    def _generate_data_hash(self, data: Dict[str, Any], columns: List[str]) -> str:
        """生成数据哈希值用于去重"""
        hash_data = {col: data.get(col) for col in columns}
        hash_str = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.md5(hash_str.encode()).hexdigest()
    
    async def bulk_insert_with_dedup(self, table_name: str, data: List[Dict[str, Any]], 
                                   session: Session = None) -> Tuple[int, int]:
        """
        批量插入数据并去重
        
        Returns:
            Tuple[int, int]: (插入成功数量, 重复跳过数量)
        """
        if not data:
            return 0, 0
        
        if session is None:
            session = next(get_db())
        
        try:
            # 获取去重配置
            dedup_columns = self.dedup_config.get(table_name, [])
            
            inserted_count = 0
            duplicate_count = 0
            
            # 分批处理
            for i in range(0, len(data), self.batch_size):
                batch_data = data[i:i + self.batch_size]
                
                if dedup_columns:
                    # 使用MySQL的INSERT ... ON DUPLICATE KEY UPDATE
                    batch_inserted, batch_duplicates = await self._bulk_insert_mysql_dedup(
                        table_name, batch_data, dedup_columns, session
                    )
                else:
                    # 普通批量插入
                    batch_inserted = await self._bulk_insert_simple(
                        table_name, batch_data, session
                    )
                    batch_duplicates = 0
                
                inserted_count += batch_inserted
                duplicate_count += batch_duplicates
                
                logger.info(f"批次处理完成: 表{table_name}, 插入{batch_inserted}条, 重复{batch_duplicates}条")
            
            session.commit()
            logger.info(f"批量插入完成: 表{table_name}, 总插入{inserted_count}条, 总重复{duplicate_count}条")
            
            return inserted_count, duplicate_count
            
        except Exception as e:
            session.rollback()
            logger.error(f"批量插入失败: 表{table_name}, 错误: {str(e)}")
            raise
    
    async def _bulk_insert_mysql_dedup(self, table_name: str, data: List[Dict[str, Any]], 
                                     dedup_columns: List[str], session: Session) -> Tuple[int, int]:
        """使用MySQL的ON DUPLICATE KEY UPDATE进行去重插入"""
        if not data:
            return 0, 0
        
        # 构建INSERT ... ON DUPLICATE KEY UPDATE语句
        columns = list(data[0].keys())
        placeholders = ', '.join([f':{col}' for col in columns])
        
        # 构建更新子句（对于重复记录，更新非关键字段）
        update_columns = [col for col in columns if col not in dedup_columns]
        update_clause = ', '.join([f'{col} = VALUES({col})' for col in update_columns])
        
        if update_clause:
            sql = f"""
            INSERT INTO {table_name} ({', '.join(columns)})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE {update_clause}
            """
        else:
            sql = f"""
            INSERT IGNORE INTO {table_name} ({', '.join(columns)})
            VALUES ({placeholders})
            """
        
        try:
            result = session.execute(text(sql), data)
            
            # MySQL的affected_rows包含插入和更新的行数
            # 对于INSERT ... ON DUPLICATE KEY UPDATE:
            # - 插入新行返回1
            # - 更新现有行返回2
            # - 没有变化返回0
            affected_rows = result.rowcount
            
            # 估算插入和重复数量
            inserted_count = min(affected_rows, len(data))
            duplicate_count = len(data) - inserted_count
            
            return inserted_count, duplicate_count
            
        except Exception as e:
            logger.error(f"MySQL去重插入失败: {str(e)}")
            raise
    
    async def _bulk_insert_simple(self, table_name: str, data: List[Dict[str, Any]], 
                                session: Session) -> int:
        """简单批量插入"""
        if not data:
            return 0
        
        columns = list(data[0].keys())
        placeholders = ', '.join([f':{col}' for col in columns])
        
        sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        
        try:
            result = session.execute(text(sql), data)
            return result.rowcount
        except Exception as e:
            logger.error(f"批量插入失败: {str(e)}")
            raise
    
    async def check_data_exists(self, table_name: str, conditions: Dict[str, Any], 
                              session: Session = None) -> bool:
        """检查数据是否存在"""
        if session is None:
            session = next(get_db())
        
        where_clause = ' AND '.join([f'{k} = :{k}' for k in conditions.keys()])
        sql = f"SELECT 1 FROM {table_name} WHERE {where_clause} LIMIT 1"
        
        result = session.execute(text(sql), conditions)
        return result.fetchone() is not None
    
    async def get_duplicate_records(self, table_name: str, 
                                  dedup_columns: List[str] = None,
                                  session: Session = None) -> pd.DataFrame:
        """获取重复记录"""
        if session is None:
            session = next(get_db())
        
        if dedup_columns is None:
            dedup_columns = self.dedup_config.get(table_name, [])
        
        if not dedup_columns:
            return pd.DataFrame()
        
        # 构建查询重复记录的SQL
        group_columns = ', '.join(dedup_columns)
        sql = f"""
        SELECT {group_columns}, COUNT(*) as duplicate_count
        FROM {table_name}
        GROUP BY {group_columns}
        HAVING COUNT(*) > 1
        ORDER BY duplicate_count DESC
        """
        
        result = session.execute(text(sql))
        return pd.DataFrame(result.fetchall(), columns=result.keys())
    
    async def remove_duplicates(self, table_name: str, 
                              dedup_columns: List[str] = None,
                              keep: str = 'first',
                              session: Session = None) -> int:
        """
        移除重复数据
        
        Args:
            table_name: 表名
            dedup_columns: 去重列
            keep: 保留策略 ('first', 'last')
            session: 数据库会话
            
        Returns:
            int: 删除的记录数
        """
        if session is None:
            session = next(get_db())
        
        if dedup_columns is None:
            dedup_columns = self.dedup_config.get(table_name, [])
        
        if not dedup_columns:
            logger.warning(f"表{table_name}没有配置去重列")
            return 0
        
        try:
            # 获取主键列名（假设为id）
            pk_column = 'id'
            
            # 构建删除重复记录的SQL
            group_columns = ', '.join(dedup_columns)
            order_clause = f"{pk_column} ASC" if keep == 'first' else f"{pk_column} DESC"
            
            sql = f"""
            DELETE t1 FROM {table_name} t1
            INNER JOIN (
                SELECT {group_columns}, 
                       ROW_NUMBER() OVER (PARTITION BY {group_columns} ORDER BY {order_clause}) as rn
                FROM {table_name}
            ) t2 ON {' AND '.join([f't1.{col} = t2.{col}' for col in dedup_columns])}
            WHERE t2.rn > 1
            """
            
            result = session.execute(text(sql))
            deleted_count = result.rowcount
            
            session.commit()
            logger.info(f"删除重复记录: 表{table_name}, 删除{deleted_count}条")
            
            return deleted_count
            
        except Exception as e:
            session.rollback()
            logger.error(f"删除重复记录失败: 表{table_name}, 错误: {str(e)}")
            raise
    
    async def archive_old_data(self, table_name: str, 
                             archive_date: datetime = None,
                             session: Session = None) -> int:
        """
        归档历史数据
        
        Args:
            table_name: 表名
            archive_date: 归档日期，早于此日期的数据将被归档
            session: 数据库会话
            
        Returns:
            int: 归档的记录数
        """
        if session is None:
            session = next(get_db())
        
        # 获取归档配置
        archive_config = self.archive_config.get(table_name)
        if not archive_config:
            logger.warning(f"表{table_name}没有配置归档策略")
            return 0
        
        if archive_date is None:
            days_to_keep = archive_config['days']
            archive_date = datetime.now() - timedelta(days=days_to_keep)
        
        try:
            # 创建归档表（如果不存在）
            archive_table_name = f"{table_name}_archive"
            await self._create_archive_table(table_name, archive_table_name, session)
            
            # 确定日期列
            date_column = self._get_date_column(table_name)
            if not date_column:
                logger.warning(f"表{table_name}没有找到日期列")
                return 0
            
            # 移动数据到归档表
            move_sql = f"""
            INSERT INTO {archive_table_name}
            SELECT * FROM {table_name}
            WHERE {date_column} < :archive_date
            """
            
            result = session.execute(text(move_sql), {'archive_date': archive_date})
            archived_count = result.rowcount
            
            # 删除原表中的旧数据
            delete_sql = f"""
            DELETE FROM {table_name}
            WHERE {date_column} < :archive_date
            """
            
            session.execute(text(delete_sql), {'archive_date': archive_date})
            
            session.commit()
            logger.info(f"数据归档完成: 表{table_name}, 归档{archived_count}条记录")
            
            return archived_count
            
        except Exception as e:
            session.rollback()
            logger.error(f"数据归档失败: 表{table_name}, 错误: {str(e)}")
            raise
    
    async def _create_archive_table(self, source_table: str, archive_table: str, 
                                  session: Session):
        """创建归档表"""
        # 检查归档表是否存在
        check_sql = f"""
        SELECT COUNT(*) as count
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
        AND table_name = '{archive_table}'
        """
        
        result = session.execute(text(check_sql))
        exists = result.fetchone()[0] > 0
        
        if not exists:
            # 创建归档表（复制源表结构）
            create_sql = f"CREATE TABLE {archive_table} LIKE {source_table}"
            session.execute(text(create_sql))
            logger.info(f"创建归档表: {archive_table}")
    
    def _get_date_column(self, table_name: str) -> Optional[str]:
        """获取表的日期列名"""
        date_column_mapping = {
            'stock_quotes': 'trade_date',
            'financial_data': 'ann_date',
            'trade_records': 'trade_time',
            'llm_decisions': 'decision_time',
            'system_metrics': 'metric_time',
        }
        
        return date_column_mapping.get(table_name)
    
    async def optimize_table_performance(self, table_name: str, session: Session = None):
        """优化表性能"""
        if session is None:
            session = next(get_db())
        
        try:
            # 分析表
            session.execute(text(f"ANALYZE TABLE {table_name}"))
            
            # 优化表
            session.execute(text(f"OPTIMIZE TABLE {table_name}"))
            
            logger.info(f"表性能优化完成: {table_name}")
            
        except Exception as e:
            logger.error(f"表性能优化失败: 表{table_name}, 错误: {str(e)}")
            raise
    
    async def get_table_statistics(self, table_name: str, session: Session = None) -> Dict[str, Any]:
        """获取表统计信息"""
        if session is None:
            session = next(get_db())
        
        stats = {}
        
        try:
            # 获取行数
            count_sql = f"SELECT COUNT(*) as row_count FROM {table_name}"
            result = session.execute(text(count_sql))
            stats['row_count'] = result.fetchone()[0]
            
            # 获取表大小
            size_sql = f"""
            SELECT 
                ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb,
                ROUND((data_length / 1024 / 1024), 2) AS data_mb,
                ROUND((index_length / 1024 / 1024), 2) AS index_mb
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            AND table_name = '{table_name}'
            """
            
            result = session.execute(text(size_sql))
            size_info = result.fetchone()
            if size_info:
                stats['size_mb'] = size_info[0]
                stats['data_mb'] = size_info[1]
                stats['index_mb'] = size_info[2]
            
            # 获取最新数据时间
            date_column = self._get_date_column(table_name)
            if date_column:
                latest_sql = f"SELECT MAX({date_column}) as latest_date FROM {table_name}"
                result = session.execute(text(latest_sql))
                latest_date = result.fetchone()[0]
                stats['latest_date'] = latest_date
            
            return stats
            
        except Exception as e:
            logger.error(f"获取表统计信息失败: 表{table_name}, 错误: {str(e)}")
            return stats
    
    async def cache_frequently_accessed_data(self, table_name: str, 
                                           cache_key: str, 
                                           query_conditions: Dict[str, Any] = None,
                                           expire_seconds: int = 3600):
        """缓存频繁访问的数据"""
        try:
            # 构建查询SQL
            if query_conditions:
                where_clause = ' AND '.join([f'{k} = :{k}' for k in query_conditions.keys()])
                sql = f"SELECT * FROM {table_name} WHERE {where_clause}"
            else:
                sql = f"SELECT * FROM {table_name}"
            
            # 执行查询
            session = next(get_db())
            result = session.execute(text(sql), query_conditions or {})
            data = [dict(row) for row in result.fetchall()]
            
            # 缓存数据
            redis_client.set_json(cache_key, data, expire_seconds)
            
            logger.info(f"缓存数据: {cache_key}, {len(data)}条记录")
            
        except Exception as e:
            logger.error(f"缓存数据失败: {cache_key}, 错误: {str(e)}")
            raise

# 全局数据存储服务实例
data_storage_service = DataStorageService()