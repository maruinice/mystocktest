"""
数据同步任务
使用Celery实现定时数据更新
"""
from celery import Celery
from datetime import datetime, timedelta
import logging
import asyncio
from typing import List, Dict, Any

from app.tasks.celery_app import celery_app
from app.services.tushare_service import tushare_service
from app.services.data_storage_service import data_storage_service
from app.core.database import get_db
from app.core.redis_client import redis_client
from app.utils.data_validator import DataValidator

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3)
def sync_stock_basic_data(self):
    """同步股票基础数据"""
    try:
        logger.info("开始同步股票基础数据")
        
        # 异步执行数据同步
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_sync_stock_basic_data_async())
            logger.info(f"股票基础数据同步完成: {result}")
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"股票基础数据同步失败: {str(e)}")
        # 重试机制
        if self.request.retries < self.max_retries:
            logger.info(f"第{self.request.retries + 1}次重试...")
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        raise

async def _sync_stock_basic_data_async():
    """异步同步股票基础数据"""
    # 获取上海和深圳交易所的股票数据
    exchanges = ['SSE', 'SZSE']
    total_inserted = 0
    total_duplicates = 0
    
    for exchange in exchanges:
        try:
            # 获取数据
            df = await tushare_service.get_stock_basic(exchange=exchange)
            
            if df.empty:
                logger.warning(f"交易所{exchange}没有获取到数据")
                continue
            
            # 转换为字典列表
            data_list = df.to_dict('records')
            
            # 批量插入数据库
            session = next(get_db())
            inserted, duplicates = await data_storage_service.bulk_insert_with_dedup(
                'stock_basic', data_list, session
            )
            
            total_inserted += inserted
            total_duplicates += duplicates
            
            logger.info(f"交易所{exchange}数据同步完成: 插入{inserted}条, 重复{duplicates}条")
            
        except Exception as e:
            logger.error(f"交易所{exchange}数据同步失败: {str(e)}")
            continue
    
    # 更新同步时间戳
    await tushare_service.update_data_timestamp('stock_basic', datetime.now())
    
    return {
        'total_inserted': total_inserted,
        'total_duplicates': total_duplicates,
        'sync_time': datetime.now().isoformat()
    }

@celery_app.task(bind=True, max_retries=3)
def sync_daily_quotes(self, trade_date: str = None):
    """同步日线行情数据"""
    try:
        if trade_date is None:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        logger.info(f"开始同步日线行情数据: {trade_date}")
        
        # 异步执行数据同步
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_sync_daily_quotes_async(trade_date))
            logger.info(f"日线行情数据同步完成: {result}")
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"日线行情数据同步失败: {str(e)}")
        if self.request.retries < self.max_retries:
            logger.info(f"第{self.request.retries + 1}次重试...")
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        raise

async def _sync_daily_quotes_async(trade_date: str):
    """异步同步日线行情数据"""
    try:
        # 获取指定日期的行情数据
        df = await tushare_service.get_daily_quotes(trade_date=trade_date)
        
        if df.empty:
            logger.warning(f"日期{trade_date}没有获取到行情数据")
            return {'message': f'日期{trade_date}没有行情数据'}
        
        # 转换为字典列表
        data_list = df.to_dict('records')
        
        # 批量插入数据库
        session = next(get_db())
        inserted, duplicates = await data_storage_service.bulk_insert_with_dedup(
            'stock_quotes', data_list, session
        )
        
        # 更新同步时间戳
        await tushare_service.update_data_timestamp('daily_quotes', datetime.now())
        
        return {
            'trade_date': trade_date,
            'inserted': inserted,
            'duplicates': duplicates,
            'sync_time': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"同步日期{trade_date}行情数据失败: {str(e)}")
        raise

