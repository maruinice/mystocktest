"""
行业分类同步服务
基于 sync_industry_classification.py 改造
"""

import logging
import time
from typing import Dict, Any
from datetime import datetime
from sqlalchemy import text
import pandas as pd

from .base_sync_service import BaseSyncService
from app.core.database import get_db

logger = logging.getLogger(__name__)


class IndustryClassificationSyncService(BaseSyncService):
    """行业分类同步服务"""
    
    async def sync(self, **kwargs) -> Dict[str, Any]:
        """
        同步申万行业分类数据
        
        Returns:
            同步结果
        """
        try:
            self.start_sync()
            
            if not self.pro:
                raise ValueError("Tushare API未初始化")
            
            levels = ['L1', 'L2', 'L3']
            level_names = {'L1': '一级行业', 'L2': '二级行业', 'L3': '三级行业'}
            
            self.update_progress(0, 3, "开始同步申万行业分类（SW2021）")
            
            total_count = 0
            
            for idx, level in enumerate(levels, 1):
                try:
                    self.update_progress(idx-1, 3, f"正在同步{level_names[level]}...")
                    
                    # 获取行业列表
                    industry_list = self.pro.index_classify(level=level, src='SW2021')
                    
                    if industry_list.empty:
                        continue
                    
                    logger.info(f"获取到 {len(industry_list)} 个{level_names[level]}")
                    
                    # 获取每个行业的成分股
                    all_stocks = []
                    for _, industry in industry_list.iterrows():
                        index_code = industry['index_code']
                        industry_name = industry['industry_name']
                        industry_code = industry['industry_code']
                        
                        try:
                            members = self.pro.index_member(index_code=index_code)
                            
                            if not members.empty:
                                members['industry_code'] = industry_code
                                members['industry_name'] = industry_name
                                members['level'] = level
                                all_stocks.append(members)
                            
                            time.sleep(0.3)
                            
                        except Exception as e:
                            logger.error(f"获取{industry_name}成分股失败: {e}")
                            continue
                    
                    if all_stocks:
                        df = pd.concat(all_stocks, ignore_index=True)
                        count = await self._batch_insert_industries(df, level)
                        total_count += count
                        logger.info(f"{level_names[level]}同步完成: {count}条")
                    
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"同步{level_names[level]}失败: {e}")
                    continue
            
            self.update_progress(3, 3, f"同步完成，共{total_count}条记录")
            self.finish_sync(True)
            
            return {
                'success': True,
                'message': f'成功同步{total_count}条行业分类',
                'data': {
                    'total_records': total_count,
                    'sync_time': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            error_msg = f"同步失败: {str(e)}"
            logger.error(error_msg)
            self.finish_sync(False, error_msg)
            return {'success': False, 'message': error_msg}
    
    async def _batch_insert_industries(self, df: pd.DataFrame, level: str) -> int:
        """批量插入行业分类数据"""
        try:
            count = 0
            level_map = {'L1': 1, 'L2': 2, 'L3': 3}
            level_num = level_map.get(level, 1)
            
            db = next(get_db())
            
            for _, row in df.iterrows():
                try:
                    ts_code = row.get('con_code', '')
                    industry_code = row.get('industry_code', '')
                    industry_name = row.get('industry_name', '')
                    
                    if not ts_code or not industry_code:
                        continue
                    
                    insert_sql = text("""
                        INSERT INTO industry_classification
                        (ts_code, industry_code, industry_name, level, classification_type, created_at, updated_at)
                        VALUES (:ts_code, :industry_code, :industry_name, :level, :classification_type, NOW(), NOW())
                        ON DUPLICATE KEY UPDATE
                        industry_name = VALUES(industry_name),
                        updated_at = NOW()
                    """)
                    
                    db.execute(insert_sql, {
                        'ts_code': ts_code,
                        'industry_code': industry_code,
                        'industry_name': industry_name,
                        'level': level_num,
                        'classification_type': 'SW2021'
                    })
                    
                    count += 1
                    
                except Exception as e:
                    logger.error(f"插入行业分类失败: {e}")
                    continue
            
            db.commit()
            return count
            
        except Exception as e:
            logger.error(f"批量插入失败: {e}")
            return 0
