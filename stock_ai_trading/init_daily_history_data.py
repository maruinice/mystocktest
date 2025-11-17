#!/usr/bin/env python3
"""
初始化三年历史数据
直接调用Tushare API同步数据并写入数据库
支持股票基础信息、日线行情、每日指标、复权因子等数据同步
"""

import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.tushare_daily_service import tushare_daily_service
from app.services.strategy_database_service import strategy_db_service
from app.config.settings import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tushare_sync.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

async def init_three_years_data() -> bool:
    """
    初始化三年历史数据
    使用分批次同步逻辑，从stock_basic表获取股票代码
    
    Returns:
        bool: 同步是否成功
    """
    print("🚀 初始化三年历史数据...")
    print("=" * 60)
    print(f"⏰ 开始时间: {datetime.now()}")
    
    # 计算三年日期范围
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=3*365)).strftime('%Y%m%d')
    
    print(f"📅 数据范围: {start_date} - {end_date} (三年)")
    
    # 检查Tushare配置
    if not settings.TUSHARE_TOKEN:
        print("⚠️  未配置TUSHARE_TOKEN，将使用模拟数据")
    else:
        print("✅ 已配置TUSHARE_TOKEN，将使用真实数据")
    
    try:
        # 1. 首先同步股票基础信息
        print("\n📊 第一步: 同步股票基础信息...")
        basic_result = await tushare_daily_service.sync_stock_basic()
        if basic_result.get('success'):
            saved_count = basic_result.get('data', {}).get('saved_count', 0)
            print(f"✅ 股票基础信息同步成功: {saved_count}条记录")
        else:
            print(f"❌ 股票基础信息同步失败: {basic_result.get('message', '未知错误')}")
        
        # 2. 从数据库获取股票代码
        print("\n📋 第二步: 从数据库获取股票代码...")
        ts_codes = await get_stock_codes_from_db()
        print(f"✅ 获取到 {len(ts_codes)} 个股票代码")
        
        # 显示前10个股票代码作为示例
        if ts_codes:
            print(f"   示例代码: {', '.join(ts_codes[:10])}")
            if len(ts_codes) > 10:
                print(f"   ... 还有 {len(ts_codes) - 10} 个股票代码")
        
        # 3. 同步交易日历
        print("\n📅 第三步: 同步交易日历...")
        cal_result = await tushare_daily_service.sync_trade_calendar(start_date, end_date)
        if cal_result.get('success'):
            saved_count = cal_result.get('data', {}).get('saved_count', 0)
            print(f"✅ 交易日历同步成功: {saved_count}条记录")
        
        # 4. 分批次同步日线行情数据
        print(f"\n📈 第四步: 分批次同步日线行情数据...")
        daily_result = await sync_daily_data_batch(
            ts_codes=ts_codes,
            start_date=start_date,
            end_date=end_date,
            batch_size=10  # 每批10个股票代码
        )
        
        # 5. 分批次同步每日指标
        print(f"\n📊 第五步: 分批次同步每日指标...")
        basic_daily_result = await sync_daily_basic_batch(
            ts_codes=ts_codes,
            start_date=start_date,
            end_date=end_date,
            batch_size=10
        )
        
        # 6. 分批次同步复权因子
        print(f"\n🔄 第六步: 分批次同步复权因子...")
        adj_result = await sync_adj_factor_batch(
            ts_codes=ts_codes,
            start_date=start_date,
            end_date=end_date,
            batch_size=10
        )
        
        # 汇总结果
        total_records = 0
        if basic_result.get('success'):
            total_records += basic_result.get('data', {}).get('saved_count', 0)
        if cal_result.get('success'):
            total_records += cal_result.get('data', {}).get('saved_count', 0)
        if daily_result.get('success'):
            total_records += daily_result.get('data', {}).get('saved_count', 0)
        if basic_daily_result.get('success'):
            total_records += basic_daily_result.get('data', {}).get('saved_count', 0)
        if adj_result.get('success'):
            total_records += adj_result.get('data', {}).get('saved_count', 0)
        
        print(f"\n✅ 三年历史数据同步完成，总计{total_records}条记录")
        print(f"📊 同步统计:")
        print(f"   日期范围: {start_date} - {end_date}")
        print(f"   股票数量: {len(ts_codes)}")
        print(f"   总记录数: {total_records}")
        print(f"   使用模拟数据: {not bool(settings.TUSHARE_TOKEN)}")
        
        # 显示详细结果
        results = {
            'stock_basic': basic_result,
            'trade_calendar': cal_result,
            'daily_data': daily_result,
            'daily_basic': basic_daily_result,
            'adj_factor': adj_result
        }
        
        for key, result in results.items():
            if result.get('success'):
                saved_count = result.get('data', {}).get('saved_count', 0)
                print(f"   {key}: {saved_count}条记录")
        
        return True
        
    except Exception as e:
        logger.error(f"数据同步异常: {e}")
        print(f"❌ 数据同步异常: {e}")
        return False

