"""
停复牌信息同步服务
"""

import logging
import time
from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import text
import pandas as pd

from .base_sync_service import BaseSyncService
from app.core.database import get_db

logger = logging.getLogger(__name__)


class SuspendSyncService(BaseSyncService):
    """停复牌信息同步服务"""
    
    async def sync(self, start_date: str = None, end_date: str = None, direction: str = 'forward', days: int = 30, **kwargs) -> Dict[str, Any]:
        """
        同步停复牌信息（支持增量同步和历史追溯）
        
        Args:
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            direction: 同步方向 ('forward': 向后/最新, 'backward': 向前/历史)
            days: 同步天数（默认30天）
            
        Returns:
            同步结果
        """
        try:
            self.start_sync()
            
            if not self.pro:
                raise ValueError("Tushare API未初始化")
            
            # 根据 direction 确定日期范围
            if not start_date or not end_date:
                # 获取数据库中的日期范围
                date_range = await self.get_sync_date_range('suspend_info', 'suspend_date')
                min_date = date_range.get('min_date')
                max_date = date_range.get('max_date')
                
                if direction == 'forward':
                    # 向后更新：从 max_date + 1 到今天
                    if max_date:
                        last_dt = datetime.strptime(max_date, '%Y%m%d')
                        start_dt = last_dt + timedelta(days=1)
                        start_date = start_dt.strftime('%Y%m%d')
                    else:
                        # 如果数据库为空，默认同步最近30天
                        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
                    
                    end_date = datetime.now().strftime('%Y%m%d')
                    
                elif direction == 'backward':
                    # 向前追溯：从 min_date - days 到 min_date - 1
                    if min_date:
                        end_dt = datetime.strptime(min_date, '%Y%m%d') - timedelta(days=1)
                        end_date = end_dt.strftime('%Y%m%d')
                        start_dt = end_dt - timedelta(days=days)
                        start_date = start_dt.strftime('%Y%m%d')
                    else:
                        # 如果数据库为空，从指定天数前开始到今天
                        end_date = datetime.now().strftime('%Y%m%d')
                        start_dt = datetime.now() - timedelta(days=days)
                        start_date = start_dt.strftime('%Y%m%d')
            
            # 如果开始日期晚于结束日期，说明不需要同步
            if start_date > end_date:
                self.finish_sync(True, "没有需要同步的数据")
                return {'success': True, 'message': '没有需要同步的数据'}
            
            self.update_progress(0, 1, f"准备同步停复牌信息 ({'向后' if direction == 'forward' else '向前'}): {start_date} - {end_date}")
            
            # 调用Tushare API获取停复牌信息
            logger.info(f"从Tushare获取停复牌信息: {start_date} - {end_date}")
            df = self.pro.suspend_d(
                start_date=start_date,
                end_date=end_date
            )
            
            if df.empty:
                self.finish_sync(True, "没有停复牌信息")
                return {'success': True, 'message': '没有停复牌信息'}
            
            total = len(df)
            self.update_progress(0, total, f"获取到{total}条停复牌信息，开始保存...")
            
            # 保存到数据库
            saved_count = await self._save_suspend_data(df)
            
            self.update_progress(total, total, f"同步完成，共 {saved_count} 条记录")
            self.finish_sync(True)
            
            return {
                'success': True,
                'message': f'成功同步{saved_count}条停复牌信息',
                'data': {
                    'direction': direction,
                    'start_date': start_date,
                    'end_date': end_date,
                    'saved_count': saved_count,
                    'total_count': total
                }
            }
            
        except Exception as e:
            error_msg = f"同步停复牌信息失败: {str(e)}"
            logger.error(error_msg)
            self.finish_sync(False, error_msg)
            return {'success': False, 'message': error_msg}
    
    async def _save_suspend_data(self, df: pd.DataFrame) -> int:
        """
        保存停复牌信息到数据库
        
        Args:
            df: 停复牌数据DataFrame
            
        Returns:
            保存的记录数
        """
        if df.empty:
            return 0
        
        db = next(get_db())
        saved_count = 0
        
        try:
            # 确保表存在
            create_table_sql = text("""
                CREATE TABLE IF NOT EXISTS suspend_info (
                    ts_code VARCHAR(20) NOT NULL COMMENT '股票代码',
                    suspend_date VARCHAR(8) NOT NULL COMMENT '停牌日期',
                    resume_date VARCHAR(8) COMMENT '复牌日期',
                    suspend_timing VARCHAR(10) COMMENT '停牌时间段',
                    suspend_type VARCHAR(50) COMMENT '停牌类型',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (ts_code, suspend_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='停复牌信息表'
            """)
            db.execute(create_table_sql)
            db.commit()
            
            # 批量插入数据
            for _, row in df.iterrows():
                try:
                    insert_sql = text("""
                        INSERT INTO suspend_info 
                        (ts_code, suspend_date, resume_date, suspend_timing, suspend_type)
                        VALUES (:ts_code, :suspend_date, :resume_date, :suspend_timing, :suspend_type)
                        ON DUPLICATE KEY UPDATE
                            resume_date = VALUES(resume_date),
                            suspend_timing = VALUES(suspend_timing),
                            suspend_type = VALUES(suspend_type),
                            updated_at = CURRENT_TIMESTAMP
                    """)
                    
                    # 确保日期格式正确
                    suspend_date = row.get('suspend_date', '')
                    if hasattr(suspend_date, 'strftime'):
                        suspend_date = suspend_date.strftime('%Y%m%d')
                    elif isinstance(suspend_date, str) and '-' in suspend_date:
                        suspend_date = suspend_date.replace('-', '')
                    
                    resume_date = row.get('resume_date', '')
                    if resume_date:
                        if hasattr(resume_date, 'strftime'):
                            resume_date = resume_date.strftime('%Y%m%d')
                        elif isinstance(resume_date, str) and '-' in resume_date:
                            resume_date = resume_date.replace('-', '')
                    
                    db.execute(insert_sql, {
                        'ts_code': row.get('ts_code', ''),
                        'suspend_date': suspend_date,
                        'resume_date': resume_date if resume_date else None,
                        'suspend_timing': row.get('suspend_timing'),
                        'suspend_type': row.get('suspend_type')
                    })
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"保存停复牌信息失败 {row.get('ts_code')}: {e}")
                    continue
            
            db.commit()
            logger.info(f"成功保存 {saved_count} 条停复牌信息")
            
        except Exception as e:
            db.rollback()
            logger.error(f"保存停复牌信息失败: {e}")
            raise
        finally:
            db.close()
        
        return saved_count

