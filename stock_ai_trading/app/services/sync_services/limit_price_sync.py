"""
涨跌停价格同步服务
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


class LimitPriceSyncService(BaseSyncService):
    """涨跌停价格同步服务"""
    
    async def sync(self, start_date: str = None, end_date: str = None, **kwargs) -> Dict[str, Any]:
        """
        同步涨跌停价格
        
        Args:
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
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
                # 默认同步最近30天的数据
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            
            self.update_progress(0, 1, f"准备同步涨跌停价格: {start_date} - {end_date}")
            
            # 获取交易日期列表
            trade_dates = await self._get_trade_dates(start_date, end_date)
            if not trade_dates:
                self.finish_sync(True, "没有需要同步的交易日")
                return {'success': True, 'message': '没有需要同步的交易日'}
            
            total_dates = len(trade_dates)
            total_count = 0
            
            self.update_progress(0, total_dates, f"开始同步 {total_dates} 个交易日的涨跌停价格")
            
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
                        trade_date = trade_date.replace('-', '')
                    
                    # 验证日期格式
                    if len(trade_date) != 8 or not trade_date.isdigit():
                        logger.warning(f"日期格式不正确: {trade_date_raw} -> {trade_date}，跳过")
                        continue
                    
                    logger.info(f"开始同步日期 {trade_date} ({i}/{total_dates})")
                    # 调用Tushare API（确保传递字符串）
                    df = self.pro.stk_limit(trade_date=str(trade_date))
                    
                    if not df.empty:
                        count = await self._save_limit_price_data(df)
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
                'message': f'成功同步{total_count}条涨跌停价格',
                'data': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'trade_dates': total_dates,
                    'saved_count': total_count
                }
            }
            
        except Exception as e:
            error_msg = f"同步涨跌停价格失败: {str(e)}"
            logger.error(error_msg)
            self.finish_sync(False, error_msg)
            return {'success': False, 'message': error_msg}
    
    async def _get_trade_dates(self, start_date: str, end_date: str) -> list:
        """获取交易日期列表"""
        try:
            db = next(get_db())
            query = text("""
                SELECT DISTINCT cal_date 
                FROM trade_cal 
                WHERE cal_date >= :start_date 
                AND cal_date <= :end_date 
                AND is_open = 1
                ORDER BY cal_date
            """)
            result = db.execute(query, {'start_date': start_date, 'end_date': end_date}).fetchall()
            trade_dates = []
            for row in result:
                date_val = row[0]
                # 确保日期格式为YYYYMMDD字符串
                if hasattr(date_val, 'strftime'):
                    trade_dates.append(date_val.strftime('%Y%m%d'))
                elif isinstance(date_val, str):
                    date_str = date_val.replace('-', '') if '-' in date_val else date_val
                    trade_dates.append(date_str)
                else:
                    date_str = str(date_val).replace('-', '')
                    trade_dates.append(date_str)
            logger.info(f"获取到 {len(trade_dates)} 个交易日")
            return trade_dates
        except Exception as e:
            logger.error(f"获取交易日期失败: {e}")
            return []
    
    async def _save_limit_price_data(self, df: pd.DataFrame) -> int:
        """
        保存涨跌停价格到数据库
        
        Args:
            df: 涨跌停价格数据DataFrame
            
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
                CREATE TABLE IF NOT EXISTS limit_prices (
                    ts_code VARCHAR(20) NOT NULL COMMENT '股票代码',
                    trade_date VARCHAR(8) NOT NULL COMMENT '交易日期',
                    pre_close DECIMAL(10, 2) COMMENT '昨收价',
                    up_limit DECIMAL(10, 2) COMMENT '涨停价',
                    down_limit DECIMAL(10, 2) COMMENT '跌停价',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (ts_code, trade_date),
                    INDEX idx_trade_date (trade_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='涨跌停价格表'
            """)
            db.execute(create_table_sql)
            db.commit()
            
            # 批量插入数据
            for _, row in df.iterrows():
                try:
                    insert_sql = text("""
                        INSERT INTO limit_prices 
                        (ts_code, trade_date, pre_close, up_limit, down_limit)
                        VALUES (:ts_code, :trade_date, :pre_close, :up_limit, :down_limit)
                        ON DUPLICATE KEY UPDATE
                            pre_close = VALUES(pre_close),
                            up_limit = VALUES(up_limit),
                            down_limit = VALUES(down_limit),
                            updated_at = CURRENT_TIMESTAMP
                    """)
                    
                    db.execute(insert_sql, {
                        'ts_code': row['ts_code'],
                        'trade_date': row['trade_date'],
                        'pre_close': row.get('pre_close'),
                        'up_limit': row.get('up_limit'),
                        'down_limit': row.get('down_limit')
                    })
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"保存涨跌停价格失败 {row.get('ts_code')}: {e}")
                    continue
            
            db.commit()
            logger.info(f"成功保存 {saved_count} 条涨跌停价格")
            
        except Exception as e:
            db.rollback()
            logger.error(f"保存涨跌停价格失败: {e}")
            raise
        finally:
            db.close()
        
        return saved_count