async def test_data_quality():
    """测试数据质量"""
    print("\n📊 数据质量检查...")
    print("=" * 60)
    
    # 检查各表的数据量
    tables_to_check = [
        ('stock_basic', '股票基础信息'),
        ('daily_history', '日线行情'),
        ('daily_basic', '每日指标'),
        ('adj_factor', '复权因子'),
        ('trade_cal', '交易日历')
    ]
    
    try:
        for table, desc in tables_to_check:
            try:
                # 直接查询数据库
                with strategy_db_service.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    result = cursor.fetchone()
                    
                    if result:
                        count = result.get('count', 0)
                        print(f"📋 {desc} ({table}): {count:,}条记录")
                    else:
                        print(f"📋 {desc} ({table}): 0条记录")
                        
            except Exception as e:
                logger.error(f"检查表 {table} 失败: {e}")
                print(f"📋 {desc} ({table}): 检查失败 - {e}")
                
    except Exception as e:
        logger.error(f"数据质量检查失败: {e}")
        print(f"❌ 数据质量检查失败: {e}")

async def get_stock_codes_from_db() -> List[str]:
    """
    从stock_basic表获取所有股票代码
    
    Returns:
        List[str]: 股票代码列表 (ts_code格式)
    """
    try:
        with strategy_db_service.get_connection() as conn:
            cursor = conn.cursor()
            # 获取所有正常上市的股票代码
            cursor.execute("""
                SELECT ts_code 
                FROM stock_basic 
                WHERE list_status = 'L' 
                  AND sync_status = 'active'
                  AND ts_code IS NOT NULL
                ORDER BY ts_code
            """)
            results = cursor.fetchall()
            
            if results:
                ts_codes = [row['ts_code'] for row in results]
                logger.info(f"从数据库获取到 {len(ts_codes)} 个股票代码")
                return ts_codes
            else:
                logger.warning("数据库中没有找到股票代码，将使用默认列表")
                # 返回一些默认的股票代码用于测试
                return [
                    '000001.SZ', '000002.SZ', '000858.SZ', '002415.SZ', '300059.SZ',
                    '600000.SH', '600036.SH', '600519.SH', '600887.SH', '601318.SH'
                ]
                
    except Exception as e:
        logger.error(f"从数据库获取股票代码失败: {e}")
        print(f"❌ 从数据库获取股票代码失败: {e}")
        # 返回默认股票代码
        return [
            '000001.SZ', '000002.SZ', '000858.SZ', '002415.SZ', '300059.SZ',
            '600000.SH', '600036.SH', '600519.SH', '600887.SH', '601318.SH'
        ]

async def sync_daily_data_batch(ts_codes: List[str], start_date: str, end_date: str, batch_size: int = 10) -> Dict:
    """
    分批次同步日线行情数据
    
    Args:
        ts_codes: 股票代码列表
        start_date: 开始日期 (YYYYMMDD格式)
        end_date: 结束日期 (YYYYMMDD格式)
        batch_size: 每批次处理的股票数量，默认10个
    
    Returns:
        Dict: 同步结果统计
    """
    total_stocks = len(ts_codes)
    total_saved = 0
    success_batches = 0
    failed_batches = 0
    
    print(f"📈 开始分批次同步日线数据: 总计 {total_stocks} 只股票，每批 {batch_size} 只")
    
    # 分批处理
    for i in range(0, total_stocks, batch_size):
        batch_codes = ts_codes[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total_stocks + batch_size - 1) // batch_size
        
        print(f"   📊 处理第 {batch_num}/{total_batches} 批: {len(batch_codes)} 只股票")
        print(f"      股票代码: {', '.join(batch_codes)}")
        
        try:
            # 调用tushare服务同步这批股票的数据
            result = await tushare_daily_service.sync_daily_data(
                ts_codes=batch_codes,
                start_date=start_date,
                end_date=end_date
            )
            
            if result.get('success'):
                saved_count = result.get('data', {}).get('saved_count', 0)
                total_saved += saved_count
                success_batches += 1
                print(f"      ✅ 第 {batch_num} 批同步成功: {saved_count} 条记录")
            else:
                failed_batches += 1
                error_msg = result.get('message', '未知错误')
                print(f"      ❌ 第 {batch_num} 批同步失败: {error_msg}")
                
        except Exception as e:
            failed_batches += 1
            logger.error(f"第 {batch_num} 批同步异常: {e}")
            print(f"      ❌ 第 {batch_num} 批同步异常: {e}")
        
        # 批次间延迟，避免API调用过于频繁
        if i + batch_size < total_stocks:  # 不是最后一批
            await asyncio.sleep(1)  # 延迟1秒
    
    print(f"📊 分批次同步完成:")
    print(f"   总批次: {total_batches}")
    print(f"   成功批次: {success_batches}")
    print(f"   失败批次: {failed_batches}")
    print(f"   总记录数: {total_saved}")
    
    return {
        'success': success_batches > 0,
        'message': f'分批次同步完成: {success_batches}/{total_batches} 批成功',
        'data': {
            'total_stocks': total_stocks,
            'total_batches': total_batches,
            'success_batches': success_batches,
            'failed_batches': failed_batches,
            'saved_count': total_saved,
            'batch_size': batch_size
        }
    }

