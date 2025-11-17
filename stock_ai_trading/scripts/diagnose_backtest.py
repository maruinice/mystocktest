"""
回测引擎诊断脚本
检查数据完整性、条件评估逻辑和交易信号生成
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from app.core.database import get_db
from sqlalchemy import text
import pandas as pd
import json

def check_database_data():
    """检查数据库历史数据"""
    print("\n" + "="*80)
    print("1. 数据库历史数据检查")
    print("="*80)
    
    db = next(get_db())
    
    # 检查总体数据
    result = db.execute(text("""
        SELECT COUNT(*) as total_records,
               COUNT(DISTINCT ts_code) as stock_count,
               MIN(trade_date) as earliest_date,
               MAX(trade_date) as latest_date
        FROM daily_history
    """)).fetchone()
    
    print(f"\n总记录数: {result[0]:,}")
    print(f"股票数量: {result[1]}")
    print(f"最早日期: {result[2]}")
    print(f"最新日期: {result[3]}")
    
    # 检查最近的数据
    result = db.execute(text("""
        SELECT ts_code, COUNT(*) as record_count,
               MIN(trade_date) as start_date,
               MAX(trade_date) as end_date
        FROM daily_history
        GROUP BY ts_code
        ORDER BY record_count DESC
        LIMIT 10
    """)).fetchall()
    
    print("\n数据最多的10只股票:")
    print(f"{'股票代码':<15} {'记录数':<10} {'开始日期':<12} {'结束日期':<12}")
    print("-" * 55)
    for row in result:
        print(f"{row[0]:<15} {row[1]:<10} {str(row[2]):<12} {str(row[3]):<12}")
    
    # 检查特定股票的数据
    test_stocks = ['000001.SZ', '600000.SH', '000002.SZ']
    print(f"\n测试股票数据检查:")
    for ts_code in test_stocks:
        result = db.execute(text("""
            SELECT COUNT(*) as count,
                   MIN(trade_date) as start_date,
                   MAX(trade_date) as end_date
            FROM daily_history
            WHERE ts_code = :ts_code
        """), {'ts_code': ts_code}).fetchone()
        
        if result[0] > 0:
            print(f"  ✅ {ts_code}: {result[0]}条记录, {result[1]} ~ {result[2]}")
        else:
            print(f"  ❌ {ts_code}: 无数据")


def check_data_fields():
    """检查数据字段完整性"""
    print("\n" + "="*80)
    print("2. 数据字段完整性检查")
    print("="*80)
    
    db = next(get_db())
    
    # 获取样本数据
    result = db.execute(text("""
        SELECT trade_date, open_price, high_price, low_price, close_price, volume, amount
        FROM daily_history
        WHERE ts_code = '000001.SZ'
        ORDER BY trade_date DESC
        LIMIT 5
    """)).fetchall()
    
    if result:
        print("\n样本数据（000001.SZ 最近5天）:")
        print(f"{'日期':<12} {'开盘':<10} {'最高':<10} {'最低':<10} {'收盘':<10} {'成交量':<15} {'成交额':<15}")
        print("-" * 90)
        for row in result:
            print(f"{str(row[0]):<12} {row[1]:<10} {row[2]:<10} {row[3]:<10} {row[4]:<10} {row[5]:<15} {row[6]:<15}")
        
        # 检查空值
        result = db.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(open_price) as has_open,
                COUNT(high_price) as has_high,
                COUNT(low_price) as has_low,
                COUNT(close_price) as has_close,
                COUNT(volume) as has_volume
            FROM daily_history
            WHERE ts_code = '000001.SZ'
        """)).fetchone()
        
        total = result[0]
        print(f"\n字段完整性（000001.SZ）:")
        print(f"  总记录数: {total}")
        print(f"  开盘价: {result[1]} ({result[1]/total*100:.1f}%)")
        print(f"  最高价: {result[2]} ({result[2]/total*100:.1f}%)")
        print(f"  最低价: {result[3]} ({result[3]/total*100:.1f}%)")
        print(f"  收盘价: {result[4]} ({result[4]/total*100:.1f}%)")
        print(f"  成交量: {result[5]} ({result[5]/total*100:.1f}%)")
    else:
        print("  ❌ 无样本数据")