@celery_app.task(bind=True, max_retries=3)
def sync_financial_data(self, period: str = None):
    """同步财务数据"""
    try:
        if period is None:
            # 默认同步最近一个季度的数据
            current_date = datetime.now()
            if current_date.month <= 3:
                period = f"{current_date.year - 1}1231"
            elif current_date.month <= 6:
                period = f"{current_date.year}0331"
            elif current_date.month <= 9:
                period = f"{current_date.year}0630"
            else:
                period = f"{current_date.year}0930"
        
        logger.info(f"开始同步财务数据: {period}")
        
        # 异步执行数据同步
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_sync_financial_data_async(period))
            logger.info(f"财务数据同步完成: {result}")
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"财务数据同步失败: {str(e)}")
        if self.request.retries < self.max_retries:
            logger.info(f"第{self.request.retries + 1}次重试...")
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        raise

async def _sync_financial_data_async(period: str):
    """异步同步财务数据"""
    total_inserted = 0
    total_duplicates = 0
    
    try:
        # 获取利润表数据
        income_df = await tushare_service.get_income_statement(period=period)
        
        if not income_df.empty:
            data_list = income_df.to_dict('records')
            session = next(get_db())
            inserted, duplicates = await data_storage_service.bulk_insert_with_dedup(
                'financial_data', data_list, session
            )
            total_inserted += inserted
            total_duplicates += duplicates
            logger.info(f"利润表数据同步: 插入{inserted}条, 重复{duplicates}条")
        
        # 可以继续添加资产负债表和现金流量表的同步
        # balance_df = await tushare_service.get_balance_sheet(period=period)
        # cashflow_df = await tushare_service.get_cash_flow(period=period)
        
        # 更新同步时间戳
        await tushare_service.update_data_timestamp('financial_data', datetime.now())
        
        return {
            'period': period,
            'total_inserted': total_inserted,
            'total_duplicates': total_duplicates,
            'sync_time': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"同步财务数据失败: {str(e)}")
        raise

@celery_app.task(bind=True, max_retries=3)
def sync_incremental_data(self):
    """增量数据同步"""
    try:
        logger.info("开始增量数据同步")
        
        # 异步执行数据同步
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_sync_incremental_data_async())
            logger.info(f"增量数据同步完成: {result}")
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"增量数据同步失败: {str(e)}")
        if self.request.retries < self.max_retries:
            logger.info(f"第{self.request.retries + 1}次重试...")
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        raise

async def _sync_incremental_data_async():
    """异步增量数据同步"""
    results = {}
    
    # 定义需要增量同步的数据类型
    data_types = ['daily_quotes', 'financial_data']
    
    for data_type in data_types:
        try:
            # 获取最后更新时间
            last_update = await tushare_service.get_last_update_time(data_type)
            
            if last_update is None:
                # 如果没有更新记录，跳过增量同步
                logger.info(f"数据类型{data_type}没有更新记录，跳过增量同步")
                continue
            
            # 检查是否需要更新（距离上次更新超过1小时）
            if datetime.now() - last_update < timedelta(hours=1):
                logger.info(f"数据类型{data_type}更新时间较近，跳过增量同步")
                continue
            
            # 获取增量数据
            df = await tushare_service.get_incremental_data(data_type, last_update)
            
            if df.empty:
                logger.info(f"数据类型{data_type}没有增量数据")
                results[data_type] = {'message': '没有增量数据'}
                continue
            
            # 转换为字典列表
            data_list = df.to_dict('records')
            
            # 批量插入数据库
            table_name = 'stock_quotes' if data_type == 'daily_quotes' else data_type
            session = next(get_db())
            inserted, duplicates = await data_storage_service.bulk_insert_with_dedup(
                table_name, data_list, session
            )
            
            # 更新同步时间戳
            await tushare_service.update_data_timestamp(data_type, datetime.now())
            
            results[data_type] = {
                'inserted': inserted,
                'duplicates': duplicates,
                'last_update': last_update.isoformat(),
                'sync_time': datetime.now().isoformat()
            }
            
            logger.info(f"数据类型{data_type}增量同步完成: 插入{inserted}条, 重复{duplicates}条")
            
        except Exception as e:
            logger.error(f"数据类型{data_type}增量同步失败: {str(e)}")
            results[data_type] = {'error': str(e)}
            continue
    
    return results