async def sync_daily_basic_batch(ts_codes: List[str], start_date: str, end_date: str, batch_size: int = 10) -> Dict:
    """
    分批次同步每日指标数据
    
    Args:
        ts_codes: 股票代码列表
        start_date: 开始日期 (YYYYMMDD格式)
        end_date: 结束日期 (YYYYMMDD格式)
        batch_size: 每批次处理的股票数量，默认10个
    
    Returns:
        Dict: 同步结果统计
    """
    total_stocks = len(ts_codes)
    total_saved = 0
    success_batches = 0
    failed_batches = 0
    
    print(f"📊 开始分批次同步每日指标: 总计 {total_stocks} 只股票，每批 {batch_size} 只")
    
    # 分批处理
    for i in range(0, total_stocks, batch_size):
        batch_codes = ts_codes[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total_stocks + batch_size - 1) // batch_size
        
        print(f"   📊 处理第 {batch_num}/{total_batches} 批: {len(batch_codes)} 只股票")
        
        try:
            # 调用tushare服务同步这批股票的数据
            result = await tushare_daily_service.sync_daily_basic(
                start_date=start_date,
                end_date=end_date,
                ts_codes=batch_codes
            )
            
            if result.get('success'):
                saved_count = result.get('data', {}).get('saved_count', 0)
                total_saved += saved_count
                success_batches += 1
                print(f"      ✅ 第 {batch_num} 批同步成功: {saved_count} 条记录")
            else:
                failed_batches += 1
                error_msg = result.get('message', '未知错误')
                print(f"      ❌ 第 {batch_num} 批同步失败: {error_msg}")
                
        except Exception as e:
            failed_batches += 1
            logger.error(f"第 {batch_num} 批每日指标同步异常: {e}")
            print(f"      ❌ 第 {batch_num} 批同步异常: {e}")
        
        # 批次间延迟
        if i + batch_size < total_stocks:
            await asyncio.sleep(1)
    
    print(f"📊 每日指标分批次同步完成: {success_batches}/{(total_stocks + batch_size - 1) // batch_size} 批成功，总计 {total_saved} 条记录")
    
    return {
        'success': success_batches > 0,
        'message': f'每日指标分批次同步完成: {success_batches} 批成功',
        'data': {
            'saved_count': total_saved,
            'success_batches': success_batches,
            'failed_batches': failed_batches
        }
    }

