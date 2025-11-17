"""
诊断策略条件 - 检查为什么没有交易信号
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pandas as pd
from datetime import datetime, timedelta
from app.services.strategy_database_service import strategy_db_service
from app.services.condition_evaluator import ConditionEvaluator
from app.core.database import get_db
import json

async def get_strategy_from_db(strategy_id: int):
    """从数据库获取策略"""
    try:
        with strategy_db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM trading_strategies 
                WHERE id = %s
            """, (strategy_id,))
            
            strategy = cursor.fetchone()
            if not strategy:
                print(f"❌ 策略ID {strategy_id} 不存在")
                return None
            
            return strategy
    except Exception as e:
        print(f"❌ 获取策略失败: {e}")
        return None


def get_stock_data(stock_code: str, start_date: str, end_date: str):
    """获取股票数据"""
    try:
        db = next(get_db())
        
        query = """
            SELECT trade_date, open_price as open, high_price as high, 
                   low_price as low, close_price as close, volume, amount
            FROM daily_history
            WHERE ts_code = %s 
            AND trade_date >= %s 
            AND trade_date <= %s
            ORDER BY trade_date
        """
        
        df = pd.read_sql(query, db.bind, params=(stock_code, start_date, end_date))
        
        if df.empty:
            print(f"❌ {stock_code} 没有数据")
            return None
        
        print(f"✅ {stock_code} 数据: {len(df)} 条记录")
        print(f"   日期范围: {df['trade_date'].min()} ~ {df['trade_date'].max()}")
        print(f"   价格范围: {df['close'].min():.2f} ~ {df['close'].max():.2f}")
        
        return df
        
    except Exception as e:
        print(f"❌ 获取数据失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_conditions_on_data(conditions, stock_data, test_dates):
    """测试条件在实际数据上的表现"""
    evaluator = ConditionEvaluator()
    
    print(f"\n{'='*80}")
    print(f"测试条件在 {len(test_dates)} 个日期上的表现")
    print(f"{'='*80}")
    
    satisfied_count = 0
    
    for date in test_dates:
        # 获取该日期之前的数据（用于计算指标）
        historical_data = stock_data[stock_data['trade_date'] <= date].copy()
        
        if len(historical_data) < 30:  # 至少需要30天数据
            continue
        
        # 评估条件
        result = evaluator.evaluate_conditions(conditions, historical_data, date)
        
        if result:
            satisfied_count += 1
            current_data = historical_data[historical_data['trade_date'] == date].iloc[0]
            print(f"\n✅ {date} 条件满足")
            print(f"   价格: {current_data['close']:.2f}")
            print(f"   成交量: {current_data['volume']:.0f}")
    
    print(f"\n{'='*80}")
    print(f"满足条件的日期数: {satisfied_count}/{len(test_dates)}")
    print(f"满足率: {satisfied_count/len(test_dates)*100:.1f}%")
    print(f"{'='*80}")
    
    return satisfied_count


async def diagnose_strategy(strategy_id: int):
    """诊断策略"""
    print(f"\n{'='*80}")
    print(f"诊断策略 ID: {strategy_id}")
    print(f"{'='*80}")
    
    # 1. 获取策略
    strategy = await get_strategy_from_db(strategy_id)
    if not strategy:
        return
    
    print(f"\n策略名称: {strategy['strategy_name']}")
    print(f"策略类型: {strategy['strategy_type']}")
    
    # 2. 解析买入条件
    try:
        buy_conditions = json.loads(strategy['buy_conditions'])
        print(f"\n买入条件数量: {len(buy_conditions)}")
        for i, cond in enumerate(buy_conditions, 1):
            print(f"  {i}. {cond.get('description', cond.get('type'))}")
            print(f"     类型: {cond.get('type')}")
            print(f"     操作符: {cond.get('operator')}")
            print(f"     值: {cond.get('value')}")
            if 'indicator' in cond:
                print(f"     指标: {cond.get('indicator')}")
            if 'params' in cond:
                print(f"     参数: {cond.get('params')}")
    except Exception as e:
        print(f"❌ 解析买入条件失败: {e}")
        return
    
    # 3. 获取测试数据
    print(f"\n{'='*80}")
    print("获取测试数据")
    print(f"{'='*80}")
    
    test_stock = '000001.SZ'  # 平安银行
    start_date = '2023-01-01'
    end_date = '2024-12-31'
    
    stock_data = get_stock_data(test_stock, start_date, end_date)
    if stock_data is None:
        return
    
    # 4. 测试条件
    # 选择一些测试日期
    all_dates = stock_data['trade_date'].tolist()
    # 每10天取一个日期
    test_dates = all_dates[30::10]  # 从第30天开始，每10天取一个
    
    print(f"\n测试日期数: {len(test_dates)}")
    print(f"第一个测试日期: {test_dates[0]}")
    print(f"最后一个测试日期: {test_dates[-1]}")
    
    # 5. 测试买入条件
    print(f"\n{'='*80}")
    print("测试买入条件")
    print(f"{'='*80}")
    
    buy_satisfied = test_conditions_on_data(buy_conditions, stock_data, test_dates)
    
    # 6. 分析结果
    print(f"\n{'='*80}")
    print("诊断结果")
    print(f"{'='*80}")
    
    if buy_satisfied == 0:
        print("\n❌ 问题: 买入条件从未满足")
        print("\n可能原因:")
        print("1. 条件过于严格")
        print("2. 条件组合不合理（AND逻辑）")
        print("3. 指标计算有问题")
        print("4. 数据不符合条件")
        
        print("\n建议:")
        print("1. 放宽条件阈值")
        print("2. 减少条件数量")
        print("3. 检查指标计算逻辑")
        print("4. 尝试其他股票或时间段")
    elif buy_satisfied < len(test_dates) * 0.05:
        print(f"\n⚠️  问题: 买入条件满足率过低 ({buy_satisfied/len(test_dates)*100:.1f}%)")
        print("\n建议: 适当放宽条件")
    else:
        print(f"\n✅ 买入条件满足率正常 ({buy_satisfied/len(test_dates)*100:.1f}%)")
    
    # 7. 详细分析每个条件
    print(f"\n{'='*80}")
    print("详细分析每个条件")
    print(f"{'='*80}")
    
    evaluator = ConditionEvaluator()
    
    # 选择一个测试日期进行详细分析
    test_date = test_dates[len(test_dates)//2]  # 选择中间的日期
    historical_data = stock_data[stock_data['trade_date'] <= test_date].copy()
    
    print(f"\n测试日期: {test_date}")
    current_data = historical_data[historical_data['trade_date'] == test_date].iloc[0]
    print(f"当前价格: {current_data['close']:.2f}")
    print(f"当前成交量: {current_data['volume']:.0f}")
    
    # 计算指标
    indicators = evaluator._calculate_indicators(historical_data, test_date, buy_conditions)
    
    print(f"\n计算的指标:")
    if indicators.ma:
        for period, value in indicators.ma.items():
            print(f"  MA{period}: {value:.2f}")
    if indicators.rsi:
        for period, value in indicators.rsi.items():
            print(f"  RSI{period}: {value:.2f}")
    if indicators.macd:
        print(f"  MACD DIF: {indicators.macd.get('dif', 0):.4f}")
        print(f"  MACD DEA: {indicators.macd.get('dea', 0):.4f}")
        print(f"  MACD: {indicators.macd.get('macd', 0):.4f}")
    
    # 逐个测试条件
    print(f"\n逐个测试条件:")
    for i, condition in enumerate(buy_conditions, 1):
        try:
            result = evaluator._evaluate_single_condition(
                condition, 
                current_data['close'], 
                current_data['volume'],
                indicators,
                historical_data,
                test_date
            )
            status = "✅ 满足" if result else "❌ 不满足"
            print(f"  {i}. {condition.get('description', condition.get('type'))}: {status}")
        except Exception as e:
            print(f"  {i}. {condition.get('description', condition.get('type'))}: ❌ 错误 - {e}")


async def main():
    """主函数"""
    print("\n" + "="*80)
    print("策略条件诊断工具")
    print("="*80)
    
    # 诊断策略31（均值回归+动量确认）
    await diagnose_strategy(31)
    
    print("\n" + "="*80)
    print("诊断完成")
    print("="*80)


if __name__ == '__main__':
    asyncio.run(main())
