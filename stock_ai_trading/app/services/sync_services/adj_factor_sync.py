"""
复权因子同步服务
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


class AdjFactorSyncService(BaseSyncService):
    """复权因子同步服务"""
    
    async def sync(self, start_date: str = None, end_date: str = None, **kwargs) -> Dict[str, Any]:
        """
        同步复权因子数据（批量股票代码）
        
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
                last_date = await self.get_last_sync_date('adj_factor', 'trade_date')
                if last_date:
                    # 从最新日期的下一天开始
                    last_dt = datetime.strptime(last_date, '%Y%m%d')
                    start_dt = last_dt + timedelta(days=1)
                    start_date = start_dt.strftime('%Y%m%d')
                else:
                    # 默认从30天前开始
                    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            
            self.update_progress(0, 1, f"准备同步复权因子: {start_date} - {end_date}")
            
            # 获取所有股票代码
            stock_codes = await self._get_all_stock_codes()
            if not stock_codes:
                self.finish_sync(False, "未找到股票代码")
                return {'success': False, 'message': '未找到股票代码'}
            
            # 分批处理（每批10个股票）
            batch_size = 10
            total_batches = (len(stock_codes) + batch_size - 1) // batch_size
            total_count = 0
            
            self.update_progress(0, total_batches, f"开始同步 {len(stock_codes)} 只股票的复权因子")
            
            for i in range(0, len(stock_codes), batch_size):
                batch_codes = stock_codes[i:i + batch_size]
                batch_num = i // batch_size + 1
                
                try:
                    # 批量调用API
                    ts_codes_str = ','.join(batch_codes)
                    df = self.pro.adj_factor(
                        ts_code=ts_codes_str,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    if not df.empty:
                        count = await self._save_adj_factor(df)
                        total_count += count
                    
                    self.update_progress(
                        batch_num,
                        total_batches,
                        f"已同步 {batch_num}/{total_batches} 批，共 {total_count} 条记录"
                    )
                    
                    # API频率控制
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"同步第 {batch_num} 批失败: {e}")
                    continue
            
            self.update_progress(total_batches, total_batches, f"同步完成，共 {total_count} 条记录")
            self.finish_sync(True)
            
            return {
                'success': True,
                'message': f'成功同步{total_count}条复权因子',
                'data': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'total_stocks': len(stock_codes),
                    'total_batches': total_batches,
                    'total_records': total_count,
                    'sync_time': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            error_msg = f"同步失败: {str(e)}"
            logger.error(error_msg)
            self.finish_sync(False, error_msg)
            return {'success': False, 'message': error_msg}
    
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
    
    async def _save_adj_factor(self, df: pd.DataFrame) -> int:
        """保存复权因子"""
        try:
            db = next(get_db())
            count = 0
            
            for _, row in df.iterrows():
                try:
                    insert_sql = text("""
                        INSERT INTO adj_factor 
                        (ts_code, trade_date, adj_factor, updated_at)
                        VALUES (:ts_code, :trade_date, :adj_factor, NOW())
                        ON DUPLICATE KEY UPDATE
                        adj_factor = VALUES(adj_factor),
                        updated_at = NOW()
                    """)
                    
                    # 确保trade_date格式正确
                    trade_date = row.get('trade_date', '')
                    if hasattr(trade_date, 'strftime'):
                        trade_date = trade_date.strftime('%Y%m%d')
                    elif isinstance(trade_date, str) and '-' in trade_date:
                        trade_date = trade_date.replace('-', '')
                    
                    db.execute(insert_sql, {
                        'ts_code': row.get('ts_code', ''),
                        'trade_date': trade_date,
                        'adj_factor': row.get('adj_factor', None)
                    })
                    
                    count += 1
                    
                except Exception as e:
                    logger.error(f"插入复权因子失败: {e}")
                    continue
            
            db.commit()
            return count
            
        except Exception as e:
            logger.error(f"保存复权因子失败: {e}")
            return 0
