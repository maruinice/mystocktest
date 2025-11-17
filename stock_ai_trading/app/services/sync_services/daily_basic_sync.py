"""
每日指标同步服务
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


class DailyBasicSyncService(BaseSyncService):
    """每日指标同步服务"""
    
    async def sync(self, start_date: str = None, end_date: str = None, **kwargs) -> Dict[str, Any]:
        """
        同步每日指标数据（按交易日期批量获取）
        
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
                last_date = await self.get_last_sync_date('daily_basic', 'trade_date')
                if last_date:
                    # 从最新日期的下一天开始
                    last_dt = datetime.strptime(last_date, '%Y%m%d')
                    start_dt = last_dt + timedelta(days=1)
                    start_date = start_dt.strftime('%Y%m%d')
                else:
                    # 默认从30天前开始
                    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            
            self.update_progress(0, 1, f"准备同步每日指标: {start_date} - {end_date}")
            
            # 获取交易日期列表
            trade_dates = await self._get_trade_dates(start_date, end_date)
            if not trade_dates:
                self.finish_sync(True, "没有需要同步的交易日")
                return {'success': True, 'message': '没有需要同步的交易日'}
            
            total_dates = len(trade_dates)
            total_count = 0
            
            self.update_progress(0, total_dates, f"开始同步 {total_dates} 个交易日的每日指标")
            
            # 按日期批量获取
            for i, trade_date in enumerate(trade_dates, 1):
                try:
                    # 调用Tushare API
                    df = self.pro.daily_basic(trade_date=trade_date)
                    
                    if not df.empty:
                        count = await self._save_daily_basic(df)
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
                'message': f'成功同步{total_count}条每日指标',
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
    
    async def _save_daily_basic(self, df: pd.DataFrame) -> int:
        """保存每日指标"""
        try:
            db = next(get_db())
            count = 0
            
            for _, row in df.iterrows():
                try:
                    insert_sql = text("""
                        INSERT INTO daily_basic 
                        (ts_code, trade_date, close, turnover_rate, turnover_rate_f, volume_ratio,
                         pe, pe_ttm, pb, ps, ps_ttm, dv_ratio, dv_ttm, total_share, float_share,
                         free_share, total_mv, circ_mv, updated_at)
                        VALUES (:ts_code, :trade_date, :close, :turnover_rate, :turnover_rate_f, :volume_ratio,
                                :pe, :pe_ttm, :pb, :ps, :ps_ttm, :dv_ratio, :dv_ttm, :total_share, :float_share,
                                :free_share, :total_mv, :circ_mv, NOW())
                        ON DUPLICATE KEY UPDATE
                        close = VALUES(close),
                        turnover_rate = VALUES(turnover_rate),
                        turnover_rate_f = VALUES(turnover_rate_f),
                        volume_ratio = VALUES(volume_ratio),
                        pe = VALUES(pe),
                        pe_ttm = VALUES(pe_ttm),
                        pb = VALUES(pb),
                        ps = VALUES(ps),
                        ps_ttm = VALUES(ps_ttm),
                        dv_ratio = VALUES(dv_ratio),
                        dv_ttm = VALUES(dv_ttm),
                        total_share = VALUES(total_share),
                        float_share = VALUES(float_share),
                        free_share = VALUES(free_share),
                        total_mv = VALUES(total_mv),
                        circ_mv = VALUES(circ_mv),
                        updated_at = NOW()
                    """)
                    
                    db.execute(insert_sql, {
                        'ts_code': row['ts_code'],
                        'trade_date': row['trade_date'],
                        'close': row.get('close', None),
                        'turnover_rate': row.get('turnover_rate', None),
                        'turnover_rate_f': row.get('turnover_rate_f', None),
                        'volume_ratio': row.get('volume_ratio', None),
                        'pe': row.get('pe', None),
                        'pe_ttm': row.get('pe_ttm', None),
                        'pb': row.get('pb', None),
                        'ps': row.get('ps', None),
                        'ps_ttm': row.get('ps_ttm', None),
                        'dv_ratio': row.get('dv_ratio', None),
                        'dv_ttm': row.get('dv_ttm', None),
                        'total_share': row.get('total_share', None),
                        'float_share': row.get('float_share', None),
                        'free_share': row.get('free_share', None),
                        'total_mv': row.get('total_mv', None),
                        'circ_mv': row.get('circ_mv', None)
                    })
                    
                    count += 1
                    
                except Exception as e:
                    logger.error(f"插入每日指标失败: {e}")
                    continue
            
            db.commit()
            return count
            
        except Exception as e:
            logger.error(f"保存每日指标失败: {e}")
            return 0
