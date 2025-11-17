"""
股票基础信息同步服务
"""

import logging
from typing import Dict, Any
from datetime import datetime
from sqlalchemy import text
import pandas as pd

from .base_sync_service import BaseSyncService
from app.core.database import get_db

logger = logging.getLogger(__name__)


class StockBasicSyncService(BaseSyncService):
    """股票基础信息同步服务"""
    
    async def sync(self, **kwargs) -> Dict[str, Any]:
        """
        同步股票基础信息
        
        Returns:
            同步结果
        """
        try:
            self.start_sync()
            self.update_progress(0, 1, "开始同步股票基础信息...")
            
            if not self.pro:
                raise ValueError("Tushare API未初始化")
            
            # 获取所有上市股票
            logger.info("从Tushare获取股票基础信息...")
            df = self.pro.stock_basic(
                exchange='',
                list_status='L',
                fields='ts_code,symbol,name,area,industry,fullname,market,exchange,list_date,is_hs'
            )
            
            if df.empty:
                self.finish_sync(False, "未获取到数据")
                return {'success': False, 'message': '未获取到数据'}
            
            total = len(df)
            self.update_progress(0, total, f"获取到{total}条股票信息，开始保存...")
            
            # 保存到数据库
            db = next(get_db())
            saved_count = 0
            
            for idx, row in df.iterrows():
                try:
                    insert_sql = text("""
                        INSERT INTO stock_basic 
                        (ts_code, symbol, name, area, industry, fullname, market, exchange, list_date, is_hs, updated_at)
                        VALUES (:ts_code, :symbol, :name, :area, :industry, :fullname, :market, :exchange, :list_date, :is_hs, NOW())
                        ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        area = VALUES(area),
                        industry = VALUES(industry),
                        fullname = VALUES(fullname),
                        market = VALUES(market),
                        exchange = VALUES(exchange),
                        list_date = VALUES(list_date),
                        is_hs = VALUES(is_hs),
                        updated_at = NOW()
                    """)
                    
                    db.execute(insert_sql, {
                        'ts_code': row['ts_code'],
                        'symbol': row['symbol'],
                        'name': row['name'],
                        'area': row.get('area', ''),
                        'industry': row.get('industry', ''),
                        'fullname': row.get('fullname', ''),
                        'market': row.get('market', ''),
                        'exchange': row.get('exchange', ''),
                        'list_date': row.get('list_date', ''),
                        'is_hs': row.get('is_hs', '')
                    })
                    
                    saved_count += 1
                    
                    # 每100条提交一次
                    if saved_count % 100 == 0:
                        db.commit()
                        self.update_progress(saved_count, total, f"已保存{saved_count}/{total}条")
                    
                except Exception as e:
                    logger.error(f"保存股票{row['ts_code']}失败: {e}")
                    continue
            
            # 最后提交
            db.commit()
            
            self.update_progress(saved_count, total, f"同步完成，共{saved_count}条")
            self.finish_sync(True)
            
            return {
                'success': True,
                'message': f'成功同步{saved_count}条股票基础信息',
                'data': {
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