async def test_condition_evaluator():
    """测试条件评估器"""
    print("\n" + "="*80)
    print("3. 条件评估器测试")
    print("="*80)
    
    try:
        from app.services.condition_evaluator import ConditionEvaluator
        from app.services.strategy_database_service import strategy_db_service
        
        evaluator = ConditionEvaluator()
        
        # 获取测试数据
        with strategy_db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT trade_date, open_price as open, high_price as high,
                       low_price as low, close_price as close, volume
                FROM daily_history
                WHERE ts_code = '000001.SZ'
                ORDER BY trade_date DESC
                LIMIT 100
            """)
            rows = cursor.fetchall()
        
        if not rows:
            print("  ❌ 无测试数据")
            return
        
        # 转换为DataFrame
        df = pd.DataFrame(rows, columns=['trade_date', 'open', 'high', 'low', 'close', 'volume'])
        df = df.sort_values('trade_date').reset_index(drop=True)
        df['trade_date'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y-%m-%d')
        
        print(f"\n获取到 {len(df)} 条测试数据")
        print(f"日期范围: {df['trade_date'].min()} ~ {df['trade_date'].max()}")
        
        # 测试日期
        test_date = df['trade_date'].iloc[-1]
        print(f"\n测试日期: {test_date}")
        
        # 测试条件1: 价格突破MA20
        print("\n测试条件1: 价格突破MA20")
        conditions = [
            {
                'type': 'price',
                'operator': 'greater_than',
                'value': 'MA20',
                'description': '价格突破MA20'
            }
        ]
        
        result = evaluator.evaluate_conditions(conditions, df, test_date)
        print(f"  结果: {result}")
        
        # 测试条件2: RSI超卖
        print("\n测试条件2: RSI < 30")
        conditions = [
            {
                'type': 'indicator',
                'indicator': 'RSI',
                'operator': 'less_than',
                'value': 30,
                'params': {'period': 14},
                'description': 'RSI超卖'
            }
        ]
        
        result = evaluator.evaluate_conditions(conditions, df, test_date)
        print(f"  结果: {result}")
        
        # 测试条件3: MA金叉
        print("\n测试条件3: MA5上穿MA20")
        conditions = [
            {
                'type': 'indicator',
                'indicator': 'MA',
                'operator': 'cross_above',
                'params': {'short_period': 5, 'long_period': 20},
                'description': 'MA5上穿MA20'
            }
        ]
        
        result = evaluator.evaluate_conditions(conditions, df, test_date)
        print(f"  结果: {result}")
        
        # 测试组合条件
        print("\n测试条件4: 价格>MA20 AND RSI<70")
        conditions = [
            {
                'type': 'price',
                'operator': 'greater_than',
                'value': 'MA20',
                'description': '价格突破MA20'
            },
            {
                'type': 'indicator',
                'indicator': 'RSI',
                'operator': 'less_than',
                'value': 70,
                'params': {'period': 14},
                'description': 'RSI未超买'
            }
        ]
        
        result = evaluator.evaluate_conditions(conditions, df, test_date)
        print(f"  结果: {result}")
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_backtest_data_flow():
    """测试回测数据流"""
    print("\n" + "="*80)
    print("4. 回测数据流测试")
    print("="*80)
    
    try:
        from app.services.backtest_engine import BacktestEngine, BacktestConfig
        
        engine = BacktestEngine()
        
        # 测试数据获取
        stock_pool = ['000001.SZ']
        start_date = '2023-10-01'
        end_date = '2023-11-01'
        
        print(f"\n测试数据获取:")
        print(f"  股票池: {stock_pool}")
        print(f"  日期范围: {start_date} ~ {end_date}")
        
        # 获取历史数据
        price_data = await engine._get_historical_data(stock_pool, start_date, end_date)
        
        if price_data:
            for code, df in price_data.items():
                if df is not None and not df.empty:
                    print(f"\n  ✅ {code}:")
                    print(f"     记录数: {len(df)}")
                    print(f"     日期范围: {df['trade_date'].min()} ~ {df['trade_date'].max()}")
                    print(f"     字段: {list(df.columns)}")
                    print(f"     样本数据:")
                    print(df.head(3).to_string(index=False))
                else:
                    print(f"  ❌ {code}: 数据为空")
        else:
            print("  ❌ 未获取到任何数据")
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_full_backtest():
    """测试完整回测流程"""
    print("\n" + "="*80)
    print("5. 完整回测流程测试")
    print("="*80)
    
    try:
        from app.services.backtest_engine import BacktestEngine, BacktestConfig
        
        engine = BacktestEngine()
        
        # 创建测试配置
        config = BacktestConfig(
            strategy_id='TEST001',
            strategy_name='测试策略',
            strategy_code='',  # 使用条件评估器
            start_date='2023-10-01',
            end_date='2023-11-01',
            initial_capital=100000.0,
            stock_pool=['000001.SZ'],
            buy_conditions=[
                {
                    'type': 'price',
                    'operator': 'greater_than',
                    'value': 'MA20',
                    'description': '价格突破MA20'
                }
            ],
            sell_conditions=[
                {
                    'type': 'price',
                    'operator': 'less_than',
                    'value': 'MA20',
                    'description': '价格跌破MA20'
                }
            ],
            risk_controls={
                'max_position_size': 0.3,
                'max_total_position': 0.8,
                'stop_loss': 10,
                'take_profit': 20
            }
        )
        
        print(f"\n测试配置:")
        print(f"  策略: {config.strategy_name}")
        print(f"  日期: {config.start_date} ~ {config.end_date}")
        print(f"  初始资金: {config.initial_capital:,.0f}")
        print(f"  股票池: {config.stock_pool}")
        print(f"  买入条件: {len(config.buy_conditions)}个")
        print(f"  卖出条件: {len(config.sell_conditions)}个")
        
        # 运行回测
        print(f"\n开始回测...")
        result = await engine.run_backtest(config)
        
        if result.get('status') == 'completed':
            print(f"\n✅ 回测完成:")
            print(f"  总收益率: {result['total_return']*100:.2f}%")
            print(f"  年化收益: {result['annualized_return']*100:.2f}%")
            print(f"  最大回撤: {result['max_drawdown']*100:.2f}%")
            print(f"  夏普比率: {result['sharpe_ratio']:.2f}")
            print(f"  总交易数: {result['total_trades']}")
            print(f"  胜率: {result['win_rate']*100:.2f}%")
            
            # 显示交易记录
            trades = result.get('trades', [])
            if trades:
                print(f"\n交易记录 (前5笔):")
                for i, trade in enumerate(trades[:5], 1):
                    print(f"  {i}. {trade['date']} {trade['side']:4s} {trade['code']} "
                          f"数量:{trade['quantity']:6d} 价格:{trade['price']:8.2f} "
                          f"金额:{trade['amount']:12.2f}")
            else:
                print(f"\n  ⚠️ 没有交易记录")
            
            # 显示净值曲线
            equity_curve = result.get('equity_curve', [])
            if equity_curve:
                print(f"\n净值曲线 (前5天和后5天):")
                for eq in equity_curve[:5]:
                    print(f"  {eq['date']}: {eq['value']:12.2f} ({eq['return']*100:6.2f}%)")
                if len(equity_curve) > 10:
                    print("  ...")
                    for eq in equity_curve[-5:]:
                        print(f"  {eq['date']}: {eq['value']:12.2f} ({eq['return']*100:6.2f}%)")
        else:
            print(f"\n❌ 回测失败:")
            print(f"  错误: {result.get('error_message', '未知错误')}")
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    print("\n" + "="*80)
    print("回测引擎诊断工具")
    print("="*80)
    
    # 1. 检查数据库数据
    check_database_data()
    
    # 2. 检查数据字段
    check_data_fields()
    
    # 3. 测试条件评估器
    await test_condition_evaluator()
    
    # 4. 测试回测数据流
    await test_backtest_data_flow()
    
    # 5. 测试完整回测
    await test_full_backtest()
    
    print("\n" + "="*80)
    print("诊断完成")
    print("="*80)


if __name__ == '__main__':
    asyncio.run(main())
