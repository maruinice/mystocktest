"""
审计意见同步服务
基于 sync_audit_opinions.py 改造
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


class AuditOpinionSyncService(BaseSyncService):
    """审计意见同步服务"""
    
    async def sync(self, start_date: str = None, end_date: str = None, start_position: int = 1, direction: str = 'forward', days: int = 365, **kwargs) -> Dict[str, Any]:
        """
        同步审计意见数据
        
        Args:
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            start_position: 起始位置（断点续传）
            direction: 同步方向 ('forward': 向后/最新, 'backward': 向前/历史)
            days: 向前同步时的天数
            
        Returns:
            同步结果
        """
        try:
            self.start_sync()
            
            if not self.pro:
                raise ValueError("Tushare API未初始化")
            
            # 获取所有股票代码
            stock_codes = await self._get_all_stock_codes()
            if not stock_codes:
                self.finish_sync(False, "未找到股票代码")
                return {'success': False, 'message': '未找到股票代码'}
            
            total_stocks = len(stock_codes)
            
            # 检查断点续传
            saved_position = await self.get_sync_position('audit_opinion_sync')
            if saved_position and start_position == 1:
                start_position = int(saved_position)
                logger.info(f"从断点位置继续: {start_position}")
            
            if start_position > total_stocks:
                self.finish_sync(False, f"起始位置超出范围: {start_position} > {total_stocks}")
                return {'success': False, 'message': '起始位置超出范围'}
            
            self.update_progress(0, total_stocks, f"开始同步 {total_stocks} 只股票的审计意见 ({'向后' if direction == 'forward' else '向前'})")
            
            # 逐个股票同步
            total_count = 0
            success_count = 0
            
            # 预先获取每只股票的日期范围
            stock_date_ranges = await self._get_all_stocks_date_ranges()
            
            for i, ts_code in enumerate(stock_codes[start_position-1:], start_position):
                try:
                    # 确定该股票的同步日期范围
                    stock_start_date = start_date
                    stock_end_date = end_date
                    
                    if not stock_start_date or not stock_end_date:
                        min_date, max_date = stock_date_ranges.get(ts_code, (None, None))
                        
                        if direction == 'forward':
                            # 向后同步：从 max_date + 1 到 今天
                            if max_date:
                                stock_start_date = (datetime.strptime(max_date, '%Y%m%d') + timedelta(days=1)).strftime('%Y%m%d')
                            else:
                                # 如果没有数据，默认同步最近3年
                                stock_start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y%m%d')
                            
                            stock_end_date = datetime.now().strftime('%Y%m%d')
                            
                        elif direction == 'backward':
                            # 向前同步：从 min_date - days 到 min_date - 1
                            if min_date:
                                stock_end_date = (datetime.strptime(min_date, '%Y%m%d') - timedelta(days=1)).strftime('%Y%m%d')
                                stock_start_date = (datetime.strptime(stock_end_date, '%Y%m%d') - timedelta(days=days)).strftime('%Y%m%d')
                            else:
                                # 如果没有数据，默认同步最近3年
                                stock_end_date = datetime.now().strftime('%Y%m%d')
                                stock_start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y%m%d')
                    
                    # 如果开始日期晚于结束日期，说明不需要同步
                    if stock_start_date > stock_end_date:
                        continue
                        
                    count = await self._sync_stock_audit_opinions(
                        ts_code, stock_start_date, stock_end_date
                    )
                    
                    if count > 0:
                        success_count += 1
                        total_count += count
                    
                    # 更新进度
                    self.update_progress(
                        i, 
                        total_stocks, 
                        f"已同步 {i}/{total_stocks} 只股票，共 {total_count} 条记录"
                    )
                    
                    # 保存断点
                    if i % 10 == 0:
                        await self.save_sync_position('audit_opinion_sync', str(i))
                    
                    # API频率控制：每分钟最多50次
                    time.sleep(1.2)
                    
                except Exception as e:
                    logger.error(f"同步股票 {ts_code} 失败: {e}")
                    continue
            
            # 清除断点
            await self.clear_sync_position('audit_opinion_sync')
            
            self.update_progress(total_stocks, total_stocks, f"同步完成，共 {total_count} 条记录")
            self.finish_sync(True)
            
            return {
                'success': True,
                'message': f'成功同步{total_count}条审计意见',
                'data': {
                    'direction': direction,
                    'total_stocks': total_stocks,
                    'success_stocks': success_count,
                    'total_records': total_count,
                    'sync_time': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            error_msg = f"同步失败: {str(e)}"
            logger.error(error_msg)
            self.finish_sync(False, error_msg)
            return {'success': False, 'message': error_msg}

    async def _get_all_stocks_date_ranges(self) -> Dict[str, tuple]:
        """获取所有股票的日期范围 (min_date, max_date)"""
        try:
            db = next(get_db())
            query = text("SELECT ts_code, MIN(ann_date), MAX(ann_date) FROM audit_opinions GROUP BY ts_code")
            result = db.execute(query).fetchall()
            return {row[0]: (row[1], row[2]) for row in result}
        except Exception as e:
            logger.error(f"获取股票日期范围失败: {e}")
            return {}
    
    async def _get_all_stock_codes(self):
        """获取所有股票代码"""
        try:
            db = next(get_db())
            query = text("SELECT ts_code FROM stock_basic WHERE list_status='L' ORDER BY ts_code")
            result = db.execute(query).fetchall()
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"获取股票代码失败: {e}")
            return []
    
    async def _sync_stock_audit_opinions(self, ts_code: str, start_date: str, end_date: str) -> int:
        """同步单只股票的审计意见"""
        try:
            # 调用Tushare API
            df = self.pro.fina_audit(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if df.empty:
                return 0
            
            # 处理数据：将NaN替换为None
            df = df.where(pd.notnull(df), None)
            
            # 动态构建插入SQL
            columns = df.columns.tolist()
            # 确保包含 updated_at
            if 'updated_at' not in columns:
                columns.append('updated_at')
            
            placeholders = [f":{col}" for col in columns if col != 'updated_at']
            placeholders.append('NOW()')
            
            update_clause = [f"{col}=VALUES({col})" for col in columns if col not in ['ts_code', 'ann_date', 'end_date', 'created_at']]
            
            insert_sql = text(f"""
                INSERT INTO audit_opinions ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                ON DUPLICATE KEY UPDATE
                {', '.join(update_clause)}
            """)
            
            # 批量插入
            db = next(get_db())
            data_list = df.to_dict('records')
            
            db.execute(insert_sql, data_list)
            db.commit()
            return len(data_list)
            
        except Exception as e:
            logger.error(f"同步股票 {ts_code} 审计意见失败: {e}")
            return 0
