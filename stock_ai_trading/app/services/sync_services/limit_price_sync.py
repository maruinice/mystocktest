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
    
    async def sync(self, start_date: str = None, end_date: str = None, direction: str = 'forward', days: int = 30, **kwargs) -> Dict[str, Any]:
        """
        同步涨跌停价格（支持增量同步和历史追溯）
        
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
                date_range = await self.get_sync_date_range('limit_prices', 'trade_date')
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
            
            self.update_progress(0, 1, f"准备同步涨跌停价格 ({'向后' if direction == 'forward' else '向前'}): {start_date} - {end_date}")
            
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
                    
                    # 添加调试信息
                    if df.empty:
                        logger.warning(f"日期 {trade_date} 返回空数据（可能该日期没有涨跌停股票）")
                    else:
                        logger.info(f"日期 {trade_date} 获取到 {len(df)} 条数据，字段: {list(df.columns)}")
                    
                    if not df.empty:
                        count = await self._save_limit_price_data(df)
                        total_count += count
                        if count == 0:
                            logger.warning(f"日期 {trade_date} 数据获取成功但保存失败，请检查字段映射")
                    
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
                    'direction': direction,
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
        error_count = 0
        
        try:
            # 注意：不在这里创建表，使用现有的表结构
            # 实际表结构中的trade_date是DATE类型，不是VARCHAR
            
            # 检查必需的字段是否存在
            required_fields = ['ts_code', 'trade_date']
            missing_fields = [f for f in required_fields if f not in df.columns]
            if missing_fields:
                logger.error(f"DataFrame缺少必需字段: {missing_fields}，可用字段: {list(df.columns)}")
                return 0
            
            # 批量插入数据
            for idx, row in df.iterrows():
                try:
                    # 使用安全的字段访问方式
                    ts_code = row.get('ts_code') or row.get('TS_CODE') or ''
                    trade_date_raw = row.get('trade_date') or row.get('TRADE_DATE') or ''
                    
                    # 处理trade_date格式（可能是字符串YYYYMMDD或日期对象）
                    # 注意：数据库表中trade_date是DATE类型，需要转换为date对象
                    from datetime import datetime as dt
                    trade_date_obj = None
                    
                    if isinstance(trade_date_raw, str):
                        # 字符串格式：可能是YYYYMMDD或YYYY-MM-DD
                        date_str = trade_date_raw.replace('-', '')[:8]
                        if len(date_str) == 8 and date_str.isdigit():
                            try:
                                trade_date_obj = dt.strptime(date_str, '%Y%m%d').date()
                            except ValueError:
                                logger.warning(f"日期格式解析失败: {trade_date_raw}")
                                error_count += 1
                                continue
                        else:
                            logger.warning(f"日期格式不正确: {trade_date_raw}")
                            error_count += 1
                            continue
                    elif hasattr(trade_date_raw, 'date'):
                        # datetime对象，转换为date
                        trade_date_obj = trade_date_raw.date()
                    elif hasattr(trade_date_raw, 'strftime'):
                        # datetime对象
                        trade_date_obj = trade_date_raw.date()
                    else:
                        # 尝试转换为字符串再解析
                        try:
                            date_str = str(trade_date_raw).replace('-', '')[:8]
                            if len(date_str) == 8 and date_str.isdigit():
                                trade_date_obj = dt.strptime(date_str, '%Y%m%d').date()
                            else:
                                raise ValueError(f"无法解析日期: {trade_date_raw}")
                        except (ValueError, AttributeError) as e:
                            logger.warning(f"日期转换失败: {trade_date_raw}, 错误: {e}")
                            error_count += 1
                            continue
                    
                    # 验证数据
                    if not ts_code or not trade_date_obj:
                        logger.warning(f"跳过无效数据: ts_code={ts_code}, trade_date={trade_date_raw}")
                        error_count += 1
                        continue
                    
                    # 注意：数据库表中没有pre_close字段，只有close、up_limit、down_limit等
                    insert_sql = text("""
                        INSERT INTO limit_prices 
                        (ts_code, trade_date, up_limit, down_limit, close)
                        VALUES (:ts_code, :trade_date, :up_limit, :down_limit, :close)
                        ON DUPLICATE KEY UPDATE
                            up_limit = VALUES(up_limit),
                            down_limit = VALUES(down_limit),
                            close = VALUES(close)
                    """)
                    
                    db.execute(insert_sql, {
                        'ts_code': ts_code,
                        'trade_date': trade_date_obj,
                        'up_limit': row.get('up_limit') or row.get('UP_LIMIT'),
                        'down_limit': row.get('down_limit') or row.get('DOWN_LIMIT'),
                        'close': row.get('close') or row.get('CLOSE')
                    })
                    saved_count += 1
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"保存涨跌停价格失败 [行{idx}]: ts_code={row.get('ts_code', 'N/A')}, 错误: {e}")
                    # 记录前几条错误的详细信息
                    if error_count <= 3:
                        logger.error(f"  行数据: {dict(row)}")
                    continue
            
            db.commit()
            logger.info(f"成功保存 {saved_count} 条涨跌停价格，失败 {error_count} 条")
            
        except Exception as e:
            db.rollback()
            logger.error(f"保存涨跌停价格失败: {e}")
            raise
        finally:
            db.close()
        
        return saved_count

