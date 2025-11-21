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
            for i, trade_date_raw in enumerate(trade_dates, 1):
                try:
                    # 确保trade_date是字符串格式（YYYYMMDD）
                    trade_date = trade_date_raw
                    if not isinstance(trade_date, str):
                        if hasattr(trade_date, 'strftime'):
                            trade_date = trade_date.strftime('%Y%m%d')
                        else:
                            trade_date = str(trade_date).replace('-', '')
                    elif '-' in trade_date:
                        # 如果字符串包含连字符，移除它
                        trade_date = trade_date.replace('-', '')
                    
                    # 验证日期格式
                    if len(trade_date) != 8 or not trade_date.isdigit():
                        logger.warning(f"日期格式不正确: {trade_date_raw} -> {trade_date}，跳过")
                        continue
                    
                    logger.info(f"开始同步日期 {trade_date} ({i}/{total_dates})")
                    # 调用Tushare API（确保传递字符串）
                    df = self.pro.daily(trade_date=str(trade_date))
                    
                    if df is None or df.empty:
                        logger.warning(f"日期 {trade_date} 没有数据或数据为空")
                        self.update_progress(
                            i,
                            total_dates,
                            f"已同步 {i}/{total_dates} 个交易日，共 {total_count} 条记录 (日期 {trade_date} 无数据)"
                        )
                    else:
                        logger.info(f"日期 {trade_date} 获取到 {len(df)} 条数据")
                        count = await self._save_daily_data(df)
                        total_count += count
                        logger.info(f"日期 {trade_date} 成功保存 {count} 条记录")
                        
                        self.update_progress(
                            i,
                            total_dates,
                            f"已同步 {i}/{total_dates} 个交易日，共 {total_count} 条记录"
                        )
                    
                    # API频率控制
                    time.sleep(0.2)
                    
                except Exception as e:
                    error_msg = str(e)
                    # 如果是日期序列化错误，记录更详细的信息
                    if 'JSON serializable' in error_msg or 'date' in error_msg.lower():
                        logger.error(f"同步日期 {trade_date} 失败 (日期格式错误): {error_msg}. trade_date类型: {type(trade_date)}, 值: {trade_date}")
                    else:
                        logger.error(f"同步日期 {trade_date} 失败: {error_msg}", exc_info=True)
                    self.update_progress(
                        i,
                        total_dates,
                        f"已同步 {i}/{total_dates} 个交易日，共 {total_count} 条记录 (日期 {trade_date} 失败: {error_msg[:50]})"
                    )
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
            trade_dates = []
            for row in result:
                date_val = row[0]
                # 确保日期格式为YYYYMMDD字符串
                if hasattr(date_val, 'strftime'):
                    # datetime.date或datetime.datetime对象
                    date_str = date_val.strftime('%Y%m%d')
                    trade_dates.append(date_str)
                elif isinstance(date_val, str):
                    # 如果是字符串，移除连字符
                    date_str = date_val.replace('-', '') if '-' in date_val else date_val
                    trade_dates.append(date_str)
                else:
                    # 其他类型，转换为字符串并移除连字符
                    date_str = str(date_val).replace('-', '')
                    trade_dates.append(date_str)
            logger.info(f"获取到 {len(trade_dates)} 个交易日: {trade_dates[:5]}...")
            return trade_dates
        except Exception as e:
            logger.error(f"获取交易日期失败: {e}")
            return []
    
    async def _save_daily_data(self, df: pd.DataFrame) -> int:
        """保存日线数据"""
        try:
            db = next(get_db())
            count = 0
            error_count = 0
            
            for idx, row in df.iterrows():
                try:
                    # 确保trade_date格式正确
                    trade_date = row.get('trade_date', '')
                    if hasattr(trade_date, 'strftime'):
                        trade_date = trade_date.strftime('%Y%m%d')
                    elif isinstance(trade_date, str) and '-' in trade_date:
                        trade_date = trade_date.replace('-', '')
                    
                    insert_sql = text("""
                        INSERT INTO daily_history 
                        (ts_code, trade_date, open_price, high_price, low_price, close_price, pre_close, 
                         change_amount, change_pct, volume, amount, updated_at)
                        VALUES (:ts_code, :trade_date, :open_price, :high_price, :low_price, :close_price, :pre_close,
                                :change_amount, :change_pct, :volume, :amount, NOW())
                        ON DUPLICATE KEY UPDATE
                        open_price = VALUES(open_price),
                        high_price = VALUES(high_price),
                        low_price = VALUES(low_price),
                        close_price = VALUES(close_price),
                        pre_close = VALUES(pre_close),
                        change_amount = VALUES(change_amount),
                        change_pct = VALUES(change_pct),
                        volume = VALUES(volume),
                        amount = VALUES(amount),
                        updated_at = NOW()
                    """)
                    
                    db.execute(insert_sql, {
                        'ts_code': row.get('ts_code', ''),
                        'trade_date': trade_date,
                        'open_price': row.get('open', None),
                        'high_price': row.get('high', None),
                        'low_price': row.get('low', None),
                        'close_price': row.get('close', None),
                        'pre_close': row.get('pre_close', None),
                        'change_amount': row.get('change', None),
                        'change_pct': row.get('pct_chg', None),
                        'volume': row.get('vol', None),
                        'amount': row.get('amount', None)
                    })
                    
                    count += 1
                    
                except Exception as e:
                    error_count += 1
                    if error_count <= 5:  # 只记录前5个错误，避免日志过多
                        logger.error(f"插入日线数据失败 (行 {idx}): {e}")
                    continue
            
            db.commit()
            if error_count > 0:
                logger.warning(f"保存数据完成: 成功 {count} 条，失败 {error_count} 条")
            else:
                logger.info(f"成功保存 {count} 条日线数据")
            return count
            
        except Exception as e:
            logger.error(f"保存日线数据失败: {e}", exc_info=True)
            db.rollback()
            return 0
