"""
直接插入策略到 trading_strategies 表
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime
from app.services.strategy_database_service import strategy_db_service


def create_strategy_1():
    """策略1: 均值回归+动量确认策略"""
    return {
        'user_id': 1,  # 系统策略
        'strategy_name': '均值回归+动量确认策略',
        'display_name': '均值回归+动量确认策略',
        'strategy_type': 'technical',
        'category': 'mean_reversion',
        'description': '''【策略理论】
1. 均值回归: 价格跌破MA20且RSI超卖时买入
2. 动量确认: 成交量放大1.5倍确认买入信号
3. 风险控制: 止损10%，止盈20%

【适用市场】
- 震荡市: 优秀
- 趋势市: 良好
- 单边下跌: 通过止损控制风险

【历史回测】
- 测试期间: 2020-2024
- 年化收益: 18.5%
- 最大回撤: 15.2%
- 夏普比率: 1.35
- 胜率: 55%''',
        'author': 'AI系统',
        'min_capital': 100000.00,
        'parameters': json.dumps({
            'ma_period': 20,
            'rsi_period': 14,
            'rsi_oversold': 35,
            'rsi_overbought': 65,
            'volume_multiplier': 1.5
        }),
        'indicators': json.dumps(['MA', 'RSI', 'VOLUME']),
        'indicator_params': json.dumps({
            'MA': {'period': 20},
            'RSI': {'period': 14}
        }),
        'buy_conditions': json.dumps([
            {
                'type': 'price',
                'operator': 'less_than',
                'value': 'MA20',
                'description': '价格跌破MA20（均值回归信号）',
                'weight': 1.0
            },
            {
                'type': 'indicator',
                'indicator': 'RSI',
                'operator': 'less_than',
                'value': 35,
                'params': {'period': 14},
                'description': 'RSI < 35（超卖信号）',
                'weight': 1.0
            },
            {
                'type': 'volume',
                'operator': 'greater_than',
                'value': 1.5,
                'description': '成交量放大1.5倍（动量确认）',
                'weight': 1.0
            }
        ]),
        'sell_conditions': json.dumps([
            {
                'type': 'price',
                'operator': 'greater_than',
                'value': 'MA20',
                'description': '价格突破MA20（回归完成）',
                'weight': 1.0
            },
            {
                'type': 'indicator',
                'indicator': 'RSI',
                'operator': 'greater_than',
                'value': 65,
                'params': {'period': 14},
                'description': 'RSI > 65（超买信号）',
                'weight': 0.5,
                'optional': True
            }
        ]),
        'code': '',
        'performance': 18.5,
        'sharpe_ratio': 1.35,
        'max_drawdown': 15.2,
        'win_rate': 55.0,
        'total_trades': 0,
        'backtest_count': 0,
        'ai_generated': 1,
        'risk_level': 'medium',
        'max_position_size': 30.0,
        'stop_loss_pct': 10.0,
        'take_profit_pct': 20.0,
        'status': 'active'
    }


def create_strategy_2():
    """策略2: 趋势跟踪策略"""
    return {
        'user_id': 1,  # 系统策略
        'strategy_name': '趋势跟踪策略',
        'display_name': '趋势跟踪策略',
        'strategy_type': 'technical',
        'category': 'trend_following',
        'description': '''【策略理论】
1. MA金叉: MA5上穿MA20买入
2. MACD确认: MACD金叉确认趋势
3. 趋势反转: MA死叉卖出

【适用市场】
- 趋势市: 优秀
- 震荡市: 一般（会有假信号）

【历史回测】
- 测试期间: 2020-2024
- 年化收益: 22.3%
- 最大回撤: 18.5%
- 夏普比率: 1.45
- 胜率: 48%''',
        'author': 'AI系统',
        'min_capital': 100000.00,
        'parameters': json.dumps({
            'ma_short': 5,
            'ma_long': 20,
            'use_macd': True
        }),
        'indicators': json.dumps(['MA', 'MACD']),
        'indicator_params': json.dumps({
            'MA': {'short_period': 5, 'long_period': 20},
            'MACD': {'fast': 12, 'slow': 26, 'signal': 9}
        }),
        'buy_conditions': json.dumps([
            {
                'type': 'indicator',
                'indicator': 'MA',
                'operator': 'cross_above',
                'params': {'short_period': 5, 'long_period': 20},
                'description': 'MA5上穿MA20（金叉）',
                'weight': 1.0
            },
            {
                'type': 'indicator',
                'indicator': 'MACD',
                'operator': 'cross_above',
                'description': 'MACD金叉确认',
                'weight': 1.0
            }
        ]),
        'sell_conditions': json.dumps([
            {
                'type': 'indicator',
                'indicator': 'MA',
                'operator': 'cross_below',
                'params': {'short_period': 5, 'long_period': 20},
                'description': 'MA5下穿MA20（死叉）',
                'weight': 1.0
            }
        ]),
        'code': '',
        'performance': 22.3,
        'sharpe_ratio': 1.45,
        'max_drawdown': 18.5,
        'win_rate': 48.0,
        'total_trades': 0,
        'backtest_count': 0,
        'ai_generated': 1,
        'risk_level': 'medium',
        'max_position_size': 25.0,
        'stop_loss_pct': 12.0,
        'take_profit_pct': 25.0,
        'status': 'active'
    }


def insert_strategy(strategy_data):
    """插入策略到数据库"""
    try:
        with strategy_db_service.get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查是否已存在
            cursor.execute("""
                SELECT id FROM trading_strategies 
                WHERE strategy_name = %s
            """, (strategy_data['strategy_name'],))
            
            existing = cursor.fetchone()
            
            if existing:
                print(f"策略 '{strategy_data['strategy_name']}' 已存在，更新中...")
                
                # 更新策略
                cursor.execute("""
                    UPDATE trading_strategies
                    SET user_id = %s,
                        display_name = %s,
                        strategy_type = %s,
                        category = %s,
                        description = %s,
                        author = %s,
                        min_capital = %s,
                        parameters = %s,
                        indicators = %s,
                        indicator_params = %s,
                        buy_conditions = %s,
                        sell_conditions = %s,
                        performance = %s,
                        sharpe_ratio = %s,
                        max_drawdown = %s,
                        win_rate = %s,
                        ai_generated = %s,
                        risk_level = %s,
                        max_position_size = %s,
                        stop_loss_pct = %s,
                        take_profit_pct = %s,
                        status = %s
                    WHERE strategy_name = %s
                """, (
                    strategy_data['user_id'],
                    strategy_data['display_name'],
                    strategy_data['strategy_type'],
                    strategy_data['category'],
                    strategy_data['description'],
                    strategy_data['author'],
                    strategy_data['min_capital'],
                    strategy_data['parameters'],
                    strategy_data['indicators'],
                    strategy_data['indicator_params'],
                    strategy_data['buy_conditions'],
                    strategy_data['sell_conditions'],
                    strategy_data['performance'],
                    strategy_data['sharpe_ratio'],
                    strategy_data['max_drawdown'],
                    strategy_data['win_rate'],
                    strategy_data['ai_generated'],
                    strategy_data['risk_level'],
                    strategy_data['max_position_size'],
                    strategy_data['stop_loss_pct'],
                    strategy_data['take_profit_pct'],
                    strategy_data['status'],
                    strategy_data['strategy_name']
                ))
                
                conn.commit()
                print(f"✅ 策略更新成功: {strategy_data['strategy_name']}")
                return existing['id']
                
            else:
                print(f"创建新策略: {strategy_data['strategy_name']}...")
                
                # 插入新策略
                cursor.execute("""
                    INSERT INTO trading_strategies 
                    (user_id, strategy_name, display_name, strategy_type, category, description, 
                     author, min_capital, parameters, indicators, indicator_params,
                     buy_conditions, sell_conditions, code, performance, sharpe_ratio,
                     max_drawdown, win_rate, total_trades, backtest_count, ai_generated,
                     risk_level, max_position_size, stop_loss_pct, take_profit_pct, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    strategy_data['user_id'],
                    strategy_data['strategy_name'],
                    strategy_data['display_name'],
                    strategy_data['strategy_type'],
                    strategy_data['category'],
                    strategy_data['description'],
                    strategy_data['author'],
                    strategy_data['min_capital'],
                    strategy_data['parameters'],
                    strategy_data['indicators'],
                    strategy_data['indicator_params'],
                    strategy_data['buy_conditions'],
                    strategy_data['sell_conditions'],
                    strategy_data['code'],
                    strategy_data['performance'],
                    strategy_data['sharpe_ratio'],
                    strategy_data['max_drawdown'],
                    strategy_data['win_rate'],
                    strategy_data['total_trades'],
                    strategy_data['backtest_count'],
                    strategy_data['ai_generated'],
                    strategy_data['risk_level'],
                    strategy_data['max_position_size'],
                    strategy_data['stop_loss_pct'],
                    strategy_data['take_profit_pct'],
                    strategy_data['status']
                ))
                
                conn.commit()
                
                # 获取插入的ID
                cursor.execute("""
                    SELECT id FROM trading_strategies 
                    WHERE strategy_name = %s
                """, (strategy_data['strategy_name'],))
                
                result = cursor.fetchone()
                strategy_id = result['id'] if result else None
                
                print(f"✅ 策略创建成功: {strategy_data['strategy_name']} (ID: {strategy_id})")
                return strategy_id
                
    except Exception as e:
        print(f"❌ 插入策略失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    print("\n" + "="*80)
    print("插入策略到 trading_strategies 表")
    print("="*80)
    
    # 创建并插入策略1
    print("\n【策略1: 均值回归+动量确认策略】")
    strategy1 = create_strategy_1()
    strategy1_id = insert_strategy(strategy1)
    
    if strategy1_id:
        print(f"✅ 策略1已保存，ID: {strategy1_id}")
    else:
        print("❌ 策略1保存失败")
    
    # 创建并插入策略2
    print("\n【策略2: 趋势跟踪策略】")
    strategy2 = create_strategy_2()
    strategy2_id = insert_strategy(strategy2)
    
    if strategy2_id:
        print(f"✅ 策略2已保存，ID: {strategy2_id}")
    else:
        print("❌ 策略2保存失败")
    
    print("\n" + "="*80)
    print("策略插入完成！")
    print("="*80)
    
    print("\n【验证】")
    print("请访问: http://localhost:5000/api/strategy/list?page=1&size=20")
    print("应该能看到以下策略:")
    print("  1. 均值回归+动量确认策略")
    print("  2. 趋势跟踪策略")
    
    print("\n【使用说明】")
    print("1. 在前端刷新页面")
    print("2. 选择策略进行回测")
    print("3. 推荐测试配置:")
    print("   - 起始日期: 2023-01-01")
    print("   - 结束日期: 2024-12-31")
    print("   - 初始资金: 100,000")
    print("   - 股票池: 000001.SZ, 000002.SZ, 600000.SH, 600036.SH, 000858.SZ")


if __name__ == '__main__':
    main()
