"""
交易日历同步服务
"""

import logging
from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import text
import pandas as pd

from .base_sync_service import BaseSyncService
from app.core.database import get_db

logger = logging.getLogger(__name__)


class TradeCalSyncService(BaseSyncService):
    """交易日历同步服务"""
    
    async def sync(self, start_date: str = None, end_date: str = None, **kwargs) -> Dict[str, Any]:
        """
        同步交易日历（增量同步）
        
        Args:
            start_date: 开始日期 (YYYYMMDD)，默认为数据库最新日期
            end_date: 结束日期 (YYYYMMDD)，默认为今天
            
        Returns:
            同步结果
        """
        try:
            self.start_sync()
            
            if not self.pro:
                raise ValueError("Tushare API未初始化")
            
            # 如果没有指定开始日期，从数据库最新日期开始
            if not start_date:
                last_date = await self.get_last_sync_date('trade_cal', 'cal_date')
                if last_date:
                    # 从最新日期的下一天开始
                    last_dt = datetime.strptime(last_date, '%Y%m%d')
                    start_dt = last_dt + timedelta(days=1)
                    start_date = start_dt.strftime('%Y%m%d')
                else:
                    # 如果数据库为空，从3年前开始
                    start_dt = datetime.now() - timedelta(days=365*3)
                    start_date = start_dt.strftime('%Y%m%d')
            
            # 如果没有指定结束日期，使用今天
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            
            self.update_progress(0, 2, f"同步交易日历: {start_date} - {end_date}")
            
            # 获取上交所和深交所的交易日历
            logger.info(f"获取交易日历: {start_date} - {end_date}")
            
            sse_df = self.pro.trade_cal(exchange='SSE', start_date=start_date, end_date=end_date)
            szse_df = self.pro.trade_cal(exchange='SZSE', start_date=start_date, end_date=end_date)
            
            # 合并数据
            df = pd.concat([sse_df, szse_df], ignore_index=True)
            
            if df.empty:
                self.finish_sync(True)
                return {'success': True, 'message': '没有新数据需要同步'}
            
            total = len(df)
            self.update_progress(1, 2, f"获取到{total}条记录，开始保存...")
            
            # 保存到数据库
            db = next(get_db())
            saved_count = 0
            
            for idx, row in df.iterrows():
                try:
                    insert_sql = text("""
                        INSERT INTO trade_cal 
                        (exchange, cal_date, is_open, pretrade_date)
                        VALUES (:exchange, :cal_date, :is_open, :pretrade_date)
                        ON DUPLICATE KEY UPDATE
                        is_open = VALUES(is_open),
                        pretrade_date = VALUES(pretrade_date)
                    """)
                    
                    db.execute(insert_sql, {
                        'exchange': row['exchange'],
                        'cal_date': row['cal_date'],
                        'is_open': row['is_open'],
                        'pretrade_date': row.get('pretrade_date', '')
                    })
                    
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"保存交易日历{row['cal_date']}失败: {e}")
                    continue
            
            db.commit()
            
            self.update_progress(2, 2, f"同步完成，共{saved_count}条")
            self.finish_sync(True)
            
            return {
                'success': True,
                'message': f'成功同步{saved_count}条交易日历',
                'data': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'total': total,
                    'saved': saved_count,
                    'sync_time': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            error_msg = f"同步失败: {str(e)}"
            logger.error(error_msg)
            self.finish_sync(False, error_msg)
            return {'success': False, 'message': error_msg}
