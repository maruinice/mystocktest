"""
审计意见同步服务
基于 sync_audit_opinions.py 改造
"""

import logging
import time
from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import text

from .base_sync_service import BaseSyncService
from app.core.database import get_db

logger = logging.getLogger(__name__)


class AuditOpinionSyncService(BaseSyncService):
    """审计意见同步服务"""
    
    async def sync(self, start_date: str = None, end_date: str = None, start_position: int = 1, **kwargs) -> Dict[str, Any]:
        """
        同步审计意见数据
        
        Args:
            start_date: 开始日期 (YYYYMMDD)，默认为数据库最新日期
            end_date: 结束日期 (YYYYMMDD)，默认为今天
            start_position: 起始位置（断点续传）
            
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
                # 尝试从数据库获取最新日期
                last_date = await self.get_last_sync_date('audit_opinions', 'ann_date')
                if last_date:
                    start_date = last_date
                else:
                    # 默认3年前
                    start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y%m%d')
            
            self.update_progress(0, 1, f"准备同步审计意见: {start_date} - {end_date}")
            
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
            
            self.update_progress(0, total_stocks, f"开始同步 {total_stocks} 只股票的审计意见")
            
            # 逐个股票同步
            total_count = 0
            success_count = 0
            
            for i, ts_code in enumerate(stock_codes[start_position-1:], start_position):
                try:
                    count = await self._sync_stock_audit_opinions(
                        ts_code, start_date, end_date
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
                    'start_date': start_date,
                    'end_date': end_date,
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
            
            # 保存到数据库
            db = next(get_db())
            count = 0
            
            for _, row in df.iterrows():
                try:
                    insert_sql = text("""
                        INSERT INTO audit_opinions 
                        (ts_code, ann_date, end_date, audit_result, audit_fees, audit_agency, audit_sign, updated_at)
                        VALUES (:ts_code, :ann_date, :end_date, :audit_result, :audit_fees, :audit_agency, :audit_sign, NOW())
                        ON DUPLICATE KEY UPDATE
                        audit_result = VALUES(audit_result),
                        audit_fees = VALUES(audit_fees),
                        audit_agency = VALUES(audit_agency),
                        audit_sign = VALUES(audit_sign),
                        updated_at = NOW()
                    """)
                    
                    db.execute(insert_sql, {
                        'ts_code': row['ts_code'],
                        'ann_date': row.get('ann_date', ''),
                        'end_date': row.get('end_date', ''),
                        'audit_result': row.get('audit_result', ''),
                        'audit_fees': row.get('audit_fees', None),
                        'audit_agency': row.get('audit_agency', ''),
                        'audit_sign': row.get('audit_sign', '')
                    })
                    
                    count += 1
                    
                except Exception as e:
                    logger.error(f"插入审计意见失败: {e}")
                    continue
            
            db.commit()
            return count
            
        except Exception as e:
            logger.error(f"同步股票 {ts_code} 审计意见失败: {e}")
            return 0
