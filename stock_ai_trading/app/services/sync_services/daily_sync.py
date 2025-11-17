"""
日线行情同步服务
基于 tushare_daily_service.py 改造
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


class DailySyncService(BaseSyncService):
    """日线行情同步服务"""
    
    async def sync(self, start_date: str = None, end_date: str = None, **kwargs) -> Dict[str, Any]:
        """
        同步日线行情数据（按日期批量获取）
        
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
            
            # 设置默认日期范围
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            
            if not start_date:
                # 从数据库获取最新日期
                last_date = await self.get_last_sync_date('daily_history', 'trade_date')
                if last_date:
                    # 从最新日期的下一天开始
                    last_dt = datetime.strptime(last_date, '%Y%m%d')
                    start_dt = last_dt + timedelta(days=1)
                    start_date = start_dt.strftime('%Y%m%d')
                else:
                    # 默认从30天前开始
                    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            
            self.update_progress(0, 1, f"准备同步日线行情: {start_date} - {end_date}")
            
            # 获取交易日期列表
            trade_dates = await self._get_trade_dates(start_date, end_date)
            if not trade_dates:
                self.finish_sync(True, "没有需要同步的交易日")
                return {'success': True, 'message': '没有需要同步的交易日'}
            
            total_dates = len(trade_dates)
            total_count = 0
            
            self.update_progress(0, total_dates, f"开始同步 {total_dates} 个交易日的行情数据")
            
            # 按日期批量获取
            for i, trade_date in enumerate(trade_dates, 1):
                try:
                    # 调用Tushare API
                    df = self.pro.daily(trade_date=trade_date)
                    
                    if not df.empty:
                        count = await self._save_daily_data(df)
                        total_count += count
                    
                    self.update_progress(
                        i,
                        total_dates,
                        f"已同步 {i}/{total_dates} 个交易日，共 {total_count} 条记录"
                    )
                    
                    # API频率控制
                    time.sleep(0.2)
                    
                except Exception as e:
                    logger.error(f"同步日期 {trade_date} 失败: {e}")
                    continue
            
            self.update_progress(total_dates, total_dates, f"同步完成，共 {total_count} 条记录")
            self.finish_sync(True)
            
            return {
                'success': True,
                'message': f'成功同步{total_count}条日线行情',
                'data': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'trade_dates': total_dates,
                    'total_records': total_count,
                    'sync_time': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            error_msg = f"同步失败: {str(e)}"
            logger.error(error_msg)
            self.finish_sync(False, error_msg)
            return {'success': False, 'message': error_msg}
    
    async def _get_trade_dates(self, start_date: str, end_date: str):
        """获取交易日期列表"""
        try:
            db = next(get_db())
            query = text("""
                SELECT DISTINCT cal_date 
                FROM trade_cal 
                WHERE is_open = 1 
                AND cal_date >= :start_date 
                AND cal_date <= :end_date
                ORDER BY cal_date
            """)
            result = db.execute(query, {'start_date': start_date, 'end_date': end_date}).fetchall()
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"获取交易日期失败: {e}")
            return []
    
    async def _save_daily_data(self, df: pd.DataFrame) -> int:
        """保存日线数据"""
        try:
            db = next(get_db())
            count = 0
            
            for _, row in df.iterrows():
                try:
                    insert_sql = text("""
                        INSERT INTO daily_history 
                        (ts_code, trade_date, open, high, low, close, pre_close, 
                         `change`, pct_chg, vol, amount, updated_at)
                        VALUES (:ts_code, :trade_date, :open, :high, :low, :close, :pre_close,
                                :change, :pct_chg, :vol, :amount, NOW())
                        ON DUPLICATE KEY UPDATE
                        open = VALUES(open),
                        high = VALUES(high),
                        low = VALUES(low),
                        close = VALUES(close),
                        pre_close = VALUES(pre_close),
                        `change` = VALUES(`change`),
                        pct_chg = VALUES(pct_chg),
                        vol = VALUES(vol),
                        amount = VALUES(amount),
                        updated_at = NOW()
                    """)
                    
                    db.execute(insert_sql, {
                        'ts_code': row['ts_code'],
                        'trade_date': row['trade_date'],
                        'open': row.get('open', None),
                        'high': row.get('high', None),
                        'low': row.get('low', None),
                        'close': row.get('close', None),
                        'pre_close': row.get('pre_close', None),
                        'change': row.get('change', None),
                        'pct_chg': row.get('pct_chg', None),
                        'vol': row.get('vol', None),
                        'amount': row.get('amount', None)
                    })
                    
                    count += 1
                    
                except Exception as e:
                    logger.error(f"插入日线数据失败: {e}")
                    continue
            
            db.commit()
            return count
            
        except Exception as e:
            logger.error(f"保存日线数据失败: {e}")
            return 0