@celery_app.task
def cleanup_old_data():
    """清理历史数据"""
    try:
        logger.info("开始清理历史数据")
        
        # 异步执行数据清理
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_cleanup_old_data_async())
            logger.info(f"历史数据清理完成: {result}")
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"历史数据清理失败: {str(e)}")
        raise

async def _cleanup_old_data_async():
    """异步清理历史数据"""
    results = {}
    
    # 需要清理的表
    tables_to_cleanup = ['stock_quotes', 'financial_data', 'trade_records', 'llm_decisions']
    
    for table_name in tables_to_cleanup:
        try:
            # 执行数据归档
            archived_count = await data_storage_service.archive_old_data(table_name)
            
            # 优化表性能
            await data_storage_service.optimize_table_performance(table_name)
            
            results[table_name] = {
                'archived_count': archived_count,
                'cleanup_time': datetime.now().isoformat()
            }
            
            logger.info(f"表{table_name}清理完成: 归档{archived_count}条记录")
            
        except Exception as e:
            logger.error(f"表{table_name}清理失败: {str(e)}")
            results[table_name] = {'error': str(e)}
            continue
    
    return results

@celery_app.task
def generate_data_quality_report():
    """生成数据质量报告"""
    try:
        logger.info("开始生成数据质量报告")
        
        # 异步执行报告生成
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_generate_data_quality_report_async())
            logger.info(f"数据质量报告生成完成")
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"数据质量报告生成失败: {str(e)}")
        raise

async def _generate_data_quality_report_async():
    """异步生成数据质量报告"""
    report = {
        'report_time': datetime.now().isoformat(),
        'tables': {}
    }
    
    # 需要检查的表
    tables_to_check = ['stock_basic', 'stock_quotes', 'financial_data', 'trade_records']
    
    for table_name in tables_to_check:
        try:
            # 获取表统计信息
            stats = await data_storage_service.get_table_statistics(table_name)
            
            # 获取重复记录信息
            duplicates = await data_storage_service.get_duplicate_records(table_name)
            
            report['tables'][table_name] = {
                'statistics': stats,
                'duplicate_count': len(duplicates),
                'duplicates': duplicates.to_dict('records') if not duplicates.empty else []
            }
            
        except Exception as e:
            logger.error(f"表{table_name}质量检查失败: {str(e)}")
            report['tables'][table_name] = {'error': str(e)}
            continue
    
    # 将报告缓存到Redis
    redis_client.set_json('data_quality_report', report, expire=3600 * 24)  # 缓存24小时
    
    return report

# 定时任务配置
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """配置定时任务"""
    
    # 每天早上8点同步股票基础数据
    sender.add_periodic_task(
        crontab(hour=8, minute=0),
        sync_stock_basic_data.s(),
        name='每日同步股票基础数据'
    )
    
    # 每个交易日下午3点半同步当日行情数据
    sender.add_periodic_task(
        crontab(hour=15, minute=30, day_of_week='1-5'),
        sync_daily_quotes.s(),
        name='每日同步行情数据'
    )
    
    # 每小时执行增量数据同步
    sender.add_periodic_task(
        crontab(minute=0),
        sync_incremental_data.s(),
        name='每小时增量数据同步'
    )
    
    # 每周日凌晨2点清理历史数据
    sender.add_periodic_task(
        crontab(hour=2, minute=0, day_of_week=0),
        cleanup_old_data.s(),
        name='每周清理历史数据'
    )
    
    # 每天凌晨1点生成数据质量报告
    sender.add_periodic_task(
        crontab(hour=1, minute=0),
        generate_data_quality_report.s(),
        name='每日数据质量报告'
    )