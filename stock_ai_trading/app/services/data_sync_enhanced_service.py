"""
增强数据同步服务
提供行业分类、涨跌停、停复牌、审计意见等数据的同步功能
"""
import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import asyncio

from app.core.database import get_db
from app.services.tushare_enhanced_service import tushare_enhanced_service

logger = logging.getLogger(__name__)


class DataSyncEnhancedService:
    """增强数据同步服务"""
    
    def __init__(self):
        self.service = tushare_enhanced_service
    
    async def sync_industry_classification(self, db: Session, 
                                          src: str = 'SW2021', 
                                          level: str = 'L1') -> Dict[str, Any]:
        """
        同步行业分类数据
        
        Args:
            db: 数据库会话
            src: 分类标准 (SW2021: 申万2021版)
            level: 行业级别 (L1: 一级, L2: 二级, L3: 三级)
        """
        try:
            logger.info(f"开始同步行业分类: {src} {level}")
            
            # 步骤1: 获取所有股票代码
            stock_codes = await self._get_all_stock_codes(db)
            if not stock_codes:
                logger.warning("未获取到股票代码，尝试先同步stock_basic")
                await self._sync_stock_basic_first(db)
                stock_codes = await self._get_all_stock_codes(db)
                
            if not stock_codes:
                return {'success': False, 'message': '无法获取股票代码', 'count': 0}
            
            logger.info(f"获取到 {len(stock_codes)} 只股票")
            
            # 步骤2: 批量获取行业分类（每次20只股票）
            batch_size = 20
            total_count = 0
            import time
            
            for i in range(0, len(stock_codes), batch_size):
                batch_codes = stock_codes[i:i+batch_size]
                ts_code_str = ','.join(batch_codes)
                
                try:
                    logger.info(f"处理批次 {i//batch_size + 1}/{(len(stock_codes)-1)//batch_size + 1}: {len(batch_codes)}只股票")
                    
                    # 调用Tushare API获取行业分类
                    df = await self.service.get_industry_classification(
                        ts_code=ts_code_str,
                        src=src,
                        level=level
                    )
                    
                    if df.empty:
                        logger.warning(f"批次 {i//batch_size + 1} 无数据")
                        continue
                    
                    # 插入数据
                    for _, row in df.iterrows():
                        try:
                            ts_code = row.get('ts_code', '')
                            index_code = row.get('index_code', '')
                            index_name = row.get('index_name', '')
                            
                            if not ts_code or not index_code:
                                continue
                            
                            # 检查是否已存在
                            check_sql = text("""
                                SELECT id FROM industry_classification 
                                WHERE ts_code = :ts_code AND industry_code = :industry_code
                            """)
                            exists = db.execute(check_sql, {
                                'ts_code': ts_code,
                                'industry_code': index_code
                            }).first()
                            
                            if not exists:
                                insert_sql = text("""
                                    INSERT INTO industry_classification 
                                    (ts_code, industry_code, industry_name, level, classification_type, is_new, created_at)
                                    VALUES (:ts_code, :code, :name, :level, :type, :is_new, :created_at)
                                """)
                                db.execute(insert_sql, {
                                    'ts_code': ts_code,
                                    'code': index_code,
                                    'name': index_name if index_name else index_code,
                                    'level': int(level[1]) if level else 1,
                                    'type': src.lower(),
                                    'is_new': True,
                                    'created_at': datetime.now()
                                })
                                total_count += 1
                                
                        except Exception as e:
                            logger.error(f"插入行业分类失败: {e}, 数据: {row.to_dict()}")
                            continue
                    
                    # 每批次提交一次
                    db.commit()
                    logger.info(f"批次 {i//batch_size + 1} 完成: 新增 {len(df)} 条")
                    
                    # 延迟，避免API调用过快
                    time.sleep(0.3)
                    
                except Exception as e:
                    logger.error(f"批次 {i//batch_size + 1} 处理失败: {e}")
                    db.rollback()
                    continue
            
            logger.info(f"行业分类同步完成: 总计新增{total_count}条")
            
            return {
                'success': True,
                'message': f'同步成功',
                'count': total_count,
                'total': len(stock_codes)
            }
            
        except Exception as e:
            logger.error(f"同步行业分类失败: {e}")
            db.rollback()
            return {'success': False, 'message': str(e), 'count': 0}
    
    async def _get_all_stock_codes(self, db: Session) -> list:
        """从stock_basic表获取所有股票代码"""
        try:
            sql = text("""
                SELECT ts_code FROM stock_basic 
                WHERE list_status = 'L' 
                ORDER BY ts_code
            """)
            result = db.execute(sql).fetchall()
            return [row.ts_code for row in result]
        except Exception as e:
            logger.error(f"获取股票代码失败: {e}")
            return []
    
    async def _sync_stock_basic_first(self, db: Session):
        """先同步stock_basic表"""
        try:
            logger.info("开始同步stock_basic表")
            df = await self.service.get_stock_basic()
            
            if df.empty:
                return
            
            for _, row in df.iterrows():
                try:
                    insert_sql = text("""
                        INSERT INTO stock_basic 
                        (ts_code, symbol, name, area, industry, market, list_status, list_date)
                        VALUES (:ts_code, :symbol, :name, :area, :industry, :market, :list_status, :list_date)
                        ON DUPLICATE KEY UPDATE
                            name = VALUES(name),
                            industry = VALUES(industry),
                            market = VALUES(market)
                    """)
                    db.execute(insert_sql, {
                        'ts_code': row.get('ts_code', ''),
                        'symbol': row.get('symbol', ''),
                        'name': row.get('name', ''),
                        'area': row.get('area', ''),
                        'industry': row.get('industry', ''),
                        'market': row.get('market', ''),
                        'list_status': row.get('list_status', 'L'),
                        'list_date': row.get('list_date', '')
                    })
                except Exception as e:
                    logger.error(f"插入stock_basic失败: {e}")
                    continue
            
            db.commit()
            logger.info(f"stock_basic同步完成: {len(df)}条")
            
        except Exception as e:
            logger.error(f"同步stock_basic失败: {e}")
            db.rollback()
    
    async def sync_limit_prices(self, db: Session, 
                               trade_date: str = None,
                               start_date: str = None,
                               end_date: str = None) -> Dict[str, Any]:
        """
        同步涨跌停价格数据（支持大范围日期，按月分批处理）
        
        Args:
            db: 数据库会话
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            同步结果
        """
        try:
            # 如果没有指定日期，获取最新日期后的数据
            if not trade_date and not start_date:
                last_date_sql = text("SELECT MAX(trade_date) as last_date FROM limit_prices")
                result = db.execute(last_date_sql).first()
                
                if result and result.last_date:
                    start_date = (result.last_date + timedelta(days=1)).strftime('%Y%m%d')
                else:
                    # 如果表为空，从30天前开始
                    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
                
                end_date = datetime.now().strftime('%Y%m%d')
            
            logger.info(f"开始同步涨跌停数据: {start_date} - {end_date}")
            
            # 计算日期范围，如果超过90天，按月分批处理
            start_dt = datetime.strptime(start_date, '%Y%m%d')
            end_dt = datetime.strptime(end_date, '%Y%m%d')
            days_diff = (end_dt - start_dt).days
            
            total_count = 0
            import time
            
            if days_diff > 90:
                # 按月分批处理
                logger.info(f"日期范围较大({days_diff}天)，将按月分批处理")
                current_date = start_dt
                batch_num = 0
                
                while current_date <= end_dt:
                    batch_num += 1
                    # 计算当前批次的结束日期（当月最后一天或总结束日期）
                    next_month = current_date.replace(day=28) + timedelta(days=4)
                    batch_end = (next_month - timedelta(days=next_month.day)).replace(hour=23, minute=59, second=59)
                    if batch_end > end_dt:
                        batch_end = end_dt
                    
                    batch_start = current_date.strftime('%Y%m%d')
                    batch_end_str = batch_end.strftime('%Y%m%d')
                    
                    logger.info(f"处理批次 {batch_num}: {batch_start} - {batch_end_str}")
                    
                    # 获取当前批次数据
                    df = await self.service.get_stk_limit(
                        start_date=batch_start,
                        end_date=batch_end_str
                    )
                    
                    if not df.empty:
                        count = await self._save_limit_prices(db, df)
                        total_count += count
                        logger.info(f"批次 {batch_num} 完成: 新增/更新 {count} 条，累计 {total_count} 条")
                    else:
                        logger.info(f"批次 {batch_num} 无数据")
                    
                    # 移动到下个月
                    current_date = batch_end + timedelta(days=1)
                    time.sleep(0.5)  # 批次间延迟500ms
                    
            else:
                # 小范围日期，一次性处理
                df = await self.service.get_stk_limit(
                    start_date=start_date,
                    end_date=end_date
                )
                
                if not df.empty:
                    total_count = await self._save_limit_prices(db, df)
            
            logger.info(f"涨跌停数据同步完成: 总计新增/更新{total_count}条")
            
            return {
                'success': True,
                'message': '同步成功',
                'count': total_count,
                'total': total_count
            }
            
        except Exception as e:
            logger.error(f"同步涨跌停数据失败: {e}")
            db.rollback()
            return {'success': False, 'message': str(e), 'count': 0}
    
    async def _save_limit_prices(self, db: Session, df: pd.DataFrame) -> int:
        """保存涨跌停价格数据到数据库"""
        count = 0
        import time
        
        for _, row in df.iterrows():
            try:
                upsert_sql = text("""
                    INSERT INTO limit_prices 
                    (ts_code, trade_date, up_limit, down_limit, created_at)
                    VALUES (:ts_code, :trade_date, :up_limit, :down_limit, :created_at)
                    ON DUPLICATE KEY UPDATE
                    up_limit = VALUES(up_limit),
                    down_limit = VALUES(down_limit),
                    created_at = VALUES(created_at)
                """)
                db.execute(upsert_sql, {
                    'ts_code': row.get('ts_code', ''),
                    'trade_date': pd.to_datetime(str(row.get('trade_date', ''))).date(),
                    'up_limit': float(row.get('up_limit', 0)) if pd.notna(row.get('up_limit')) else None,
                    'down_limit': float(row.get('down_limit', 0)) if pd.notna(row.get('down_limit')) else None,
                    'created_at': datetime.now()
                })
                count += 1
                
                # 每500条提交一次并延迟
                if count % 500 == 0:
                    db.commit()
                    time.sleep(0.05)  # 延迟50ms
                    logger.info(f"已处理 {count}/{len(df)} 条数据")
                    
            except Exception as e:
                logger.error(f"插入涨跌停数据失败: {e}")
                continue
        
        db.commit()
        return count
    
    async def sync_suspend_info(self, db: Session,
                               start_date: str = None,
                               end_date: str = None) -> Dict[str, Any]:
        """
        同步停复牌信息
        
        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            同步结果
        """
        try:
            # 如果没有指定日期，获取最新日期后的数据
            if not start_date:
                last_date_sql = text("SELECT MAX(suspend_date) as last_date FROM suspend_info")
                result = db.execute(last_date_sql).first()
                
                if result and result.last_date:
                    start_date = (result.last_date + timedelta(days=1)).strftime('%Y%m%d')
                else:
                    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
                
                end_date = datetime.now().strftime('%Y%m%d')
            
            logger.info(f"开始同步停复牌数据: {start_date} - {end_date}")
            
            # 获取停牌数据
            df_suspend = await self.service.get_suspend_data(
                suspend_type='S',
                start_date=start_date,
                end_date=end_date
            )
            
            # 获取复牌数据
            df_resume = await self.service.get_suspend_data(
                suspend_type='R',
                start_date=start_date,
                end_date=end_date
            )
            
            count = 0
            
            # 处理停牌数据
            import time
            if not df_suspend.empty:
                for _, row in df_suspend.iterrows():
                    try:
                        insert_sql = text("""
                            INSERT INTO suspend_info 
                            (ts_code, suspend_date, suspend_timing, suspend_type, is_suspended, created_at)
                            VALUES (:ts_code, :suspend_date, :suspend_timing, :suspend_type, :is_suspended, :created_at)
                            ON DUPLICATE KEY UPDATE
                            suspend_timing = VALUES(suspend_timing),
                            is_suspended = VALUES(is_suspended),
                            created_at = VALUES(created_at)
                        """)
                        
                        trade_date = pd.to_datetime(str(row.get('trade_date', ''))).date()
                        
                        db.execute(insert_sql, {
                            'ts_code': row.get('ts_code', ''),
                            'suspend_date': trade_date,
                            'suspend_timing': row.get('suspend_timing', '') if pd.notna(row.get('suspend_timing')) else None,
                            'suspend_type': row.get('suspend_type', ''),
                            'is_suspended': True,
                            'created_at': datetime.now()
                        })
                        count += 1
                        time.sleep(0.05)  # 延迟50ms
                    except Exception as e:
                        logger.error(f"插入停牌数据失败: {e}, 数据: {row.to_dict()}")
                        continue
            
            # 处理复牌数据
            if not df_resume.empty:
                for _, row in df_resume.iterrows():
                    try:
                        # 更新对应的停牌记录
                        update_sql = text("""
                            UPDATE suspend_info 
                            SET resume_date = :resume_date,
                                is_suspended = FALSE
                            WHERE ts_code = :ts_code 
                            AND suspend_date <= :resume_date
                            AND (resume_date IS NULL OR resume_date > :resume_date)
                            ORDER BY suspend_date DESC
                            LIMIT 1
                        """)
                        
                        trade_date = pd.to_datetime(str(row.get('trade_date', ''))).date()
                        
                        db.execute(update_sql, {
                            'ts_code': row.get('ts_code', ''),
                            'resume_date': trade_date
                        })
                        count += 1
                        time.sleep(0.05)  # 延迟50ms
                    except Exception as e:
                        logger.error(f"更新复牌数据失败: {e}, 数据: {row.to_dict()}")
                        continue
            
            db.commit()
            logger.info(f"停复牌数据同步完成: 新增/更新{count}条")
            
            return {
                'success': True,
                'message': '同步成功',
                'count': count,
                'suspend_count': len(df_suspend),
                'resume_count': len(df_resume)
            }
            
        except Exception as e:
            logger.error(f"同步停复牌数据失败: {e}")
            db.rollback()
            return {'success': False, 'message': str(e), 'count': 0}
    
    async def sync_audit_opinions(self, db: Session,
                                  start_date: str = None,
                                  end_date: str = None) -> Dict[str, Any]:
        """
        同步审计意见数据
        
        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            同步结果
        """
        try:
            if not start_date:
                # 获取最近一年的数据
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
                end_date = datetime.now().strftime('%Y%m%d')
            
            logger.info(f"开始同步审计意见: {start_date} - {end_date}")
            
            # 获取数据
            df = await self.service.get_audit_opinion(
                start_date=start_date,
                end_date=end_date
            )
            
            if df.empty:
                return {'success': True, 'message': '无新数据', 'count': 0}
            
            count = 0
            for _, row in df.iterrows():
                try:
                    insert_sql = text("""
                        INSERT INTO audit_opinions 
                        (ts_code, ann_date, end_date, audit_result, audit_fees, 
                         audit_agency, audit_sign, opinion_type, created_at)
                        VALUES (:ts_code, :ann_date, :end_date, :audit_result, :audit_fees,
                                :audit_agency, :audit_sign, :opinion_type, :created_at)
                        ON DUPLICATE KEY UPDATE
                        audit_result = VALUES(audit_result),
                        opinion_type = VALUES(opinion_type)
                    """)
                    
                    db.execute(insert_sql, {
                        'ts_code': row.get('ts_code', ''),
                        'ann_date': pd.to_datetime(row.get('ann_date', '')).date(),
                        'end_date': pd.to_datetime(row.get('end_date', '')).date(),
                        'audit_result': row.get('audit_result', ''),
                        'audit_fees': float(row.get('audit_fees', 0)) if row.get('audit_fees') else None,
                        'audit_agency': row.get('audit_agency', ''),
                        'audit_sign': row.get('audit_sign', ''),
                        'opinion_type': row.get('opinion_type', ''),
                        'created_at': datetime.now()
                    })
                    count += 1
                except Exception as e:
                    logger.error(f"插入审计意见失败: {e}")
                    continue
            
            db.commit()
            logger.info(f"审计意见同步完成: 新增/更新{count}条")
            
            return {
                'success': True,
                'message': '同步成功',
                'count': count,
                'total': len(df)
            }
            
        except Exception as e:
            logger.error(f"同步审计意见失败: {e}")
            db.rollback()
            return {'success': False, 'message': str(e), 'count': 0}


# 全局服务实例
data_sync_enhanced_service = DataSyncEnhancedService()
