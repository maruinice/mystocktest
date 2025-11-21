#!/usr/bin/env python3
"""
创建一个完全工作的选股功能
基于实际数据表结构
"""

import asyncio
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.strategy_database_service import strategy_db_service

async def create_working_screening():
    """创建工作的选股功能"""
    print("🎯 创建工作的选股功能")
    print("=" * 60)
    
    try:
        with strategy_db_service.get_connection() as conn:
            one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            
            # 第一步：获取股票基础信息
            print("📊 第一步：获取股票基础信息...")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ts_code, symbol, name, industry, market, exchange, area
                FROM stock_basic 
                WHERE list_status = 'L' AND sync_status = 'active'
                ORDER BY ts_code
                LIMIT 100
            """)
            stocks = cursor.fetchall()
            print(f"   获取到 {len(stocks)} 只股票")
            
            # 第二步：为每只股票获取最新数据
            print("📊 第二步：获取最新行情和基本面数据...")
            screening_data = []
            
            for i, stock in enumerate(stocks):
                ts_code = stock['ts_code']
                
                # 获取最新日线数据
                cursor.execute(f"""
                    SELECT close_price, change_pct, volume, amount, turnover_rate, volume_ratio,
                           pe, pb, ps, pcf, market_cap, circ_mv, trade_date
                    FROM daily_history 
                    WHERE ts_code = '{ts_code}' 
                    AND trade_date >= '{one_year_ago}'
                    ORDER BY trade_date DESC 
                    LIMIT 1
                """)
                dh_data = cursor.fetchone()
                
                # 获取最新基本面数据
                cursor.execute(f"""
                    SELECT pe, pb, ps, pe_ttm, ps_ttm, total_mv, circ_mv, 
                           turnover_rate, volume_ratio, trade_date
                    FROM daily_basic 
                    WHERE ts_code = '{ts_code}' 
                    AND trade_date >= '{one_year_ago}'
                    ORDER BY trade_date DESC 
                    LIMIT 1
                """)
                db_data = cursor.fetchone()
                
                # 合并数据
                if dh_data and db_data:
                    stock_data = {
                        'ts_code': ts_code,
                        'symbol': stock['symbol'],
                        'name': stock['name'],
                        'industry': stock['industry'],
                        'market': stock['market'],
                        'exchange': stock['exchange'],
                        'area': stock['area'],
                        
                        # 行情数据
                        'close_price': float(dh_data['close_price']) if dh_data['close_price'] else None,
                        'change_pct': float(dh_data['change_pct']) if dh_data['change_pct'] else None,
                        'volume': float(dh_data['volume']) if dh_data['volume'] else None,
                        'amount': float(dh_data['amount']) if dh_data['amount'] else None,
                        'turnover_rate': float(dh_data['turnover_rate']) if dh_data['turnover_rate'] else None,
                        'volume_ratio': float(dh_data['volume_ratio']) if dh_data['volume_ratio'] else None,
                        
                        # 估值数据 - 优先使用daily_basic
                        'pe': float(db_data['pe']) if db_data['pe'] else (float(dh_data['pe']) if dh_data['pe'] else None),
                        'pb': float(db_data['pb']) if db_data['pb'] else (float(dh_data['pb']) if dh_data['pb'] else None),
                        'ps': float(db_data['ps']) if db_data['ps'] else (float(dh_data['ps']) if dh_data['ps'] else None),
                        'pe_ttm': float(db_data['pe_ttm']) if db_data['pe_ttm'] else None,
                        'ps_ttm': float(db_data['ps_ttm']) if db_data['ps_ttm'] else None,
                        
                        # 市值数据
                        'market_cap': float(db_data['total_mv']) if db_data['total_mv'] else (float(dh_data['market_cap']) if dh_data['market_cap'] else None),
                        'circ_mv': float(db_data['circ_mv']) if db_data['circ_mv'] else (float(dh_data['circ_mv']) if dh_data['circ_mv'] else None),
                    }
                    
                    screening_data.append(stock_data)
                
                if (i + 1) % 20 == 0:
                    print(f"   处理进度: {i + 1}/{len(stocks)}")
            
            print(f"✅ 获取到 {len(screening_data)} 条完整数据")
            
            # 第三步：数据质量检查
            print("📊 第三步：数据质量检查...")
            df = pd.DataFrame(screening_data)
            
            if not df.empty:
                pe_count = df['pe'].notna().sum()
                pb_count = df['pb'].notna().sum()
                close_count = df['close_price'].notna().sum()
                market_cap_count = df['market_cap'].notna().sum()
                
                print(f"   收盘价非空: {close_count}")
                print(f"   PE非空: {pe_count}")
                print(f"   PB非空: {pb_count}")
                print(f"   市值非空: {market_cap_count}")
                
                # 显示数据样例
                valid_data = df[df['pe'].notna() & df['pb'].notna() & df['close_price'].notna()].head(5)
                if not valid_data.empty:
                    print(f"\n📋 数据样例:")
                    for i, (idx, row) in enumerate(valid_data.iterrows(), 1):
                        print(f"   {i}. {row['symbol']} - {row['name']} - 收盘价: {row['close_price']:.2f} - PE: {row['pe']:.2f} - PB: {row['pb']:.2f} - 市值: {row['market_cap']:.0f}万")
                
                # 第四步：执行筛选
                print(f"\n🔍 第四步：执行筛选...")
                
                # 筛选条件：PE在5-50之间，PB在0.5-10之间，市值大于10亿
                filtered = df[
                    (df['pe'] >= 5) & (df['pe'] <= 50) &
                    (df['pb'] >= 0.5) & (df['pb'] <= 10) &
                    (df['market_cap'] >= 1000000)  # 10亿 = 1000000万
                ]
                
                print(f"   筛选条件: PE(5-50), PB(0.5-10), 市值>10亿")
                print(f"   筛选结果: {len(filtered)} 只股票")
                
                if not filtered.empty:
                    print(f"\n📋 筛选结果:")
                    for i, (idx, row) in enumerate(filtered.head(10).iterrows(), 1):
                        print(f"   {i}. {row['symbol']} - {row['name']} - PE: {row['pe']:.2f} - PB: {row['pb']:.2f} - 市值: {row['market_cap']:.0f}万 - 涨跌幅: {row['change_pct']:.2f}%")
                
                # 第五步：不同筛选条件测试
                print(f"\n🔍 第五步：不同筛选条件测试...")
                
                # 低估值股票
                low_pe = df[(df['pe'] > 0) & (df['pe'] <= 15)]
                print(f"   低PE股票(PE≤15): {len(low_pe)} 只")
                
                # 破净股票
                low_pb = df[(df['pb'] > 0) & (df['pb'] <= 1)]
                print(f"   破净股票(PB≤1): {len(low_pb)} 只")
                
                # 大盘股
                large_cap = df[df['market_cap'] >= 10000000]  # 100亿
                print(f"   大盘股(市值≥100亿): {len(large_cap)} 只")
                
                # 活跃股票
                active_stocks = df[df['turnover_rate'] >= 3]
                print(f"   活跃股票(换手率≥3%): {len(active_stocks)} 只")
                
                # 上涨股票
                rising_stocks = df[df['change_pct'] > 0]
                print(f"   上涨股票: {len(rising_stocks)} 只")
                
                return True
            else:
                print("❌ 没有获取到数据")
                return False
                
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        return False

async def main():
    """主函数"""
    print("🎯 创建完全工作的选股功能")
    print("=" * 60)
    print(f"⏰ 开始时间: {datetime.now()}")
    
    success = await create_working_screening()
    
    print(f"\n⏰ 完成时间: {datetime.now()}")
    
    if success:
        print("🎉 选股功能创建成功！")
        print("💡 数据获取、处理和筛选逻辑完全正常")
        print("💡 现在可以基于这个逻辑修复原有的选股服务")
    else:
        print("⚠️  选股功能创建失败")

if __name__ == "__main__":
    asyncio.run(main())