async def sync_adj_factor_batch(ts_codes: List[str], start_date: str, end_date: str, batch_size: int = 10) -> Dict:
    """
    分批次同步复权因子数据
    
    Args:
        ts_codes: 股票代码列表
        start_date: 开始日期 (YYYYMMDD格式)
        end_date: 结束日期 (YYYYMMDD格式)
        batch_size: 每批次处理的股票数量，默认10个
    
    Returns:
        Dict: 同步结果统计
    """
    total_stocks = len(ts_codes)
    total_saved = 0
    success_batches = 0
    failed_batches = 0
    
    print(f"🔄 开始分批次同步复权因子: 总计 {total_stocks} 只股票，每批 {batch_size} 只")
    
    # 分批处理
    for i in range(0, total_stocks, batch_size):
        batch_codes = ts_codes[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total_stocks + batch_size - 1) // batch_size
        
        print(f"   🔄 处理第 {batch_num}/{total_batches} 批: {len(batch_codes)} 只股票")
        
        try:
            # 调用tushare服务同步这批股票的数据
            result = await tushare_daily_service.sync_adj_factor(
                start_date=start_date,
                end_date=end_date,
                ts_codes=batch_codes
            )
            
            if result.get('success'):
                saved_count = result.get('data', {}).get('saved_count', 0)
                total_saved += saved_count
                success_batches += 1
                print(f"      ✅ 第 {batch_num} 批同步成功: {saved_count} 条记录")
            else:
                failed_batches += 1
                error_msg = result.get('message', '未知错误')
                print(f"      ❌ 第 {batch_num} 批同步失败: {error_msg}")
                
        except Exception as e:
            failed_batches += 1
            logger.error(f"第 {batch_num} 批复权因子同步异常: {e}")
            print(f"      ❌ 第 {batch_num} 批同步异常: {e}")
        
        # 批次间延迟
        if i + batch_size < total_stocks:
            await asyncio.sleep(1)
    
    print(f"🔄 复权因子分批次同步完成: {success_batches}/{(total_stocks + batch_size - 1) // batch_size} 批成功，总计 {total_saved} 条记录")
    
    return {
        'success': success_batches > 0,
        'message': f'复权因子分批次同步完成: {success_batches} 批成功',
        'data': {
            'saved_count': total_saved,
            'success_batches': success_batches,
            'failed_batches': failed_batches
        }
    }

async def sync_specific_data(data_type: str, **kwargs):
    """
    同步特定类型的数据
    
    Args:
        data_type: 数据类型 (stock_basic, daily_history, daily_basic, adj_factor, trade_cal)
        **kwargs: 其他参数
    """
    print(f"\n🔄 同步 {data_type} 数据...")
    
    try:
        if data_type == 'stock_basic':
            result = await tushare_daily_service.sync_stock_basic()
        elif data_type == 'trade_cal':
            start_date = kwargs.get('start_date', (datetime.now() - timedelta(days=365)).strftime('%Y%m%d'))
            end_date = kwargs.get('end_date', datetime.now().strftime('%Y%m%d'))
            result = await tushare_daily_service.sync_trade_calendar(start_date, end_date)
        elif data_type == 'daily_history':
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            ts_codes = kwargs.get('ts_codes')
            result = await tushare_daily_service.sync_daily_data(
                start_date=start_date, 
                end_date=end_date, 
                ts_codes=ts_codes
            )
        elif data_type == 'daily_basic':
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            ts_codes = kwargs.get('ts_codes')
            result = await tushare_daily_service.sync_daily_basic(
                start_date=start_date,
                end_date=end_date,
                ts_codes=ts_codes
            )
        elif data_type == 'adj_factor':
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            ts_codes = kwargs.get('ts_codes')
            result = await tushare_daily_service.sync_adj_factor(
                start_date=start_date,
                end_date=end_date,
                ts_codes=ts_codes
            )
        else:
            print(f"❌ 不支持的数据类型: {data_type}")
            return False
        
        if result.get('success'):
            saved_count = result.get('data', {}).get('saved_count', 0)
            print(f"✅ {data_type} 同步成功: {saved_count}条记录")
            return True
        else:
            print(f"❌ {data_type} 同步失败: {result.get('message', '未知错误')}")
            return False
            
    except Exception as e:
        logger.error(f"{data_type} 同步异常: {e}")
        print(f"❌ {data_type} 同步异常: {e}")
        return False

async def main():
    """主函数"""
    print("🎯 Tushare数据同步工具")
    print("=" * 60)
    
    # 检查数据库连接
    print("🔍 检查数据库连接...")
    try:
        # 测试数据库连接
        with strategy_db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            if result:
                print("   ✅ 数据库连接正常")
            else:
                print("   ❌ 数据库连接失败")
                return
    except Exception as e:
        print(f"   ❌ 数据库连接异常: {e}")
        print("   💡 请检查数据库配置和服务状态")
        return
    
    # 显示配置信息
    print(f"\n📋 配置信息:")
    print(f"   数据库URL: {settings.DATABASE_URL}")
    print(f"   Tushare Token: {'已配置' if settings.TUSHARE_TOKEN else '未配置'}")
    
    # 执行数据同步
    success = await init_three_years_data()
    
    # 检查数据质量
    await test_data_quality()
    
    print(f"\n⏰ 完成时间: {datetime.now()}")
    
    if success:
        print("🎉 三年历史数据同步成功！")
        print("💡 数据已保存到数据库，可以开始使用选股功能")
    else:
        print("⚠️  数据同步完成，但可能存在问题")
        print("💡 请检查日志文件 tushare_sync.log 获取详细信息")

if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())